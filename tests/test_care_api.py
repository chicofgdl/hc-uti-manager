import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

# Configure environment BEFORE importing the app


@pytest_asyncio.fixture
async def test_app(tmp_path):
    os.environ["AUTH_ENABLED"] = "false"
    os.environ["POSTGRES_DSN"] = ""
    db_path = tmp_path / "test.db"
    os.environ["SQLITE_DSN"] = f"sqlite+aiosqlite:///{db_path}"

    import importlib
    import src.main as main_module
    main = importlib.reload(main_module)
    app = main.app
    from resources.database import DatabaseManager
    from models.care import Bed, BedAvailability, BedOccupancy

    async with LifespanManager(app):
        # Seed minimal data (1 bed)
        manager: DatabaseManager = app.state.app_db
        async with manager.async_session_maker() as session:
            async with session.begin():
                session.add_all(
                    [
                        Bed(code="B1", availability_status=BedAvailability.DISPONIVEL, occupancy_status=BedOccupancy.LIVRE),
                    ]
                )
        yield app


@pytest_asyncio.fixture
async def client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_reservation_creation_notifies_icu(client):
    # Create reservation
    res = await client.post("/api/surgical-center/reservations", json={"patientId": "123"})
    assert res.status_code == 201

    # ICU should have unread notification
    notif = await client.get("/api/notifications", params={"role": "ICU", "unreadOnly": True})
    assert notif.status_code == 200
    types = [n["type"] for n in notif.json()]
    assert "RESERVA_CRIADA" in types


@pytest.mark.asyncio
async def test_accept_reservation_prevents_double_allocation(client):
    # create two pending reservations while bed still disponível
    r1 = await client.post("/api/surgical-center/reservations", json={"patientId": "A"})
    r2 = await client.post("/api/surgical-center/reservations", json={"patientId": "B"})
    assert r1.status_code == 201 and r2.status_code == 201
    res1_id = r1.json()["id"]
    res2_id = r2.json()["id"]

    # accept first reservation (auto bed)
    accept1 = await client.patch(f"/api/icu/reservations/{res1_id}/decision", json={"decision": "ACCEPT"})
    assert accept1.status_code == 200

    # try to accept second reservation -> should fail due to no available beds
    accept2 = await client.patch(f"/api/icu/reservations/{res2_id}/decision", json={"decision": "ACCEPT"})
    assert accept2.status_code == 400


@pytest.mark.asyncio
async def test_transfer_denied_notifies_cc(client):
    # create and accept reservation so transfer can be requested
    res = await client.post("/api/surgical-center/reservations", json={"patientId": "321"})
    res_id = res.json()["id"]
    await client.patch(f"/api/icu/reservations/{res_id}/decision", json={"decision": "ACCEPT"})

    transfer = await client.post("/api/surgical-center/transfers", json={"patientId": "321", "reservationId": res_id})
    assert transfer.status_code == 201
    tr_id = transfer.json()["id"]

    denial = await client.patch(f"/api/icu/transfers/{tr_id}/decision", json={"decision": "DENY"})
    assert denial.status_code == 200

    notif = await client.get("/api/notifications", params={"role": "SURGICAL_CENTER", "unreadOnly": True})
    messages = [n["type"] for n in notif.json()]
    assert "TRANSFERENCIA_ATUALIZADA" in messages

import csv
import importlib
import os
from pathlib import Path

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _patient_row(rows: list[dict[str, str]], external_id: str) -> dict[str, str]:
    for row in rows:
        if str(row.get("Prontuário", "")).strip() == str(external_id):
            return row
    raise AssertionError(f"Paciente {external_id} não encontrado em pacientes.csv")


@pytest_asyncio.fixture
async def test_app(tmp_path: Path):
    leitos_csv = tmp_path / "leitos.csv"
    pacientes_csv = tmp_path / "pacientes.csv"
    sqlite_path = tmp_path / "test.db"

    _write_csv(
        leitos_csv,
        headers=["Cód Leito", "Leito", "Situação do Leito", "Data Última Atualização", "Operação"],
        rows=[
            {
                "Cód Leito": "B1",
                "Leito": "1",
                "Situação do Leito": "A",
                "Data Última Atualização": "2026-02-24T00:00:00",
                "Operação": "UPD",
            },
            {
                "Cód Leito": "B2",
                "Leito": "2",
                "Situação do Leito": "I",
                "Data Última Atualização": "2026-02-24T00:00:00",
                "Operação": "UPD",
            },
        ],
    )
    _write_csv(
        pacientes_csv,
        headers=["Prontuário", "Nome"],
        rows=[
            {"Prontuário": "77001", "Nome": "Paciente 77001"},
            {"Prontuário": "77002", "Nome": "Paciente 77002"},
            {"Prontuário": "77003", "Nome": "Paciente 77003"},
        ],
    )

    os.environ["AUTH_ENABLED"] = "false"
    os.environ["POSTGRES_DSN"] = ""
    os.environ["SQLITE_DSN"] = f"sqlite+aiosqlite:///{sqlite_path}"
    os.environ["LEITOS_CSV_PATH"] = str(leitos_csv)
    os.environ["PACIENTE_CSV_PATH"] = str(pacientes_csv)

    import src.main as main_module

    main = importlib.reload(main_module)
    app = main.app

    async with LifespanManager(app):
        app.state.test_leitos_csv = leitos_csv
        app.state.test_pacientes_csv = pacientes_csv
        yield app


@pytest_asyncio.fixture
async def client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_bed_availability_flow_updates_count_and_listing(client):
    beds = await client.get("/api/icu/beds")
    assert beds.status_code == 200
    payload = beds.json()
    assert len(payload) == 2

    bed_b1 = next(item for item in payload if item["code"] == "B1")

    before_count = await client.get("/api/icu/beds/available-count")
    assert before_count.status_code == 200
    assert before_count.json()["count"] == 1

    block = await client.patch(
        f"/api/icu/beds/{bed_b1['id']}/availability",
        json={"availableForReservation": False},
    )
    assert block.status_code == 200
    assert block.json()["availability_status"] == "NAO_DISPONIVEL"

    after_block = await client.get("/api/icu/beds/available-count")
    assert after_block.status_code == 200
    assert after_block.json()["count"] == 0

    reopen = await client.patch(
        f"/api/icu/beds/{bed_b1['id']}/availability",
        json={"availableForReservation": True},
    )
    assert reopen.status_code == 200
    assert reopen.json()["availability_status"] == "DISPONIVEL"

    after_reopen = await client.get("/api/icu/beds/available-count")
    assert after_reopen.status_code == 200
    assert after_reopen.json()["count"] == 1


@pytest.mark.asyncio
async def test_accept_reservation_blocks_double_allocation_and_updates_csv(client, test_app):
    r1 = await client.post("/api/surgical-center/reservations", json={"patientId": "77001"})
    r2 = await client.post("/api/surgical-center/reservations", json={"patientId": "77002"})
    assert r1.status_code == 201
    assert r2.status_code == 201

    res1_id = r1.json()["id"]
    res2_id = r2.json()["id"]

    accept1 = await client.patch(f"/api/icu/reservations/{res1_id}/decision", json={"decision": "ACCEPT"})
    assert accept1.status_code == 200
    accepted = accept1.json()
    assert accepted["status"] == "ACEITA"
    assert accepted["bed_id"] is not None

    accept2 = await client.patch(f"/api/icu/reservations/{res2_id}/decision", json={"decision": "ACCEPT"})
    assert accept2.status_code == 400

    leitos_rows = _read_csv(test_app.state.test_leitos_csv)
    pacientes_rows = _read_csv(test_app.state.test_pacientes_csv)

    reserved_row = next(row for row in leitos_rows if row["care_bed_id"] == str(accepted["bed_id"]))
    assert reserved_row["care_availability_status"] == "NAO_DISPONIVEL"
    assert reserved_row["care_reserved_for_patient"] == "77001"

    paciente_77001 = _patient_row(pacientes_rows, "77001")
    assert "\"status\": \"ACEITA\"" in paciente_77001["care_reservations_json"]


@pytest.mark.asyncio
async def test_transfer_accept_occupies_bed_and_moves_patient_to_uti(client, test_app):
    reservation = await client.post("/api/surgical-center/reservations", json={"patientId": "77003"})
    assert reservation.status_code == 201
    reservation_id = reservation.json()["id"]

    accepted_reservation = await client.patch(
        f"/api/icu/reservations/{reservation_id}/decision",
        json={"decision": "ACCEPT"},
    )
    assert accepted_reservation.status_code == 200
    reserved_bed_id = accepted_reservation.json()["bed_id"]

    transfer = await client.post(
        "/api/surgical-center/transfers",
        json={"patientId": "77003", "reservationId": reservation_id},
    )
    assert transfer.status_code == 201
    transfer_id = transfer.json()["id"]

    decision = await client.patch(f"/api/icu/transfers/{transfer_id}/decision", json={"decision": "ACCEPT"})
    assert decision.status_code == 200
    assert decision.json()["status"] == "ACEITA"
    assert decision.json()["bed_id"] == reserved_bed_id

    leitos_rows = _read_csv(test_app.state.test_leitos_csv)
    pacientes_rows = _read_csv(test_app.state.test_pacientes_csv)

    occupied_row = next(row for row in leitos_rows if row["care_bed_id"] == str(reserved_bed_id))
    assert occupied_row["care_occupancy_status"] == "OCUPADO"
    assert occupied_row["care_current_patient"] == "77003"

    paciente_77003 = _patient_row(pacientes_rows, "77003")
    assert paciente_77003["care_location"] == "UTI"
    assert paciente_77003["care_current_bed_id"] == str(reserved_bed_id)


@pytest.mark.asyncio
async def test_cancel_reservation_cleans_bed_reservation_link(client, test_app):
    reservation = await client.post("/api/surgical-center/reservations", json={"patientId": "77002"})
    assert reservation.status_code == 201
    reservation_id = reservation.json()["id"]

    accepted = await client.patch(
        f"/api/icu/reservations/{reservation_id}/decision",
        json={"decision": "ACCEPT"},
    )
    assert accepted.status_code == 200
    bed_id = accepted.json()["bed_id"]

    canceled = await client.patch(f"/api/surgical-center/reservations/{reservation_id}/cancel", json={"reason": "Sem necessidade"})
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "CANCELADA"
    assert canceled.json()["bed_id"] is None

    leitos_rows = _read_csv(test_app.state.test_leitos_csv)
    bed_row = next(row for row in leitos_rows if row["care_bed_id"] == str(bed_id))
    assert bed_row["care_reserved_for_patient"] == ""

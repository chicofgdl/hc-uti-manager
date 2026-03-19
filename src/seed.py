"""
Seed simples para popular leitos e pacientes a partir dos CSVs em data/.
Uso:
    python -m src.seed
"""
from __future__ import annotations

import asyncio
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select, func

from models.care import Bed, BedAvailability, BedOccupancy, Patient
from resources.database import DatabaseManager, Base


load_dotenv()


def _get_app_dsn() -> str:
    dsn = os.getenv("SQLITE_DSN")
    sqlite_path = os.getenv("SQLITE_PATH")
    if not dsn and sqlite_path:
        dsn = f"sqlite+aiosqlite:///{os.path.abspath(sqlite_path)}"
    if not dsn:
        default_sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "app.db"))
        dsn = f"sqlite+aiosqlite:///{default_sqlite_path}"
    return dsn


async def seed_beds(session):
    count = await session.scalar(select(func.count()).select_from(Bed))
    if count and count > 0:
        print(f"Beds already populated ({count} rows). Skipping.")
        return

    csv_path = Path("data/leitos.csv")
    if not csv_path.exists():
        print("data/leitos.csv not found; skipping bed seed.")
        return

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)[:50]  # limit para não inflar base local

    beds = [
        Bed(
            code=row.get("Cód Leito") or row.get("Cod Leito") or row.get("Código Leito") or str(idx),
            availability_status=BedAvailability.NAO_DISPONIVEL,
            occupancy_status=BedOccupancy.LIVRE,
        )
        for idx, row in enumerate(rows, start=1)
    ]
    session.add_all(beds)
    await session.commit()
    print(f"Seeded {len(beds)} beds.")


async def seed_patients(session):
    count = await session.scalar(select(func.count()).select_from(Patient))
    if count and count > 0:
        print(f"Patients already populated ({count} rows). Skipping.")
        return

    csv_path = Path("data/pacientes.csv")
    if not csv_path.exists():
        print("data/pacientes.csv not found; skipping patient seed.")
        return

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)[:20]

    patients = [
        Patient(
            external_id=row.get("Prontuário") or row.get("Prontuario") or str(idx),
            name=row.get("Nome"),
            location="CC",
        )
        for idx, row in enumerate(rows, start=1)
    ]
    session.add_all(patients)
    await session.commit()
    print(f"Seeded {len(patients)} patients.")


async def main():
    dsn = _get_app_dsn()
    manager = DatabaseManager(dsn)
    async with manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with manager.async_session_maker() as session:
        await seed_beds(session)
        await seed_patients(session)

    await manager.close_connection()


if __name__ == "__main__":
    asyncio.run(main())

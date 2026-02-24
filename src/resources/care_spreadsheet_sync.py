from __future__ import annotations

import asyncio
import csv
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.care import Bed, Patient, Reservation, ReservationStatus


class CareSpreadsheetSync:
    """
    Sincroniza o estado operacional do domínio care para as planilhas CSV
    de leitos e pacientes usadas no projeto.
    """

    BED_CODE_CANDIDATES = [
        "Cód Leito",
        "Cod Leito",
        "Código Leito",
        "leito_numero",
        "lto_lto_id",
        "code",
    ]
    PATIENT_ID_CANDIDATES = ["Prontuário", "Prontuario", "PRONTUARIO", "codigo", "Código"]

    BED_SYNC_COLUMNS = [
        "care_availability_status",
        "care_occupancy_status",
        "care_reserved_for_patient",
        "care_current_patient",
        "care_updated_at",
    ]
    PATIENT_SYNC_COLUMNS = ["care_location", "care_current_bed", "care_updated_at"]

    def __init__(self, leitos_csv_path: str, pacientes_csv_path: str, enabled: bool = True):
        self.leitos_csv_path = leitos_csv_path
        self.pacientes_csv_path = pacientes_csv_path
        self.enabled = bool(enabled)
        self._lock = asyncio.Lock()

    async def sync_from_database(self, session: AsyncSession) -> None:
        if not self.enabled:
            return
        if not os.path.isfile(self.leitos_csv_path) or not os.path.isfile(self.pacientes_csv_path):
            return

        beds_result = await session.execute(select(Bed).order_by(Bed.code.asc()))
        beds = beds_result.scalars().all()
        beds_payload = [
            {
                "id": bed.id,
                "code": str(bed.code),
                "availability_status": bed.availability_status.value,
                "occupancy_status": bed.occupancy_status.value,
                "updated_at": bed.updated_at.isoformat() if bed.updated_at else "",
            }
            for bed in beds
        ]
        bed_code_by_id = {int(item["id"]): str(item["code"]) for item in beds_payload}

        accepted_reservations_result = await session.execute(
            select(Reservation.bed_id, Patient.external_id)
            .join(Patient, Reservation.patient_id == Patient.id)
            .where(
                Reservation.status == ReservationStatus.ACEITA,
                Reservation.bed_id.is_not(None),
            )
        )
        accepted_reservations_payload = [
            {"bed_id": bed_id, "patient_external_id": str(external_id)}
            for bed_id, external_id in accepted_reservations_result.all()
            if bed_id is not None and external_id is not None
        ]

        patients_result = await session.execute(select(Patient))
        patients = patients_result.scalars().all()
        patients_payload = [
            {
                "external_id": str(patient.external_id),
                "location": patient.location or "",
                "current_bed_id": patient.current_bed_id,
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else "",
            }
            for patient in patients
        ]

        async with self._lock:
            await asyncio.to_thread(
                self._sync_csv_files,
                beds_payload,
                accepted_reservations_payload,
                patients_payload,
                bed_code_by_id,
            )

    def _sync_csv_files(
        self,
        beds_payload: List[Dict[str, Any]],
        accepted_reservations_payload: List[Dict[str, Any]],
        patients_payload: List[Dict[str, Any]],
        bed_code_by_id: Dict[int, str],
    ) -> None:
        self._sync_leitos_csv(beds_payload, accepted_reservations_payload, patients_payload)
        self._sync_pacientes_csv(patients_payload, bed_code_by_id)

    def _sync_leitos_csv(
        self,
        beds_payload: List[Dict[str, Any]],
        accepted_reservations_payload: List[Dict[str, Any]],
        patients_payload: List[Dict[str, Any]],
    ) -> None:
        headers, rows = self._read_csv(self.leitos_csv_path)
        if not headers:
            return

        code_col = self._pick_existing_header(headers, self.BED_CODE_CANDIDATES)
        if not code_col:
            return

        for col in self.BED_SYNC_COLUMNS:
            if col not in headers:
                headers.append(col)

        beds_by_code = {str(bed["code"]): bed for bed in beds_payload}
        reserved_by_code: Dict[str, str] = {}
        for res in accepted_reservations_payload:
            bed_id = res.get("bed_id")
            patient_external_id = res.get("patient_external_id")
            if bed_id is None or not patient_external_id:
                continue
            bed_match = next((b for b in beds_payload if int(b["id"]) == int(bed_id)), None)
            if not bed_match:
                continue
            reserved_by_code[str(bed_match["code"])] = str(patient_external_id)

        occupied_by_code: Dict[str, str] = {}
        for patient in patients_payload:
            bed_id = patient.get("current_bed_id")
            external_id = patient.get("external_id")
            if bed_id is None or not external_id:
                continue
            bed_match = next((b for b in beds_payload if int(b["id"]) == int(bed_id)), None)
            if not bed_match:
                continue
            occupied_by_code[str(bed_match["code"])] = str(external_id)

        for row in rows:
            row_code = self._normalize_identifier(row.get(code_col))
            if not row_code:
                continue
            bed = beds_by_code.get(row_code)
            if not bed:
                continue
            row["care_availability_status"] = str(bed["availability_status"])
            row["care_occupancy_status"] = str(bed["occupancy_status"])
            row["care_reserved_for_patient"] = reserved_by_code.get(row_code, "")
            row["care_current_patient"] = occupied_by_code.get(row_code, "")
            row["care_updated_at"] = str(bed["updated_at"])
            if "Data Última Atualização" in headers:
                row["Data Última Atualização"] = str(bed["updated_at"])

        self._write_csv_atomic(self.leitos_csv_path, headers, rows)

    def _sync_pacientes_csv(self, patients_payload: List[Dict[str, Any]], bed_code_by_id: Dict[int, str]) -> None:
        headers, rows = self._read_csv(self.pacientes_csv_path)
        if not headers:
            return

        patient_id_col = self._pick_existing_header(headers, self.PATIENT_ID_CANDIDATES)
        if not patient_id_col:
            patient_id_col = "Prontuário"
            headers.insert(0, patient_id_col)

        for col in self.PATIENT_SYNC_COLUMNS:
            if col not in headers:
                headers.append(col)

        patients_by_external_id = {
            self._normalize_identifier(p["external_id"]): p
            for p in patients_payload
            if self._normalize_identifier(p.get("external_id"))
        }
        existing_ids = set()

        for row in rows:
            patient_id = self._normalize_identifier(row.get(patient_id_col))
            if not patient_id:
                continue
            existing_ids.add(patient_id)
            patient = patients_by_external_id.get(patient_id)
            if not patient:
                continue
            bed_code = ""
            current_bed_id = patient.get("current_bed_id")
            if current_bed_id is not None:
                bed_code = bed_code_by_id.get(int(current_bed_id), "")
            row["care_location"] = str(patient.get("location") or "")
            row["care_current_bed"] = bed_code
            row["care_updated_at"] = str(patient.get("updated_at") or "")

        now = datetime.utcnow().isoformat()
        for patient_id, patient in patients_by_external_id.items():
            if patient_id in existing_ids:
                continue
            bed_code = ""
            current_bed_id = patient.get("current_bed_id")
            if current_bed_id is not None:
                bed_code = bed_code_by_id.get(int(current_bed_id), "")
            new_row = {header: "" for header in headers}
            new_row[patient_id_col] = patient_id
            if "Nome" in headers:
                new_row["Nome"] = f"Paciente {patient_id}"
            new_row["care_location"] = str(patient.get("location") or "")
            new_row["care_current_bed"] = bed_code
            new_row["care_updated_at"] = str(patient.get("updated_at") or now)
            rows.append(new_row)

        self._write_csv_atomic(self.pacientes_csv_path, headers, rows)

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        if value is None:
            return ""
        normalized = str(value).strip()
        if normalized.lower() in {"nan", "none", "<na>"}:
            return ""
        if normalized.endswith(".0"):
            maybe_int = normalized[:-2]
            if maybe_int.isdigit():
                return maybe_int
        return normalized

    @staticmethod
    def _pick_existing_header(headers: List[str], candidates: List[str]) -> str | None:
        for candidate in candidates:
            if candidate in headers:
                return candidate
        return None

    @staticmethod
    def _read_csv(path: str) -> tuple[List[str], List[Dict[str, str]]]:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames or [])
            rows = list(reader)
        return headers, rows

    @staticmethod
    def _write_csv_atomic(path: str, headers: List[str], rows: List[Dict[str, str]]) -> None:
        folder = os.path.dirname(path) or "."
        os.makedirs(folder, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=folder, newline="", encoding="utf-8") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                complete_row = {header: row.get(header, "") for header in headers}
                writer.writerow(complete_row)
            temp_path = tmp.name
        os.replace(temp_path, path)

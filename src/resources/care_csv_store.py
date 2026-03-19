from __future__ import annotations

import asyncio
import csv
import json
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover - non-posix fallback
    fcntl = None  # type: ignore


T = TypeVar("T")


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    normalized = str(value).strip()
    if normalized.lower() in {"nan", "none", "<na>", "(null)"}:
        return ""
    return normalized


def _to_int(value: Any) -> Optional[int]:
    normalized = _clean(value)
    if not normalized:
        return None
    if normalized.endswith(".0"):
        normalized = normalized[:-2]
    if normalized.isdigit():
        return int(normalized)
    return None


def _to_json_list(value: Any) -> List[Dict[str, Any]]:
    normalized = _clean(value)
    if not normalized:
        return []
    try:
        parsed = json.loads(normalized)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except Exception:
        pass
    return []


class CareCsvStateStore:
    BED_CODE_CANDIDATES = ["Cód Leito", "Cod Leito", "Código Leito", "code", "leito_numero", "lto_lto_id"]
    PATIENT_ID_CANDIDATES = ["Prontuário", "Prontuario", "PRONTUARIO", "codigo", "Código"]

    BED_COLUMNS = [
        "care_bed_id",
        "care_base_availability_status",
        "care_availability_status",
        "care_occupancy_status",
        "care_reserved_for_patient",
        "care_current_patient",
        "care_created_at",
        "care_updated_at",
    ]
    PATIENT_COLUMNS = [
        "care_patient_id",
        "care_location",
        "care_current_bed_id",
        "care_current_bed_code",
        "care_reservations_json",
        "care_transfers_json",
        "care_updated_at",
    ]
    META_COLUMNS = [
        "care_meta_next_patient_id",
        "care_meta_next_reservation_id",
        "care_meta_next_transfer_id",
        "care_meta_next_notification_id",
        "care_meta_notifications_json",
    ]

    def __init__(self, leitos_csv_path: str, pacientes_csv_path: str):
        self.leitos_csv_path = leitos_csv_path
        self.pacientes_csv_path = pacientes_csv_path
        lock_dir = os.path.dirname(os.path.abspath(leitos_csv_path)) or "."
        self.lock_path = os.path.join(lock_dir, ".care_csv.lock")
        self._async_lock = asyncio.Lock()
        self._file_lock_timeout_seconds = float(os.getenv("CARE_CSV_LOCK_TIMEOUT_SECONDS", "2.0"))
        self._file_lock_sleep_seconds = 0.05

    async def read(self, reader: Callable[[Dict[str, Any]], T]) -> T:
        async with self._async_lock:
            return self._read_sync(reader)

    async def mutate(self, mutator: Callable[[Dict[str, Any]], T]) -> T:
        async with self._async_lock:
            return self._mutate_sync(mutator)

    def _read_sync(self, reader: Callable[[Dict[str, Any]], T]) -> T:
        # Reads do not take file lock. Writes are atomic (os.replace), so readers
        # can safely open stable snapshots and avoid lock-induced stalls.
        state = self._load_state()
        self._sync_derived_state(state)
        return reader(state)

    def _mutate_sync(self, mutator: Callable[[Dict[str, Any]], T]) -> T:
        with self._file_lock():
            state = self._load_state()
            self._sync_derived_state(state)
            result = mutator(state)
            self._sync_derived_state(state)
            self._write_state(state)
            return result

    @contextmanager
    def _file_lock(self):
        os.makedirs(os.path.dirname(self.lock_path) or ".", exist_ok=True)
        with open(self.lock_path, "a+", encoding="utf-8") as lock_file:
            lock_acquired = False
            if fcntl is not None:
                started_at = time.monotonic()
                while True:
                    try:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        lock_acquired = True
                        break
                    except BlockingIOError:
                        if (time.monotonic() - started_at) >= self._file_lock_timeout_seconds:
                            print(
                                f"WARNING: CSV lock timeout after {self._file_lock_timeout_seconds}s; "
                                "continuing with process-local lock only."
                            )
                            break
                        time.sleep(self._file_lock_sleep_seconds)
                    except OSError as exc:
                        print(
                            f"WARNING: CSV file lock unsupported or failed ({type(exc).__name__}); "
                            "continuing with process-local lock only."
                        )
                        break
            try:
                yield
            finally:
                if fcntl is not None and lock_acquired:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _read_csv(path: str) -> Tuple[List[str], List[Dict[str, str]]]:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames or [])
            rows = list(reader)
        return headers, rows

    @staticmethod
    def _write_csv(path: str, headers: List[str], rows: List[Dict[str, str]]) -> str:
        folder = os.path.dirname(path) or "."
        os.makedirs(folder, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=folder, newline="", encoding="utf-8") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})
            tmp.flush()
            os.fsync(tmp.fileno())
            return tmp.name

    @staticmethod
    def _ensure_columns(headers: List[str], columns: List[str]) -> bool:
        changed = False
        for col in columns:
            if col not in headers:
                headers.append(col)
                changed = True
        return changed

    @staticmethod
    def _pick_header(headers: List[str], candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            if candidate in headers:
                return candidate
        return None

    @staticmethod
    def _infer_base_availability(row: Dict[str, str]) -> str:
        status = _clean(row.get("Situação do Leito")).upper()
        if status in {"A", "DISPONIVEL", "LIVRE"}:
            return "DISPONIVEL"
        return "NAO_DISPONIVEL"

    def _load_state(self) -> Dict[str, Any]:
        leitos_headers, leitos_rows = self._read_csv(self.leitos_csv_path)
        pacientes_headers, pacientes_rows = self._read_csv(self.pacientes_csv_path)

        dirty = False
        dirty = self._ensure_columns(leitos_headers, self.BED_COLUMNS + self.META_COLUMNS) or dirty
        dirty = self._ensure_columns(pacientes_headers, self.PATIENT_COLUMNS) or dirty

        bed_code_col = self._pick_header(leitos_headers, self.BED_CODE_CANDIDATES)
        if not bed_code_col:
            raise RuntimeError("leitos.csv não possui coluna de código do leito compatível.")

        patient_id_col = self._pick_header(pacientes_headers, self.PATIENT_ID_CANDIDATES)
        if not patient_id_col:
            patient_id_col = "Prontuário"
            pacientes_headers.insert(0, patient_id_col)
            dirty = True

        if not leitos_rows:
            raise RuntimeError("leitos.csv está vazio; ao menos um leito é obrigatório.")

        beds_by_id: Dict[int, Dict[str, Any]] = {}
        beds_by_code: Dict[str, Dict[str, Any]] = {}

        next_bed_id = 1
        for row in leitos_rows:
            bed_code = _clean(row.get(bed_code_col))
            if not bed_code:
                continue
            bed_id = _to_int(row.get("care_bed_id"))
            if bed_id is None:
                bed_id = next_bed_id
                row["care_bed_id"] = str(bed_id)
                dirty = True

            next_bed_id = max(next_bed_id, bed_id + 1)
            base_availability = _clean(row.get("care_base_availability_status")).upper()
            if base_availability not in {"DISPONIVEL", "NAO_DISPONIVEL"}:
                base_availability = self._infer_base_availability(row)
                row["care_base_availability_status"] = base_availability
                dirty = True

            created_at = _clean(row.get("care_created_at")) or _clean(row.get("Data Última Atualização")) or _utcnow_iso()
            updated_at = _clean(row.get("care_updated_at")) or created_at
            if not _clean(row.get("care_created_at")):
                row["care_created_at"] = created_at
                dirty = True
            if not _clean(row.get("care_updated_at")):
                row["care_updated_at"] = updated_at
                dirty = True

            bed = {
                "id": bed_id,
                "code": bed_code,
                "base_availability_status": base_availability,
                "availability_status": _clean(row.get("care_availability_status")) or base_availability,
                "occupancy_status": _clean(row.get("care_occupancy_status")) or "LIVRE",
                "reserved_for_patient": _clean(row.get("care_reserved_for_patient")) or None,
                "current_patient": _clean(row.get("care_current_patient")) or None,
                "created_at": created_at,
                "updated_at": updated_at,
                "_row": row,
            }
            beds_by_id[bed_id] = bed
            beds_by_code[bed_code] = bed

        patients_by_external_id: Dict[str, Dict[str, Any]] = {}
        next_patient_id = 1
        for row in pacientes_rows:
            external_id = _clean(row.get(patient_id_col))
            if not external_id:
                continue

            patient_id = _to_int(row.get("care_patient_id"))
            if patient_id is None:
                patient_id = next_patient_id
                row["care_patient_id"] = str(patient_id)
                dirty = True
            next_patient_id = max(next_patient_id, patient_id + 1)

            current_bed_id = _to_int(row.get("care_current_bed_id"))
            if current_bed_id is None:
                bed_code = _clean(row.get("care_current_bed_code"))
                if bed_code in beds_by_code:
                    current_bed_id = beds_by_code[bed_code]["id"]
                    row["care_current_bed_id"] = str(current_bed_id)
                    dirty = True

            location = _clean(row.get("care_location")) or "CC"
            updated_at = _clean(row.get("care_updated_at")) or _utcnow_iso()
            if not _clean(row.get("care_location")):
                row["care_location"] = location
                dirty = True
            if not _clean(row.get("care_updated_at")):
                row["care_updated_at"] = updated_at
                dirty = True

            reservations = _to_json_list(row.get("care_reservations_json"))
            transfers = _to_json_list(row.get("care_transfers_json"))

            patient = {
                "id": patient_id,
                "external_id": external_id,
                "name": _clean(row.get("Nome")) or None,
                "location": location,
                "current_bed_id": current_bed_id,
                "updated_at": updated_at,
                "reservations": reservations,
                "transfers": transfers,
                "_row": row,
            }
            patients_by_external_id[external_id] = patient

        metadata_row = leitos_rows[0]
        notifications = _to_json_list(metadata_row.get("care_meta_notifications_json"))

        max_reservation_id = 1
        max_transfer_id = 1
        for patient in patients_by_external_id.values():
            for reservation in patient["reservations"]:
                max_reservation_id = max(max_reservation_id, (_to_int(reservation.get("id")) or 0) + 1)
            for transfer in patient["transfers"]:
                max_transfer_id = max(max_transfer_id, (_to_int(transfer.get("id")) or 0) + 1)

        max_notification_id = 1
        for notification in notifications:
            max_notification_id = max(max_notification_id, (_to_int(notification.get("id")) or 0) + 1)

        next_patient_id_meta = _to_int(metadata_row.get("care_meta_next_patient_id")) or next_patient_id
        next_reservation_id_meta = _to_int(metadata_row.get("care_meta_next_reservation_id")) or max_reservation_id
        next_transfer_id_meta = _to_int(metadata_row.get("care_meta_next_transfer_id")) or max_transfer_id
        next_notification_id_meta = _to_int(metadata_row.get("care_meta_next_notification_id")) or max_notification_id

        if _clean(metadata_row.get("care_meta_next_patient_id")) != str(next_patient_id_meta):
            metadata_row["care_meta_next_patient_id"] = str(next_patient_id_meta)
            dirty = True
        if _clean(metadata_row.get("care_meta_next_reservation_id")) != str(next_reservation_id_meta):
            metadata_row["care_meta_next_reservation_id"] = str(next_reservation_id_meta)
            dirty = True
        if _clean(metadata_row.get("care_meta_next_transfer_id")) != str(next_transfer_id_meta):
            metadata_row["care_meta_next_transfer_id"] = str(next_transfer_id_meta)
            dirty = True
        if _clean(metadata_row.get("care_meta_next_notification_id")) != str(next_notification_id_meta):
            metadata_row["care_meta_next_notification_id"] = str(next_notification_id_meta)
            dirty = True
        if _clean(metadata_row.get("care_meta_notifications_json")) != json.dumps(notifications, ensure_ascii=False):
            metadata_row["care_meta_notifications_json"] = json.dumps(notifications, ensure_ascii=False)
            dirty = True

        state = {
            "dirty": dirty,
            "leitos_headers": leitos_headers,
            "leitos_rows": leitos_rows,
            "pacientes_headers": pacientes_headers,
            "pacientes_rows": pacientes_rows,
            "patient_id_col": patient_id_col,
            "beds": beds_by_id,
            "beds_by_code": beds_by_code,
            "patients": patients_by_external_id,
            "notifications": notifications,
            "meta": {
                "next_patient_id": next_patient_id_meta,
                "next_reservation_id": next_reservation_id_meta,
                "next_transfer_id": next_transfer_id_meta,
                "next_notification_id": next_notification_id_meta,
            },
        }
        return state

    def _sync_derived_state(self, state: Dict[str, Any]) -> None:
        beds: Dict[int, Dict[str, Any]] = state["beds"]
        patients: Dict[str, Dict[str, Any]] = state["patients"]

        for bed in beds.values():
            bed["availability_status"] = bed["base_availability_status"]
            bed["occupancy_status"] = "LIVRE"
            bed["reserved_for_patient"] = None
            bed["current_patient"] = None

        for patient in patients.values():
            current_bed_id = patient.get("current_bed_id")
            if current_bed_id not in beds:
                if current_bed_id is not None:
                    patient["current_bed_id"] = None
                    if patient.get("location") == "UTI":
                        patient["location"] = "CC"
                    patient["updated_at"] = _utcnow_iso()
                    state["dirty"] = True
                continue
            bed = beds[current_bed_id]
            bed["current_patient"] = patient["external_id"]
            bed["occupancy_status"] = "OCUPADO"
            bed["availability_status"] = "NAO_DISPONIVEL"
            if patient.get("location") != "UTI":
                patient["location"] = "UTI"
                patient["updated_at"] = _utcnow_iso()
                state["dirty"] = True

        for patient in patients.values():
            for reservation in patient["reservations"]:
                status = _clean(reservation.get("status")).upper()
                bed_id = _to_int(reservation.get("bed_id"))
                if status != "ACEITA" or bed_id is None or bed_id not in beds:
                    continue
                if patient.get("current_bed_id") == bed_id:
                    continue
                bed = beds[bed_id]
                if bed["occupancy_status"] == "LIVRE":
                    bed["reserved_for_patient"] = patient["external_id"]
                    bed["availability_status"] = "NAO_DISPONIVEL"

        self._persist_runtime_columns(state)

    def _persist_runtime_columns(self, state: Dict[str, Any]) -> None:
        beds: Dict[int, Dict[str, Any]] = state["beds"]
        patients: Dict[str, Dict[str, Any]] = state["patients"]
        bed_code_by_id = {bed_id: bed["code"] for bed_id, bed in beds.items()}

        for bed in beds.values():
            row = bed["_row"]
            row["care_bed_id"] = str(bed["id"])
            row["care_base_availability_status"] = bed["base_availability_status"]
            row["care_availability_status"] = bed["availability_status"]
            row["care_occupancy_status"] = bed["occupancy_status"]
            row["care_reserved_for_patient"] = bed["reserved_for_patient"] or ""
            row["care_current_patient"] = bed["current_patient"] or ""
            row["care_created_at"] = bed["created_at"]
            row["care_updated_at"] = bed["updated_at"]
            if "Data Última Atualização" in state["leitos_headers"]:
                row["Data Última Atualização"] = bed["updated_at"]

        patient_id_col = state["patient_id_col"]
        for patient in patients.values():
            row = patient["_row"]
            row[patient_id_col] = patient["external_id"]
            row["care_patient_id"] = str(patient["id"])
            row["care_location"] = patient.get("location") or "CC"
            current_bed_id = patient.get("current_bed_id")
            row["care_current_bed_id"] = str(current_bed_id) if current_bed_id is not None else ""
            row["care_current_bed_code"] = bed_code_by_id.get(current_bed_id, "") if current_bed_id is not None else ""
            row["care_reservations_json"] = json.dumps(patient.get("reservations", []), ensure_ascii=False)
            row["care_transfers_json"] = json.dumps(patient.get("transfers", []), ensure_ascii=False)
            row["care_updated_at"] = patient.get("updated_at") or _utcnow_iso()

        metadata_row = state["leitos_rows"][0]
        metadata_row["care_meta_next_patient_id"] = str(state["meta"]["next_patient_id"])
        metadata_row["care_meta_next_reservation_id"] = str(state["meta"]["next_reservation_id"])
        metadata_row["care_meta_next_transfer_id"] = str(state["meta"]["next_transfer_id"])
        metadata_row["care_meta_next_notification_id"] = str(state["meta"]["next_notification_id"])
        metadata_row["care_meta_notifications_json"] = json.dumps(state.get("notifications", []), ensure_ascii=False)
        for row in state["leitos_rows"][1:]:
            for col in self.META_COLUMNS:
                row[col] = ""

    def _write_state(self, state: Dict[str, Any]) -> None:
        self._persist_runtime_columns(state)

        temp_leitos_path = self._write_csv(self.leitos_csv_path, state["leitos_headers"], state["leitos_rows"])
        temp_pacientes_path = self._write_csv(self.pacientes_csv_path, state["pacientes_headers"], state["pacientes_rows"])

        backup_leitos_path = f"{self.leitos_csv_path}.bak"
        backup_pacientes_path = f"{self.pacientes_csv_path}.bak"

        if os.path.exists(self.leitos_csv_path):
            shutil.copy2(self.leitos_csv_path, backup_leitos_path)
        if os.path.exists(self.pacientes_csv_path):
            shutil.copy2(self.pacientes_csv_path, backup_pacientes_path)

        try:
            os.replace(temp_leitos_path, self.leitos_csv_path)
            os.replace(temp_pacientes_path, self.pacientes_csv_path)
        except Exception:
            if os.path.exists(backup_leitos_path):
                shutil.copy2(backup_leitos_path, self.leitos_csv_path)
            if os.path.exists(backup_pacientes_path):
                shutil.copy2(backup_pacientes_path, self.pacientes_csv_path)
            raise
        finally:
            for path in [temp_leitos_path, temp_pacientes_path, backup_leitos_path, backup_pacientes_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from models.care import (
    BedAvailability,
    BedOccupancy,
    NotificationType,
    ReservationStatus,
    Role,
    TransferStatus,
)
from resources.care_csv_store import CareCsvStateStore


def _now_iso() -> str:
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


class CareProvider:
    """
    Provider CSV-first para regras de negócio de leitos, reservas, transferências
    e notificações.
    """

    def __init__(self, leitos_csv_path: str, pacientes_csv_path: str):
        self.store = CareCsvStateStore(leitos_csv_path, pacientes_csv_path)

    # --- Helpers internos -----------------------------------------------------
    @staticmethod
    def _patient_payload(patient: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": int(patient["id"]),
            "external_id": patient["external_id"],
            "name": patient.get("name"),
            "location": patient.get("location"),
            "current_bed_id": patient.get("current_bed_id"),
        }

    @staticmethod
    def _bed_payload(bed: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": int(bed["id"]),
            "code": bed["code"],
            "availability_status": bed["availability_status"],
            "occupancy_status": bed["occupancy_status"],
            "created_at": bed["created_at"],
            "updated_at": bed["updated_at"],
        }

    def _reservation_payload(self, reservation: Dict[str, Any], patient: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": int(reservation["id"]),
            "status": reservation["status"],
            "patient": self._patient_payload(patient),
            "notes": reservation.get("notes"),
            "preferred_datetime": reservation.get("preferred_datetime"),
            "bed_id": reservation.get("bed_id"),
            "requested_by": reservation.get("requested_by", Role.SURGICAL_CENTER.value),
            "cancellation_reason": reservation.get("cancellation_reason"),
            "created_at": reservation.get("created_at"),
            "updated_at": reservation.get("updated_at"),
            "decided_at": reservation.get("decided_at"),
        }

    def _transfer_payload(self, transfer: Dict[str, Any], patient: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": int(transfer["id"]),
            "status": transfer["status"],
            "patient": self._patient_payload(patient),
            "reservation_id": transfer.get("reservation_id"),
            "bed_id": transfer.get("bed_id"),
            "requested_by": transfer.get("requested_by", Role.SURGICAL_CENTER.value),
            "created_at": transfer.get("created_at"),
            "updated_at": transfer.get("updated_at"),
            "decided_at": transfer.get("decided_at"),
        }

    @staticmethod
    def _iter_reservations(state: Dict[str, Any]):
        for patient in state["patients"].values():
            for reservation in patient["reservations"]:
                yield patient, reservation

    @staticmethod
    def _iter_transfers(state: Dict[str, Any]):
        for patient in state["patients"].values():
            for transfer in patient["transfers"]:
                yield patient, transfer

    @staticmethod
    def _active_patient_reservation(patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for reservation in patient["reservations"]:
            if reservation.get("status") in {ReservationStatus.PENDENTE.value, ReservationStatus.ACEITA.value}:
                return reservation
        return None

    @staticmethod
    def _active_patient_transfer(patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for transfer in patient["transfers"]:
            if transfer.get("status") in {TransferStatus.PENDENTE.value, TransferStatus.ACEITA.value}:
                return transfer
        return None

    @staticmethod
    def _first_available_bed(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        beds = sorted(state["beds"].values(), key=lambda bed: bed["code"])
        for bed in beds:
            if (
                bed["availability_status"] == BedAvailability.DISPONIVEL.value
                and bed["occupancy_status"] == BedOccupancy.LIVRE.value
            ):
                return bed
        return None

    @staticmethod
    def _reservation_lookup(state: Dict[str, Any], reservation_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        for patient, reservation in CareProvider._iter_reservations(state):
            if _to_int(reservation.get("id")) == reservation_id:
                return patient, reservation
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

    @staticmethod
    def _transfer_lookup(state: Dict[str, Any], transfer_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        for patient, transfer in CareProvider._iter_transfers(state):
            if _to_int(transfer.get("id")) == transfer_id:
                return patient, transfer
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transferência não encontrada.")

    @staticmethod
    def _find_or_create_patient(state: Dict[str, Any], external_id: str) -> Dict[str, Any]:
        patient_id = _clean(external_id)
        if not patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patientId é obrigatório.",
            )

        patient = state["patients"].get(patient_id)
        if patient:
            return patient

        row = {header: "" for header in state["pacientes_headers"]}
        row[state["patient_id_col"]] = patient_id
        if "Nome" in state["pacientes_headers"]:
            row["Nome"] = f"Paciente {patient_id}"

        state["pacientes_rows"].append(row)
        patient = {
            "id": int(state["meta"]["next_patient_id"]),
            "external_id": patient_id,
            "name": _clean(row.get("Nome")) or None,
            "location": "CC",
            "current_bed_id": None,
            "updated_at": _now_iso(),
            "reservations": [],
            "transfers": [],
            "_row": row,
        }
        state["patients"][patient_id] = patient
        state["meta"]["next_patient_id"] = int(state["meta"]["next_patient_id"]) + 1
        state["dirty"] = True
        return patient

    @staticmethod
    def _bed_by_id(state: Dict[str, Any], bed_id: int) -> Dict[str, Any]:
        bed = state["beds"].get(int(bed_id))
        if not bed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leito não encontrado.")
        return bed

    @staticmethod
    def _active_reservation_on_bed(state: Dict[str, Any], bed_id: int) -> bool:
        for _, reservation in CareProvider._iter_reservations(state):
            if _to_int(reservation.get("bed_id")) != bed_id:
                continue
            if reservation.get("status") in {ReservationStatus.PENDENTE.value, ReservationStatus.ACEITA.value}:
                return True
        return False

    @staticmethod
    def _active_transfer_on_bed(state: Dict[str, Any], bed_id: int) -> bool:
        for _, transfer in CareProvider._iter_transfers(state):
            if _to_int(transfer.get("bed_id")) != bed_id:
                continue
            if transfer.get("status") in {TransferStatus.PENDENTE.value, TransferStatus.ACEITA.value}:
                return True
        return False

    @staticmethod
    def _accepted_reservation_for_bed(state: Dict[str, Any], bed_id: int) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        for patient, reservation in CareProvider._iter_reservations(state):
            if _to_int(reservation.get("bed_id")) != bed_id:
                continue
            if reservation.get("status") == ReservationStatus.ACEITA.value:
                return patient, reservation
        return None

    @staticmethod
    def _notify(
        state: Dict[str, Any],
        *,
        recipient: Role,
        type_: NotificationType,
        message: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        notification = {
            "id": int(state["meta"]["next_notification_id"]),
            "type": type_.value,
            "message": message,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "recipient_role": recipient.value,
            "read": False,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        state["meta"]["next_notification_id"] = int(state["meta"]["next_notification_id"]) + 1
        state["notifications"].append(notification)
        state["dirty"] = True
        return notification

    # --- Leitos ---------------------------------------------------------------
    async def list_beds(self) -> List[Dict[str, Any]]:
        def reader(state: Dict[str, Any]) -> List[Dict[str, Any]]:
            beds = sorted(state["beds"].values(), key=lambda bed: bed["code"])
            return [self._bed_payload(bed) for bed in beds]

        return await self.store.read(reader)

    async def set_bed_availability(self, bed_id: int, available: bool) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            bed = self._bed_by_id(state, bed_id)
            now = _now_iso()

            if available:
                if bed["occupancy_status"] != BedOccupancy.LIVRE.value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Leito ocupado não pode ser disponibilizado para reserva.",
                    )
                if bed.get("reserved_for_patient"):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Leito reservado para outro paciente. Cancele a reserva antes.",
                    )
                bed["base_availability_status"] = BedAvailability.DISPONIVEL.value
                bed["availability_status"] = BedAvailability.DISPONIVEL.value
            else:
                if bed["occupancy_status"] == BedOccupancy.OCUPADO.value:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Leito ocupado não pode ter disponibilização cancelada.",
                    )
                if self._active_reservation_on_bed(state, int(bed["id"])) or self._active_transfer_on_bed(state, int(bed["id"])):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Há vínculo ativo de reserva/transferência neste leito. Finalize antes de bloquear.",
                    )
                bed["base_availability_status"] = BedAvailability.NAO_DISPONIVEL.value
                bed["availability_status"] = BedAvailability.NAO_DISPONIVEL.value

            bed["updated_at"] = now
            state["dirty"] = True
            return self._bed_payload(bed)

        return await self.store.mutate(mutator)

    async def available_count(self) -> int:
        def reader(state: Dict[str, Any]) -> int:
            return sum(
                1
                for bed in state["beds"].values()
                if bed["availability_status"] == BedAvailability.DISPONIVEL.value
                and bed["occupancy_status"] == BedOccupancy.LIVRE.value
            )

        return await self.store.read(reader)

    # --- Reservas -------------------------------------------------------------
    async def create_reservation(
        self,
        *,
        patient_external_id: str,
        notes: Optional[str],
        preferred_datetime: Optional[datetime],
    ) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            available = sum(
                1
                for bed in state["beds"].values()
                if bed["availability_status"] == BedAvailability.DISPONIVEL.value
                and bed["occupancy_status"] == BedOccupancy.LIVRE.value
            )
            if available == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não há leitos disponíveis para reserva.",
                )

            patient = self._find_or_create_patient(state, patient_external_id)
            active_reservation = self._active_patient_reservation(patient)
            if active_reservation:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Paciente já possui reserva pendente/aceita.",
                )

            now = _now_iso()
            reservation = {
                "id": int(state["meta"]["next_reservation_id"]),
                "status": ReservationStatus.PENDENTE.value,
                "notes": notes,
                "preferred_datetime": preferred_datetime.isoformat() if preferred_datetime else None,
                "bed_id": None,
                "requested_by": Role.SURGICAL_CENTER.value,
                "cancellation_reason": None,
                "created_at": now,
                "updated_at": now,
                "decided_at": None,
            }
            state["meta"]["next_reservation_id"] = int(state["meta"]["next_reservation_id"]) + 1
            patient["reservations"].append(reservation)
            patient["updated_at"] = now
            state["dirty"] = True

            self._notify(
                state,
                recipient=Role.ICU,
                type_=NotificationType.RESERVA_CRIADA,
                message=f"Nova solicitação de reserva para paciente {patient['external_id']}.",
                reference_type="reservation",
                reference_id=int(reservation["id"]),
            )
            return self._reservation_payload(reservation, patient)

        return await self.store.mutate(mutator)

    async def list_reservations(self) -> List[Dict[str, Any]]:
        def reader(state: Dict[str, Any]) -> List[Dict[str, Any]]:
            reservations: List[Dict[str, Any]] = []
            for patient, reservation in self._iter_reservations(state):
                reservations.append(self._reservation_payload(reservation, patient))
            reservations.sort(key=lambda item: item["created_at"] or "", reverse=True)
            return reservations

        return await self.store.read(reader)

    async def decide_reservation(self, reservation_id: int, decision: str, bed_id: Optional[int]) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            patient, reservation = self._reservation_lookup(state, reservation_id)
            if reservation.get("status") != ReservationStatus.PENDENTE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Apenas reservas pendentes podem ser decididas.",
                )

            now = _now_iso()
            decision_normalized = _clean(decision).upper()

            if decision_normalized == "DENY":
                reservation["status"] = ReservationStatus.NEGADA.value
                reservation["bed_id"] = None
                reservation["decided_at"] = now
                reservation["updated_at"] = now
                patient["updated_at"] = now
                state["dirty"] = True

                self._notify(
                    state,
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.RESERVA_ATUALIZADA,
                    message=f"Reserva {reservation_id} negada pela UTI.",
                    reference_type="reservation",
                    reference_id=reservation_id,
                )
                return self._reservation_payload(reservation, patient)

            if decision_normalized != "ACCEPT":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decisão inválida.")

            if patient.get("location") == "UTI":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Paciente já está na UTI, reserva não pode ser aceita.",
                )

            selected_bed = self._bed_by_id(state, bed_id) if bed_id else self._first_available_bed(state)
            if not selected_bed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nenhum leito disponível para alocação.",
                )
            if selected_bed["occupancy_status"] != BedOccupancy.LIVRE.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leito selecionado está ocupado.")
            if selected_bed["availability_status"] != BedAvailability.DISPONIVEL.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leito selecionado não está disponível para reserva.",
                )

            reservation["status"] = ReservationStatus.ACEITA.value
            reservation["bed_id"] = int(selected_bed["id"])
            reservation["decided_at"] = now
            reservation["updated_at"] = now
            selected_bed["updated_at"] = now
            patient["updated_at"] = now
            state["dirty"] = True

            self._notify(
                state,
                recipient=Role.SURGICAL_CENTER,
                type_=NotificationType.RESERVA_ATUALIZADA,
                message=f"Reserva {reservation_id} aceita. Leito {selected_bed['code']} reservado.",
                reference_type="reservation",
                reference_id=reservation_id,
            )
            return self._reservation_payload(reservation, patient)

        return await self.store.mutate(mutator)

    async def cancel_reservation(self, reservation_id: int, actor: Role, reason: Optional[str]) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            patient, reservation = self._reservation_lookup(state, reservation_id)
            if reservation.get("status") not in {ReservationStatus.PENDENTE.value, ReservationStatus.ACEITA.value}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Somente reservas pendentes ou aceitas podem ser canceladas.",
                )

            now = _now_iso()
            prior_bed_id = _to_int(reservation.get("bed_id"))
            reservation["status"] = ReservationStatus.CANCELADA.value
            reservation["cancellation_reason"] = reason
            reservation["bed_id"] = None
            reservation["updated_at"] = now
            reservation["decided_at"] = reservation.get("decided_at") or now

            for transfer in patient["transfers"]:
                if transfer.get("reservation_id") != reservation_id:
                    continue
                if transfer.get("status") in {TransferStatus.PENDENTE.value, TransferStatus.ACEITA.value}:
                    transfer["reservation_id"] = None
                    transfer["updated_at"] = now

            if prior_bed_id and prior_bed_id in state["beds"]:
                state["beds"][prior_bed_id]["updated_at"] = now

            patient["updated_at"] = now
            state["dirty"] = True

            recipient = Role.ICU if actor == Role.SURGICAL_CENTER else Role.SURGICAL_CENTER
            self._notify(
                state,
                recipient=recipient,
                type_=NotificationType.RESERVA_ATUALIZADA,
                message=f"Reserva {reservation_id} cancelada por {actor.value}.",
                reference_type="reservation",
                reference_id=reservation_id,
            )
            return self._reservation_payload(reservation, patient)

        return await self.store.mutate(mutator)

    # --- Transferências -------------------------------------------------------
    async def create_transfer(
        self,
        *,
        patient_external_id: str,
        reservation_id: Optional[int],
        bed_id: Optional[int],
        notes: Optional[str],
    ) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            patient = self._find_or_create_patient(state, patient_external_id)
            active_transfer = self._active_patient_transfer(patient)
            if active_transfer:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Paciente já possui transferência pendente/aceita.",
                )

            reservation = None
            if reservation_id is not None:
                reservation_patient, reservation = self._reservation_lookup(state, reservation_id)
                if reservation_patient["external_id"] != patient["external_id"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reserva informada pertence a outro paciente.",
                    )
                if reservation.get("status") != ReservationStatus.ACEITA.value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Somente reservas aceitas podem originar transferência.",
                    )

            if bed_id is not None:
                self._bed_by_id(state, bed_id)

            now = _now_iso()
            transfer = {
                "id": int(state["meta"]["next_transfer_id"]),
                "status": TransferStatus.PENDENTE.value,
                "reservation_id": reservation_id if reservation else None,
                "bed_id": bed_id,
                "notes": notes,
                "requested_by": Role.SURGICAL_CENTER.value,
                "created_at": now,
                "updated_at": now,
                "decided_at": None,
            }
            state["meta"]["next_transfer_id"] = int(state["meta"]["next_transfer_id"]) + 1
            patient["transfers"].append(transfer)
            patient["updated_at"] = now
            state["dirty"] = True

            self._notify(
                state,
                recipient=Role.ICU,
                type_=NotificationType.TRANSFERENCIA_CRIADA,
                message=f"Solicitação de transferência para paciente {patient['external_id']}.",
                reference_type="transfer",
                reference_id=int(transfer["id"]),
            )
            return self._transfer_payload(transfer, patient)

        return await self.store.mutate(mutator)

    async def list_transfers(self) -> List[Dict[str, Any]]:
        def reader(state: Dict[str, Any]) -> List[Dict[str, Any]]:
            transfers: List[Dict[str, Any]] = []
            for patient, transfer in self._iter_transfers(state):
                transfers.append(self._transfer_payload(transfer, patient))
            transfers.sort(key=lambda item: item["created_at"] or "", reverse=True)
            return transfers

        return await self.store.read(reader)

    async def decide_transfer(self, transfer_id: int, decision: str, bed_id: Optional[int]) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            patient, transfer = self._transfer_lookup(state, transfer_id)
            if transfer.get("status") != TransferStatus.PENDENTE.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transferência já decidida.")

            now = _now_iso()
            decision_normalized = _clean(decision).upper()

            if decision_normalized == "DENY":
                transfer["status"] = TransferStatus.NEGADA.value
                transfer["bed_id"] = None
                transfer["decided_at"] = now
                transfer["updated_at"] = now
                patient["updated_at"] = now
                state["dirty"] = True

                self._notify(
                    state,
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.TRANSFERENCIA_ATUALIZADA,
                    message=f"Transferência {transfer_id} negada pela UTI.",
                    reference_type="transfer",
                    reference_id=transfer_id,
                )
                return self._transfer_payload(transfer, patient)

            if decision_normalized != "ACCEPT":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decisão inválida.")

            selected_bed: Optional[Dict[str, Any]] = None
            explicit_bed_id = bed_id if bed_id is not None else _to_int(transfer.get("bed_id"))
            if explicit_bed_id is not None:
                selected_bed = self._bed_by_id(state, explicit_bed_id)
            elif transfer.get("reservation_id") is not None:
                reservation_patient, reservation = self._reservation_lookup(state, int(transfer["reservation_id"]))
                if reservation_patient["external_id"] != patient["external_id"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reserva vinculada pertence a outro paciente.",
                    )
                if reservation.get("status") != ReservationStatus.ACEITA.value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reserva vinculada não está aceita.",
                    )
                res_bed_id = _to_int(reservation.get("bed_id"))
                if res_bed_id is not None:
                    selected_bed = self._bed_by_id(state, res_bed_id)
            if selected_bed is None:
                selected_bed = self._first_available_bed(state)

            if not selected_bed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nenhum leito livre para receber o paciente.",
                )
            if selected_bed["occupancy_status"] != BedOccupancy.LIVRE.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leito selecionado está ocupado.")

            accepted_reservation = self._accepted_reservation_for_bed(state, int(selected_bed["id"]))
            if accepted_reservation and accepted_reservation[0]["external_id"] != patient["external_id"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leito reservado para outro paciente.",
                )
            if (
                selected_bed["availability_status"] != BedAvailability.DISPONIVEL.value
                and selected_bed.get("reserved_for_patient") != patient["external_id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leito selecionado não está disponível para esta transferência.",
                )

            transfer["status"] = TransferStatus.ACEITA.value
            transfer["bed_id"] = int(selected_bed["id"])
            transfer["decided_at"] = now
            transfer["updated_at"] = now

            patient["location"] = "UTI"
            patient["current_bed_id"] = int(selected_bed["id"])
            patient["updated_at"] = now

            selected_bed["updated_at"] = now
            state["dirty"] = True

            self._notify(
                state,
                recipient=Role.SURGICAL_CENTER,
                type_=NotificationType.TRANSFERENCIA_ATUALIZADA,
                message=f"Transferência {transfer_id} aceita. UTI pronta para receber.",
                reference_type="transfer",
                reference_id=transfer_id,
            )
            return self._transfer_payload(transfer, patient)

        return await self.store.mutate(mutator)

    # --- Notificações ---------------------------------------------------------
    async def list_notifications(self, role: Role, unread_only: bool) -> List[Dict[str, Any]]:
        def reader(state: Dict[str, Any]) -> List[Dict[str, Any]]:
            notifications = [
                notification
                for notification in state["notifications"]
                if notification.get("recipient_role") == role.value and (not unread_only or not notification.get("read"))
            ]
            notifications.sort(key=lambda item: item.get("created_at") or "", reverse=True)
            return notifications

        return await self.store.read(reader)

    async def mark_notification(self, notification_id: int, read: bool = True) -> Dict[str, Any]:
        def mutator(state: Dict[str, Any]) -> Dict[str, Any]:
            for notification in state["notifications"]:
                if _to_int(notification.get("id")) != notification_id:
                    continue
                notification["read"] = bool(read)
                notification["updated_at"] = _now_iso()
                state["dirty"] = True
                return notification
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada.")

        return await self.store.mutate(mutator)

    async def mark_all_read(self, role: Role) -> None:
        def mutator(state: Dict[str, Any]) -> None:
            changed = False
            now = _now_iso()
            for notification in state["notifications"]:
                if notification.get("recipient_role") != role.value or notification.get("read") is True:
                    continue
                notification["read"] = True
                notification["updated_at"] = now
                changed = True
            if changed:
                state["dirty"] = True
            return None

        await self.store.mutate(mutator)

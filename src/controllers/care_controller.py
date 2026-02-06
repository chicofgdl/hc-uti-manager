from __future__ import annotations

from typing import List, Optional

from models.care import Role
from providers.implementations.app.care_provider import CareProvider
from schemas.care import (
    BedAvailabilityUpdate,
    BedOut,
    BedsCount,
    NotificationOut,
    ReservationCancelRequest,
    ReservationCreateRequest,
    ReservationDecisionRequest,
    ReservationOut,
    TransferCreateRequest,
    TransferDecisionRequest,
    TransferOut,
)


class CareController:
    """
    Orquestra regras de negócio expostas via API, delegando persistência
    ao CareProvider.
    """

    def __init__(self, provider: CareProvider):
        self.provider = provider

    # --- Leitos ---------------------------------------------------------------
    async def list_beds(self) -> List[BedOut]:
        beds = await self.provider.list_beds()
        return [BedOut.model_validate(bed) for bed in beds]

    async def set_bed_availability(self, bed_id: int, payload: BedAvailabilityUpdate) -> BedOut:
        bed = await self.provider.set_bed_availability(bed_id, payload.availableForReservation)
        return BedOut.model_validate(bed)

    async def available_count(self) -> BedsCount:
        count = await self.provider.available_count()
        return BedsCount(count=count)

    # --- Reservas -------------------------------------------------------------
    async def create_reservation(self, payload: ReservationCreateRequest) -> ReservationOut:
        reservation = await self.provider.create_reservation(
            patient_external_id=payload.patientId,
            notes=payload.notes,
            preferred_datetime=payload.preferredDateTime,
        )
        return ReservationOut.model_validate(reservation)

    async def list_reservations(self) -> List[ReservationOut]:
        reservations = await self.provider.list_reservations()
        return [ReservationOut.model_validate(res) for res in reservations]

    async def decide_reservation(self, reservation_id: int, payload: ReservationDecisionRequest) -> ReservationOut:
        reservation = await self.provider.decide_reservation(reservation_id, payload.decision, payload.bedId)
        return ReservationOut.model_validate(reservation)

    async def cancel_reservation(self, reservation_id: int, actor: Role, payload: ReservationCancelRequest) -> ReservationOut:
        reservation = await self.provider.cancel_reservation(reservation_id, actor, payload.reason)
        return ReservationOut.model_validate(reservation)

    # --- Transferências -------------------------------------------------------
    async def create_transfer(self, payload: TransferCreateRequest) -> TransferOut:
        transfer = await self.provider.create_transfer(
            patient_external_id=payload.patientId,
            reservation_id=payload.reservationId,
            bed_id=payload.bedId,
            notes=payload.notes,
        )
        return TransferOut.model_validate(transfer)

    async def list_transfers(self) -> List[TransferOut]:
        transfers = await self.provider.list_transfers()
        return [TransferOut.model_validate(tr) for tr in transfers]

    async def decide_transfer(self, transfer_id: int, payload: TransferDecisionRequest) -> TransferOut:
        transfer = await self.provider.decide_transfer(transfer_id, payload.decision, payload.bedId)
        return TransferOut.model_validate(transfer)

    # --- Notificações ---------------------------------------------------------
    async def list_notifications(self, role: Role, unread_only: bool) -> List[NotificationOut]:
        notifications = await self.provider.list_notifications(role, unread_only)
        return [NotificationOut.model_validate(n) for n in notifications]

    async def mark_notification(self, notification_id: int, read: bool = True) -> NotificationOut:
        notification = await self.provider.mark_notification(notification_id, read)
        return NotificationOut.model_validate(notification)

    async def mark_all_notifications(self, role: Role) -> None:
        await self.provider.mark_all_read(role)

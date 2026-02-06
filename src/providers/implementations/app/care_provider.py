from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.care import (
    Bed,
    BedAvailability,
    BedOccupancy,
    Notification,
    NotificationType,
    Patient,
    Reservation,
    ReservationStatus,
    Role,
    Transfer,
    TransferStatus,
)


class CareProvider:
    """
    Camada de acesso a dados + regras de negócio centrais para leitos, reservas,
    transferências e notificações.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Helpers internos -----------------------------------------------------

    async def _get_patient(self, external_id: str) -> Patient:
        stmt = select(Patient).where(Patient.external_id == external_id)
        patient = await self.session.scalar(stmt)
        if patient:
            return patient
        patient = Patient(external_id=external_id, location="CC")
        self.session.add(patient)
        await self.session.flush()
        return patient

    async def _notify(
        self,
        *,
        recipient: Role,
        type_: NotificationType,
        message: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> Notification:
        notification = Notification(
            recipient_role=recipient,
            type=type_,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def _first_available_bed(self) -> Optional[Bed]:
        stmt = (
            select(Bed)
            .where(
                Bed.availability_status == BedAvailability.DISPONIVEL,
                Bed.occupancy_status == BedOccupancy.LIVRE,
            )
            .order_by(Bed.code.asc())
        )
        return await self.session.scalar(stmt)

    # --- Leitos ---------------------------------------------------------------

    async def list_beds(self) -> List[Bed]:
        result = await self.session.execute(select(Bed).order_by(Bed.code))
        return result.scalars().all()

    async def set_bed_availability(self, bed_id: int, available: bool) -> Bed:
        bed = await self.session.get(Bed, bed_id)
        if not bed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leito não encontrado.")

        if available:
            if bed.occupancy_status != BedOccupancy.LIVRE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leito ocupado não pode ser disponibilizado para reserva.",
                )
            bed.availability_status = BedAvailability.DISPONIVEL
        else:
            # Regra: não permitir retirar disponibilidade se houver reserva pendente/aceita para o leito
            stmt = select(func.count()).select_from(Reservation).where(
                Reservation.bed_id == bed_id,
                Reservation.status.in_([ReservationStatus.PENDENTE, ReservationStatus.ACEITA]),
            )
            in_use = await self.session.scalar(stmt)
            if in_use:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Há reserva pendente/aceita para este leito. Cancele a reserva antes.",
                )
            bed.availability_status = BedAvailability.NAO_DISPONIVEL

        bed.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(bed)
        return bed

    async def available_count(self) -> int:
        stmt = select(func.count()).select_from(Bed).where(
            Bed.availability_status == BedAvailability.DISPONIVEL,
            Bed.occupancy_status == BedOccupancy.LIVRE,
        )
        return (await self.session.scalar(stmt)) or 0

    # --- Reservas -------------------------------------------------------------

    async def create_reservation(
        self,
        *,
        patient_external_id: str,
        notes: Optional[str],
        preferred_datetime: Optional[datetime],
    ) -> Reservation:
        async with self.session.begin():
            available = await self.available_count()
            if available == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não há leitos disponíveis para reserva.",
                )
            patient = await self._get_patient(patient_external_id)
            reservation = Reservation(
                patient=patient,
                notes=notes,
                preferred_datetime=preferred_datetime,
                requested_by=Role.SURGICAL_CENTER,
            )
            self.session.add(reservation)
            await self.session.flush()
            await self._notify(
                recipient=Role.ICU,
                type_=NotificationType.RESERVA_CRIADA,
                message=f"Nova solicitação de reserva para paciente {patient.external_id}",
                reference_type="reservation",
                reference_id=reservation.id,
            )
        await self.session.refresh(reservation)
        return reservation

    async def list_reservations(self) -> List[Reservation]:
        stmt = (
            select(Reservation)
            .options(joinedload(Reservation.patient))
            .order_by(Reservation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def decide_reservation(self, reservation_id: int, decision: str, bed_id: Optional[int]) -> Reservation:
        async with self.session.begin():
            reservation = await self.session.get(
                Reservation,
                reservation_id,
                options=[joinedload(Reservation.patient), joinedload(Reservation.bed)],
            )
            if not reservation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")
            if reservation.status != ReservationStatus.PENDENTE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Apenas reservas pendentes podem ser decididas."
                )

            if decision == "DENY":
                reservation.status = ReservationStatus.NEGADA
                reservation.decided_at = datetime.utcnow()
                await self._notify(
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.RESERVA_ATUALIZADA,
                    message=f"Reserva {reservation.id} negada pela UTI.",
                    reference_type="reservation",
                    reference_id=reservation.id,
                )
            elif decision == "ACCEPT":
                bed: Optional[Bed]
                if bed_id:
                    bed = await self.session.get(Bed, bed_id)
                    if not bed:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leito não encontrado.")
                else:
                    bed = await self._first_available_bed()
                if not bed or bed.availability_status != BedAvailability.DISPONIVEL or bed.occupancy_status != BedOccupancy.LIVRE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nenhum leito disponível para alocação.",
                    )
                bed.availability_status = BedAvailability.NAO_DISPONIVEL
                bed.updated_at = datetime.utcnow()
                reservation.bed = bed
                reservation.status = ReservationStatus.ACEITA
                reservation.decided_at = datetime.utcnow()
                await self._notify(
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.RESERVA_ATUALIZADA,
                    message=f"Reserva {reservation.id} aceita. Leito {bed.code} reservado.",
                    reference_type="reservation",
                    reference_id=reservation.id,
                )
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decisão inválida.")
        await self.session.refresh(reservation)
        return reservation

    async def cancel_reservation(self, reservation_id: int, actor: Role, reason: Optional[str]) -> Reservation:
        async with self.session.begin():
            reservation = await self.session.get(
                Reservation,
                reservation_id,
                options=[joinedload(Reservation.patient), joinedload(Reservation.bed)],
            )
            if not reservation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")
            if reservation.status not in (ReservationStatus.PENDENTE, ReservationStatus.ACEITA):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Somente reservas pendentes ou aceitas podem ser canceladas."
                )

            reservation.status = ReservationStatus.CANCELADA
            reservation.cancellation_reason = reason
            reservation.updated_at = datetime.utcnow()
            if reservation.bed and reservation.bed.occupancy_status == BedOccupancy.LIVRE:
                reservation.bed.availability_status = BedAvailability.DISPONIVEL
                reservation.bed.updated_at = datetime.utcnow()

            destinatario = Role.ICU if actor == Role.SURGICAL_CENTER else Role.SURGICAL_CENTER
            await self._notify(
                recipient=destinatario,
                type_=NotificationType.RESERVA_ATUALIZADA,
                message=f"Reserva {reservation.id} cancelada por {actor}.",
                reference_type="reservation",
                reference_id=reservation.id,
            )
        await self.session.refresh(reservation)
        return reservation

    # --- Transferências -------------------------------------------------------

    async def create_transfer(
        self,
        *,
        patient_external_id: str,
        reservation_id: Optional[int],
        bed_id: Optional[int],
        notes: Optional[str],
    ) -> Transfer:
        async with self.session.begin():
            patient = await self._get_patient(patient_external_id)
            reservation = None
            if reservation_id:
                reservation = await self.session.get(Reservation, reservation_id)
                if not reservation:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva vinculada não encontrada.")
                if reservation.status != ReservationStatus.ACEITA:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Somente reservas aceitas podem originar transferência.",
                    )

            transfer = Transfer(
                patient=patient,
                reservation=reservation,
                bed_id=bed_id,
                requested_by=Role.SURGICAL_CENTER,
            )
            self.session.add(transfer)
            await self.session.flush()
            await self._notify(
                recipient=Role.ICU,
                type_=NotificationType.TRANSFERENCIA_CRIADA,
                message=f"Solicitação de transferência para paciente {patient.external_id}.",
                reference_type="transfer",
                reference_id=transfer.id,
            )
        await self.session.refresh(transfer)
        return transfer

    async def list_transfers(self) -> List[Transfer]:
        stmt = (
            select(Transfer)
            .options(joinedload(Transfer.patient))
            .order_by(Transfer.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def decide_transfer(self, transfer_id: int, decision: str, bed_id: Optional[int]) -> Transfer:
        async with self.session.begin():
            transfer = await self.session.get(
                Transfer,
                transfer_id,
                options=[
                    joinedload(Transfer.patient),
                    joinedload(Transfer.reservation).joinedload(Reservation.bed),
                    joinedload(Transfer.bed),
                ],
            )
            if not transfer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transferência não encontrada.")
            if transfer.status != TransferStatus.PENDENTE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transferência já decidida.")

            if decision == "DENY":
                transfer.status = TransferStatus.NEGADA
                transfer.decided_at = datetime.utcnow()
                await self._notify(
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.TRANSFERENCIA_ATUALIZADA,
                    message=f"Transferência {transfer.id} negada pela UTI.",
                    reference_type="transfer",
                    reference_id=transfer.id,
                )
            elif decision == "ACCEPT":
                selected_bed: Optional[Bed] = None
                if bed_id:
                    selected_bed = await self.session.get(Bed, bed_id)
                    if not selected_bed:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leito não encontrado.")
                elif transfer.reservation and transfer.reservation.bed:
                    selected_bed = transfer.reservation.bed
                else:
                    selected_bed = await self._first_available_bed()

                if not selected_bed or selected_bed.occupancy_status != BedOccupancy.LIVRE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nenhum leito livre para receber o paciente.",
                    )

                # Se veio de reserva aceita, garantir que o leito está bloqueado para reserva
                selected_bed.availability_status = BedAvailability.NAO_DISPONIVEL
                selected_bed.occupancy_status = BedOccupancy.OCUPADO
                selected_bed.updated_at = datetime.utcnow()

                transfer.bed = selected_bed
                transfer.status = TransferStatus.ACEITA
                transfer.decided_at = datetime.utcnow()

                transfer.patient.location = "UTI"
                transfer.patient.current_bed_id = selected_bed.id
                transfer.patient.updated_at = datetime.utcnow()

                await self._notify(
                    recipient=Role.SURGICAL_CENTER,
                    type_=NotificationType.TRANSFERENCIA_ATUALIZADA,
                    message=f"Transferência {transfer.id} aceita. UTI pronta para receber.",
                    reference_type="transfer",
                    reference_id=transfer.id,
                )
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decisão inválida.")
        await self.session.refresh(transfer)
        return transfer

    # --- Notificações ---------------------------------------------------------

    async def list_notifications(self, role: Role, unread_only: bool) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.recipient_role == role)
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            stmt = stmt.where(Notification.read.is_(False))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_notification(self, notification_id: int, read: bool = True) -> Notification:
        notification = await self.session.get(Notification, notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada.")
        notification.read = read
        notification.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_all_read(self, role: Role) -> None:
        stmt = (
            select(Notification)
            .where(Notification.recipient_role == role, Notification.read.is_(False))
        )
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        for notif in notifications:
            notif.read = True
            notif.updated_at = datetime.utcnow()
        await self.session.commit()

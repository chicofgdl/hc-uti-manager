from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from resources.database import Base


# --- Enums --------------------------------------------------------------------


class Role(str, Enum):
    ICU = "ICU"
    SURGICAL_CENTER = "SURGICAL_CENTER"


class BedAvailability(str, Enum):
    NAO_DISPONIVEL = "NAO_DISPONIVEL"
    DISPONIVEL = "DISPONIVEL"


class BedOccupancy(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"


class ReservationStatus(str, Enum):
    PENDENTE = "PENDENTE"
    ACEITA = "ACEITA"
    NEGADA = "NEGADA"
    CANCELADA = "CANCELADA"


class TransferStatus(str, Enum):
    PENDENTE = "PENDENTE"
    ACEITA = "ACEITA"
    NEGADA = "NEGADA"
    CANCELADA = "CANCELADA"


class NotificationType(str, Enum):
    RESERVA_CRIADA = "RESERVA_CRIADA"
    RESERVA_ATUALIZADA = "RESERVA_ATUALIZADA"
    TRANSFERENCIA_CRIADA = "TRANSFERENCIA_CRIADA"
    TRANSFERENCIA_ATUALIZADA = "TRANSFERENCIA_ATUALIZADA"


# --- Models -------------------------------------------------------------------


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g. "CC", "UTI"
    current_bed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("beds.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    current_bed = relationship("Bed", foreign_keys=[current_bed_id])
    reservations = relationship("Reservation", back_populates="patient")
    transfers = relationship("Transfer", back_populates="patient")


class Bed(Base):
    __tablename__ = "beds"
    __table_args__ = (UniqueConstraint("code", name="uq_beds_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    availability_status: Mapped[BedAvailability] = mapped_column(
        SqlEnum(BedAvailability), default=BedAvailability.NAO_DISPONIVEL, nullable=False
    )
    occupancy_status: Mapped[BedOccupancy] = mapped_column(
        SqlEnum(BedOccupancy), default=BedOccupancy.LIVRE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="bed")
    transfers = relationship("Transfer", back_populates="bed")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    status: Mapped[ReservationStatus] = mapped_column(
        SqlEnum(ReservationStatus), default=ReservationStatus.PENDENTE, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("beds.id"), nullable=True)
    requested_by: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.SURGICAL_CENTER, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="reservations")
    bed = relationship("Bed", back_populates="reservations")
    transfers = relationship("Transfer", back_populates="reservation")


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    reservation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reservations.id"), nullable=True)
    bed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("beds.id"), nullable=True)
    status: Mapped[TransferStatus] = mapped_column(
        SqlEnum(TransferStatus), default=TransferStatus.PENDENTE, nullable=False
    )
    requested_by: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.SURGICAL_CENTER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="transfers")
    reservation = relationship("Reservation", back_populates="transfers")
    bed = relationship("Bed", back_populates="transfers")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[NotificationType] = mapped_column(SqlEnum(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recipient_role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False, index=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


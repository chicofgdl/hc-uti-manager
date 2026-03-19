from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from models.care import (
    BedAvailability,
    BedOccupancy,
    NotificationType,
    ReservationStatus,
    Role,
    TransferStatus,
)


class BedAvailabilityUpdate(BaseModel):
    availableForReservation: bool = Field(..., description="Define se o leito deve ficar disponível para reserva.")


class BedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    availability_status: BedAvailability
    occupancy_status: BedOccupancy
    created_at: datetime
    updated_at: datetime


class BedsCount(BaseModel):
    count: int


class ReservationCreateRequest(BaseModel):
    patientId: str
    notes: Optional[str] = None
    preferredDateTime: Optional[datetime] = None


class ReservationDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|DENY)$")
    bedId: Optional[int] = None


class ReservationCancelRequest(BaseModel):
    reason: Optional[str] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    name: Optional[str] = None
    location: Optional[str] = None
    current_bed_id: Optional[int] = None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ReservationStatus
    patient: PatientOut
    notes: Optional[str] = None
    preferred_datetime: Optional[datetime] = None
    bed_id: Optional[int] = None
    requested_by: Role
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    decided_at: Optional[datetime] = None


class TransferCreateRequest(BaseModel):
    patientId: str
    reservationId: Optional[int] = None
    bedId: Optional[int] = None
    notes: Optional[str] = None


class TransferDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|DENY)$")
    bedId: Optional[int] = None


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TransferStatus
    patient: PatientOut
    reservation_id: Optional[int] = None
    bed_id: Optional[int] = None
    requested_by: Role
    created_at: datetime
    updated_at: datetime
    decided_at: Optional[datetime] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    message: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    recipient_role: Role
    read: bool
    created_at: datetime
    updated_at: datetime


class NotificationReadRequest(BaseModel):
    read: bool = True

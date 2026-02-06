from fastapi import APIRouter, Depends, Query, status

from auth.auth import auth_handler
from controllers.care_controller import CareController
from dependencies import get_care_controller
from models.care import Role
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

router = APIRouter(prefix="/api", tags=["UTI & CC"])


# --- Beds (UTI) --------------------------------------------------------------
@router.get("/icu/beds", response_model=list[BedOut], dependencies=[Depends(auth_handler.decode_token)])
async def list_beds(controller: CareController = Depends(get_care_controller)):
    return await controller.list_beds()


@router.patch(
    "/icu/beds/{bed_id}/availability",
    response_model=BedOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def update_bed_availability(
    bed_id: int,
    payload: BedAvailabilityUpdate,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.set_bed_availability(bed_id, payload)


@router.get(
    "/icu/beds/available-count",
    response_model=BedsCount,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def available_beds_count(controller: CareController = Depends(get_care_controller)):
    return await controller.available_count()


# --- Reservations ------------------------------------------------------------
@router.post(
    "/surgical-center/reservations",
    status_code=status.HTTP_201_CREATED,
    response_model=ReservationOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def create_reservation(
    payload: ReservationCreateRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.create_reservation(payload)


@router.get(
    "/surgical-center/reservations",
    response_model=list[ReservationOut],
    dependencies=[Depends(auth_handler.decode_token)],
)
async def list_reservations_cc(controller: CareController = Depends(get_care_controller)):
    return await controller.list_reservations()


@router.get(
    "/icu/reservations",
    response_model=list[ReservationOut],
    dependencies=[Depends(auth_handler.decode_token)],
)
async def list_reservations_icu(controller: CareController = Depends(get_care_controller)):
    return await controller.list_reservations()


@router.patch(
    "/icu/reservations/{reservation_id}/decision",
    response_model=ReservationOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def decide_reservation(
    reservation_id: int,
    payload: ReservationDecisionRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.decide_reservation(reservation_id, payload)


@router.patch(
    "/surgical-center/reservations/{reservation_id}/cancel",
    response_model=ReservationOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def cancel_reservation_cc(
    reservation_id: int,
    payload: ReservationCancelRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.cancel_reservation(reservation_id, Role.SURGICAL_CENTER, payload)


@router.patch(
    "/icu/reservations/{reservation_id}/cancel",
    response_model=ReservationOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def cancel_reservation_icu(
    reservation_id: int,
    payload: ReservationCancelRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.cancel_reservation(reservation_id, Role.ICU, payload)


# --- Transfers ---------------------------------------------------------------
@router.post(
    "/surgical-center/transfers",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def create_transfer(
    payload: TransferCreateRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.create_transfer(payload)


@router.get(
    "/surgical-center/transfers",
    response_model=list[TransferOut],
    dependencies=[Depends(auth_handler.decode_token)],
)
async def list_transfers_cc(controller: CareController = Depends(get_care_controller)):
    return await controller.list_transfers()


@router.get(
    "/icu/transfers",
    response_model=list[TransferOut],
    dependencies=[Depends(auth_handler.decode_token)],
)
async def list_transfers_icu(controller: CareController = Depends(get_care_controller)):
    return await controller.list_transfers()


@router.patch(
    "/icu/transfers/{transfer_id}/decision",
    response_model=TransferOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def decide_transfer(
    transfer_id: int,
    payload: TransferDecisionRequest,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.decide_transfer(transfer_id, payload)


# --- Notifications -----------------------------------------------------------
@router.get(
    "/notifications",
    response_model=list[NotificationOut],
    dependencies=[Depends(auth_handler.decode_token)],
)
async def list_notifications(
    role: Role = Query(..., description="ICU ou SURGICAL_CENTER"),
    unreadOnly: bool = Query(False),
    controller: CareController = Depends(get_care_controller),
):
    return await controller.list_notifications(role, unreadOnly)


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationOut,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def mark_notification_read(
    notification_id: int,
    controller: CareController = Depends(get_care_controller),
):
    return await controller.mark_notification(notification_id, True)


@router.patch(
    "/notifications/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_handler.decode_token)],
)
async def mark_all_notifications(
    role: Role = Query(..., description="ICU ou SURGICAL_CENTER"),
    controller: CareController = Depends(get_care_controller),
):
    await controller.mark_all_notifications(role)
    return None

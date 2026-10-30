
from datetime import date
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from src.api.v1.dependencies import (
    get_current_user_or_internal_service,
    get_current_user_payload,
    require_internal_service,
)
from src.core.database import get_db
from src.schemas.booking_schema import (
    BookingCreateRequest,
    BookingPaginatedResponse,
    BookingResponse,
)
from src.services.booking_service import BookingService


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


# =========================================================
# 1. CAC HAM HO TRO
# =========================================================

def get_user_id(user_payload: dict) -> int:
    try:
        user_id = int(user_payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thong tin tai khoan trong token khong hop le.",
        )

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID tai khoan khong hop le.",
        )

    return user_id


def get_user_role(user_payload: dict) -> str:
    return str(user_payload.get("role", "USER")).upper()


# =========================================================
# 2. TAO BOOKING
# =========================================================

@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    payload: BookingCreateRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload),
):
    role = get_user_role(user_payload)
    current_user_id = get_user_id(user_payload)

    if role == "ADMIN" and payload.id_tai_khoan is not None:
        booking_user_id = payload.id_tai_khoan
    else:
        booking_user_id = current_user_id

    return BookingService.create_booking(
        db=db,
        payload=payload,
        current_user_id=booking_user_id,
    )


# =========================================================
# 3. LAY DANH SACH BOOKING
# =========================================================

@router.get(
    "",
    response_model=BookingPaginatedResponse,
)
def get_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
    ),
    id_khach_san: Optional[int] = Query(
        default=None,
        ge=1,
    ),
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user_payload: dict = Depends(
        get_current_user_or_internal_service
    ),
):
    role = get_user_role(user_payload)

    if role in ("ADMIN", "SERVICE"):
        current_user_id = None
    else:
        current_user_id = get_user_id(user_payload)

    items, total, total_pages = BookingService.get_all_bookings(
        db=db,
        page=page,
        page_size=page_size,
        user_id=current_user_id,
        hotel_id=id_khach_san,
        status_filter=status_filter,
        keyword=keyword,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# =========================================================
# 4. LAY DANH SACH PHONG DA DUOC DAT
# =========================================================

@router.get("/booked-room-ids")
def get_booked_room_ids(
    id_khach_san: int = Query(..., ge=1),
    ngay_nhan_phong: date = Query(...),
    ngay_tra_phong: date = Query(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_service),
):
    return BookingService.get_booked_room_ids(
        db=db,
        hotel_id=id_khach_san,
        check_in=ngay_nhan_phong,
        check_out=ngay_tra_phong,
    )


# =========================================================
# 5. LAY CHI TIET BOOKING
# =========================================================

@router.get(
    "/{id_or_code}",
    response_model=BookingResponse,
)
def get_booking_detail(
    id_or_code: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(
        get_current_user_or_internal_service
    ),
):
    booking = BookingService.get_booking_by_id_or_code(
        db=db,
        id_or_code=id_or_code,
    )

    role = get_user_role(user_payload)

    if role not in ("ADMIN", "SERVICE"):
        current_user_id = get_user_id(user_payload)

        if booking.id_tai_khoan != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ban khong co quyen xem don dat phong nay.",
            )

    return booking


# =========================================================
# 6. XAC NHAN BOOKING
# =========================================================

@router.patch(
    "/{id_or_code}/confirm",
    response_model=BookingResponse,
)
def confirm_booking(
    id_or_code: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_service),
):
    return BookingService.confirm_booking(
        db=db,
        id_or_code=id_or_code,
    )


# =========================================================
# 7. HUY BOOKING
# =========================================================

@router.patch(
    "/{id_or_code}/cancel",
    response_model=BookingResponse,
)
def cancel_booking(
    id_or_code: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload),
):
    booking = BookingService.get_booking_by_id_or_code(
        db=db,
        id_or_code=id_or_code,
    )

    role = get_user_role(user_payload)

    if role != "ADMIN":
        current_user_id = get_user_id(user_payload)

        if booking.id_tai_khoan != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ban khong co quyen huy don dat phong nay.",
            )

    return BookingService.cancel_booking(
        db=db,
        id_or_code=id_or_code,
    )


# =========================================================
# 8. GIAI PHONG BOOKING HET HAN
# =========================================================

@router.post("/release-expired")
def release_expired_bookings(
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_service),
):
    released_count = BookingService.release_expired_holds(
        db=db,
    )

    return {
        "message": "Da xu ly booking het han giu cho.",
        "released_count": released_count,
    }

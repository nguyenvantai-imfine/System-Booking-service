from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.api.v1.dependencies import get_db, get_current_user_payload
from src.schemas import (
    BookingCreateRequest,
    BookingResponse,
    BookingPaginatedResponse,
    BookingStatusUpdate,
)
from src.services import BookingService

router = APIRouter(prefix="/bookings", tags=["📋 Quản lý Đặt Phòng"])

# 1. Tạo đơn đặt phòng mới (Chống trùng phòng + Giữ chỗ 15 phút)
@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo đơn đặt phòng mới (Giữ chỗ 15 phút)",
)
def create_booking(
    payload: BookingCreateRequest,
    db: Session = Depends(get_db),
    user_payload: Optional[dict] = Depends(get_current_user_payload),
):
    current_user_id = None
    if user_payload and "sub" in user_payload:
        try:
            current_user_id = int(user_payload["sub"])
        except Exception:
            pass

    return BookingService.create_booking(
        db=db, payload=payload, current_user_id=current_user_id
    )

# 2. Danh sách toàn bộ đơn đặt phòng kèm phân trang & lọc
@router.get(
    "",
    response_model=BookingPaginatedResponse,
    summary="Danh sách đơn đặt phòng",
)
def get_bookings(
    hotel_id: Optional[int] = Query(None, description="Lọc theo khách sạn"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: PENDING_PAYMENT, CONFIRMED, CANCELLED..."),
    keyword: Optional[str] = Query(None, description="Tìm theo mã booking, tên khách, email, SĐT"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total, total_pages = BookingService.get_all_bookings(
        db=db,
        hotel_id=hotel_id,
        status_filter=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

# 3. Xem chi tiết đơn đặt phòng theo ID hoặc mã Booking
@router.get(
    "/{id_or_code}",
    response_model=BookingResponse,
    summary="Xem chi tiết đơn đặt phòng",
)
def get_booking_detail(
    id_or_code: str,
    db: Session = Depends(get_db),
):
    return BookingService.get_booking_by_id_or_code(db, id_or_code)

# 4. Xác nhận đơn sau khi thanh toán thành công
@router.patch(
    "/{id_or_code}/confirm",
    response_model=BookingResponse,
    summary="Xác nhận thanh toán thành công (CONFIRMED)",
)
def confirm_booking(
    id_or_code: str,
    note: Optional[str] = Query(None, description="Ghi chú xác nhận"),
    db: Session = Depends(get_db),
):
    return BookingService.confirm_booking(db, id_or_code, note=note)

# 5. Hủy đơn đặt phòng và nhả phòng
@router.patch(
    "/{id_or_code}/cancel",
    response_model=BookingResponse,
    summary="Hủy đơn đặt phòng và giải phóng phòng (CANCELLED)",
)
def cancel_booking(
    id_or_code: str,
    reason: Optional[str] = Query(None, description="Lý do hủy đơn"),
    db: Session = Depends(get_db),
):
    return BookingService.cancel_booking(db, id_or_code, reason=reason)

# 6. Kích hoạt giải phóng các đơn giữ chỗ đã hết hạn
@router.post(
    "/release-expired",
    summary="Kích hoạt quét và nhả các phòng giữ chỗ quá 15 phút",
)
def release_expired_holds(db: Session = Depends(get_db)):
    count = BookingService.release_expired_holds(db)
    return {"message": f"Đã giải phóng {count} đơn giữ chỗ hết hạn.", "released_count": count}

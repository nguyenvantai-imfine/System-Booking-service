from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
import math

from src.core.config import settings
from src.core.database import get_db
from src.core.security import get_current_user_id
from src.schemas.notification_schema import (
    SendNotificationRequest,
    ThongBaoResponse,
    PaginatedNotifications,
    NotificationStats,
)
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/send", response_model=ThongBaoResponse, status_code=status.HTTP_201_CREATED)
def send_notification(
    req: SendNotificationRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Tạo thông báo cho tài khoản đang đăng nhập."""
    req = req.model_copy(update={"id_tai_khoan": user_id})
    return NotificationService.send_notification(db, req)

@router.post("/internal-send", response_model=ThongBaoResponse, status_code=status.HTTP_201_CREATED)
def internal_send_notification(
    req: SendNotificationRequest,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret"),
):
    """
    Endpoint nội bộ dành riêng cho Booking Service & Payment Service gửi thông báo qua REST Fallback.
    Xác thực bằng Header X-Internal-Secret thay vì JWT Token người dùng.
    """
    expected_secret = getattr(settings, "INTERNAL_SERVICE_SECRET", "booking_internal_secret_key_2026")
    if not x_internal_secret or x_internal_secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Khóa xác thực dịch vụ nội bộ (X-Internal-Secret) không hợp lệ.",
        )
    return NotificationService.send_notification(db, req)

@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Lấy thống kê số lượng thông báo theo trạng thái"""
    return NotificationService.get_stats(db, user_id)

@router.get("", response_model=PaginatedNotifications)
def get_notifications(
    status: Optional[str] = Query(None, description="SENT, FAILED, PENDING, ALL"),
    notification_type: Optional[str] = Query(None, description="BOOKING_CONFIRMED, PAYMENT_SUCCESS, BOOKING_CANCELLED, OTP"),
    recipient: Optional[str] = Query(None, description="Tìm theo email người nhận"),
    booking_code: Optional[str] = Query(None, description="Tìm theo mã booking"),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Lấy danh sách lịch sử thông báo kèm phân trang và bộ lọc"""
    items, total = NotificationService.get_notifications(
        db=db,
        user_id=user_id,
        status=status,
        notification_type=notification_type,
        recipient=recipient,
        booking_code=booking_code,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedNotifications(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

@router.get("/{id_thong_bao}", response_model=ThongBaoResponse)
def get_notification_detail(
    id_thong_bao: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Lấy chi tiết thông báo theo ID"""
    item = NotificationService.get_notification_by_id(db, id_thong_bao, user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo này.",
        )
    return item

@router.get("/{id_thong_bao}/preview", response_class=HTMLResponse)
def preview_email_html(
    id_thong_bao: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Xem trực tiếp giao diện HTML của email đã gửi"""
    item = NotificationService.get_notification_by_id(db, id_thong_bao, user_id)
    if not item or not item.noi_dung:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nội dung email.",
        )
    return HTMLResponse(content=item.noi_dung.noi_dung_html)


@router.patch("/{id_thong_bao}/read", response_model=ThongBaoResponse)
def mark_notification_as_read(
    id_thong_bao: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    item = NotificationService.mark_as_read(db, id_thong_bao, user_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo này.",
        )
    return item


@router.delete("/{id_thong_bao}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    id_thong_bao: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    deleted = NotificationService.delete_notification(db, id_thong_bao, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo này.",
        )

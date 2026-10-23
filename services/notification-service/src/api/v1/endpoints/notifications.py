from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
import math

from src.core.database import get_db
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
):
    """API gửi thông báo trực tiếp qua Email/SMS và lưu vết vào CSDL"""
    try:
        return NotificationService.send_notification(db, req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi gửi thông báo: {str(e)}",
        )

@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(db: Session = Depends(get_db)):
    """Lấy thống kê số lượng thông báo theo trạng thái"""
    return NotificationService.get_stats(db)

@router.get("", response_model=PaginatedNotifications)
def get_notifications(
    status: Optional[str] = Query(None, description="SENT, FAILED, PENDING, ALL"),
    notification_type: Optional[str] = Query(None, description="BOOKING_CONFIRMED, PAYMENT_SUCCESS, BOOKING_CANCELLED, OTP"),
    recipient: Optional[str] = Query(None, description="Tìm theo email người nhận"),
    booking_code: Optional[str] = Query(None, description="Tìm theo mã booking"),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lấy danh sách lịch sử thông báo kèm phân trang và bộ lọc"""
    items, total = NotificationService.get_notifications(
        db=db,
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
):
    """Lấy chi tiết thông báo theo ID"""
    item = NotificationService.get_notification_by_id(db, id_thong_bao)
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
):
    """Xem trực tiếp giao diện HTML của email đã gửi"""
    item = NotificationService.get_notification_by_id(db, id_thong_bao)
    if not item or not item.noi_dung:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nội dung email.",
        )
    return HTMLResponse(content=item.noi_dung.noi_dung_html)

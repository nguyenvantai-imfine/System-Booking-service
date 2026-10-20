from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

class SendNotificationRequest(BaseModel):
    loai_thong_bao: str # BOOKING_CONFIRMED, PAYMENT_SUCCESS, BOOKING_CANCELLED, SYSTEM
    nguoi_nhan: str # Email or Phone
    kenh_gui: str = "EMAIL"
    id_tai_khoan: Optional[int] = None
    ma_booking: Optional[str] = None
    du_lieu: Dict[str, Any] = {}

class NoiDungResponse(BaseModel):
    id_noi_dung: int
    tieu_de: str
    noi_dung_html: str
    noi_dung_text: Optional[str] = None
    du_lieu_dinh_kem: Optional[str] = None

    class Config:
        from_attributes = True

class ThongBaoResponse(BaseModel):
    id_thong_bao: int
    id_tai_khoan: Optional[int] = None
    loai_thong_bao: str
    kenh_gui: str
    nguoi_nhan: str
    trang_thai: str
    ma_booking: Optional[str] = None
    ngay_tao: datetime
    ngay_gui: Optional[datetime] = None
    ghi_chu_loi: Optional[str] = None
    noi_dung: Optional[NoiDungResponse] = None

    class Config:
        from_attributes = True

class PaginatedNotifications(BaseModel):
    items: List[ThongBaoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class NotificationStats(BaseModel):
    total_notifications: int
    sent_count: int
    failed_count: int
    pending_count: int

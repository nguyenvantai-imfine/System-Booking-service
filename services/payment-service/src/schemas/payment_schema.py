from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from src.models.thanh_toan import PhuongThucThanhToanEnum, TrangThaiThanhToanEnum

class GenerateOtpRequest(BaseModel):
    ma_giao_dich_gateway: str = Field(..., min_length=5, max_length=100, description="Mã giao dịch gateway")
    email: EmailStr = Field(..., description="Email nhận mã OTP")

class VerifyOtpRequest(BaseModel):
    ma_giao_dich_gateway: str = Field(..., min_length=5, max_length=100, description="Mã giao dịch gateway")
    otp_code: str = Field(..., pattern=r"^\d{6}$", description="Mã OTP đúng 6 ký tự, chỉ gồm chữ số")

class OtpResponse(BaseModel):
    success: bool = Field(..., description="Trạng thái thao tác OTP")
    message: str = Field(..., description="Thông điệp thông báo")
    ma_giao_dich_gateway: str = Field(..., description="Mã giao dịch gateway")
    expires_in_seconds: Optional[int] = Field(None, description="Thời gian hiệu lực tính bằng giây")

class CreatePaymentRequest(BaseModel):
    id_dat_phong: int = Field(..., ge=1)
    ma_booking: str = Field(..., min_length=5, max_length=50)
    so_tien: float = Field(..., gt=0)
    phuong_thuc: PhuongThucThanhToanEnum = PhuongThucThanhToanEnum.VNPAY
    ghi_chu: Optional[str] = Field(None, max_length=255)

class SimulateIpnRequest(BaseModel):
    ma_giao_dich_gateway: str = Field(..., min_length=5, max_length=100)
    trang_thai: TrangThaiThanhToanEnum = TrangThaiThanhToanEnum.SUCCESS
    note: Optional[str] = Field("Mô phỏng IPN từ cổng thanh toán", max_length=255)

class PaymentResponse(BaseModel):
    id_thanh_toan: int
    id_dat_phong: int
    ma_booking: str
    so_tien: float
    phuong_thuc: PhuongThucThanhToanEnum
    trang_thai: TrangThaiThanhToanEnum
    ma_giao_dich_gateway: str
    payment_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    ngay_tao: datetime
    ngay_thanh_toan: Optional[datetime] = None
    ghi_chu: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PaymentPaginatedResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class PaymentStatsResponse(BaseModel):
    total_revenue: float
    total_transactions: int
    success_count: int
    pending_count: int
    failed_count: int

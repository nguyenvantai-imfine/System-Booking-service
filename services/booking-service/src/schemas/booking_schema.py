from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from src.models.dat_phong import TrangThaiBookingEnum

# Thông tin khách ở
class ThongTinKhachOBase(BaseModel):
    ho_ten: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    sdt: str = Field(..., min_length=6, max_length=20)
    ghi_chu_dac_biet: Optional[str] = Field(None, max_length=500)

class ThongTinKhachOCreate(ThongTinKhachOBase):
    pass

class ThongTinKhachOResponse(ThongTinKhachOBase):
    id_khach_o: int
    id_dat_phong: int

    model_config = ConfigDict(from_attributes=True)

# Chi tiết phòng đặt
class ChiTietDatPhongCreate(BaseModel):
    id_phong: int = Field(..., ge=1)
    id_loai_phong: int = Field(..., ge=1)
    so_phong: Optional[str] = Field(None, max_length=50)
    ten_loai_phong: Optional[str] = Field(None, max_length=100)
    gia: float = Field(..., gt=0, description="Giá 1 đêm tại thời điểm đặt")

class ChiTietDatPhongResponse(BaseModel):
    id_chi_tiet: int
    id_dat_phong: int
    id_phong: int
    id_loai_phong: int
    so_phong: Optional[str]
    ten_loai_phong: Optional[str]
    gia_tai_thoi_diem_dat: float

    model_config = ConfigDict(from_attributes=True)

# Nhật ký
class NhatKyBookingResponse(BaseModel):
    id_nhat_ky: int
    trang_thai_cu: Optional[str]
    trang_thai_moi: str
    ly_do: Optional[str]
    thoi_gian: datetime

    model_config = ConfigDict(from_attributes=True)

# Yêu cầu đặt phòng mới
class BookingCreateRequest(BaseModel):
    id_khach_san: int = Field(..., ge=1)
    ngay_nhan_phong: date
    ngay_tra_phong: date
    rooms: List[ChiTietDatPhongCreate] = Field(..., min_length=1)
    khach_o: ThongTinKhachOCreate
    id_tai_khoan: Optional[int] = Field(None, description="Tự động trích xuất từ JWT hoặc truyền lên")

# Phản hồi đơn đặt phòng
class BookingResponse(BaseModel):
    id_dat_phong: int
    ma_booking: str
    id_tai_khoan: int
    id_khach_san: int
    ngay_nhan_phong: date
    ngay_tra_phong: date
    tien_phong: Optional[float] = Field(None, description="Tổng tiền phòng trước thuế/phí")
    thue_phi: Optional[float] = Field(0.0, description="Thuế và phí VAT 10%")
    tong_tien: float
    trang_thai: TrangThaiBookingEnum
    han_giu_cho: datetime
    ngay_tao: datetime
    ngay_cap_nhat: datetime
    chi_tiet: List[ChiTietDatPhongResponse] = []
    khach_o: Optional[ThongTinKhachOResponse] = None
    nhat_ky: List[NhatKyBookingResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def ensure_tax_and_room_amount(self):
        if self.tien_phong is None and self.tong_tien is not None:
            tax = self.thue_phi or 0.0
            self.tien_phong = round(float(self.tong_tien) - float(tax), 2)
        return self

# Danh sách phân trang
class BookingPaginatedResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Cập nhật trạng thái
class BookingStatusUpdate(BaseModel):
    trang_thai: TrangThaiBookingEnum
    ly_do: Optional[str] = Field(None, max_length=255)

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from src.models.tai_khoan import VaiTroEnum, TrangThaiTaiKhoanEnum

class NguoiDungProfile(BaseModel):
    id_nguoi_dung: Optional[int] = None
    ho: Optional[str] = None
    ten: Optional[str] = None
    ho_va_ten: Optional[str] = None
    ngay_sinh: Optional[date] = None
    gioi_tinh: Optional[str] = None
    dia_chi: Optional[str] = None
    avatar: Optional[str] = None
    cccd: Optional[str] = None

class NguoiDungUpdate(BaseModel):
    ho: Optional[str] = Field(None, max_length=50)
    ten: Optional[str] = Field(None, max_length=50)
    ngay_sinh: Optional[date] = None
    gioi_tinh: Optional[str] = Field(None, max_length=10)
    dia_chi: Optional[str] = Field(None, max_length=255)
    avatar: Optional[str] = Field(None, max_length=500)
    cccd: Optional[str] = Field(None, max_length=20)
    sdt: Optional[str] = Field(None, max_length=20)

class TaiKhoanResponse(BaseModel):
    id_tai_khoan: int
    ten_dang_nhap: str
    email: str
    sdt: Optional[str] = None
    vai_tro: VaiTroEnum
    trang_thai: TrangThaiTaiKhoanEnum
    ngay_tao: datetime
    profile: Optional[NguoiDungProfile] = None
    nguoi_dung: Optional[NguoiDungProfile] = None

class UserStatusUpdate(BaseModel):
    trang_thai: TrangThaiTaiKhoanEnum

class UserPaginatedResponse(BaseModel):
    items: List[TaiKhoanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class UserActionResponse(BaseModel):
    message: str
    id_tai_khoan: Optional[int] = None
    success: bool = True


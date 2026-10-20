from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from src.models.tai_khoan import VaiTroEnum, TrangThaiTaiKhoanEnum

class RegisterRequest(BaseModel):
    ten_dang_nhap: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    email: EmailStr = Field(..., description="Email tài khoản")
    mat_khau: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    sdt: Optional[str] = Field(None, max_length=20, description="Số điện thoại")
    vai_tro: VaiTroEnum = Field(default=VaiTroEnum.CUSTOMER, description="Vai trò: CUSTOMER hoặc PARTNER")
    ho: Optional[str] = Field(None, max_length=50, description="Họ đệm")
    ten: Optional[str] = Field(None, max_length=50, description="Tên")

class LoginRequest(BaseModel):
    ten_dang_nhap_hoac_email: str = Field(..., description="Tên đăng nhập hoặc Email")
    mat_khau: str = Field(..., description="Mật khẩu tài khoản")

class UserBrief(BaseModel):
    id_tai_khoan: int
    ten_dang_nhap: str
    email: str
    vai_tro: VaiTroEnum
    trang_thai: TrangThaiTaiKhoanEnum
    ho_va_ten: Optional[str] = None
    avatar: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserBrief

class RefreshTokenRequest(BaseModel):
    refresh_token: str

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["🔐 Xác thực & Phân quyền"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="Hỗ trợ người dùng đăng ký vai trò Khách hàng (CUSTOMER) hoặc Đối tác khách sạn (PARTNER).",
)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService.register(db, req)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập hệ thống",
    description="Xác thực bằng Tên đăng nhập hoặc Email kèm Mật khẩu. Trả về cặp Access Token và Refresh Token.",
)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, req)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Làm mới Access Token",
    description="Sử dụng Refresh Token hợp lệ để lấy Access Token mới mà không cần đăng nhập lại.",
)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService.refresh(db, req.refresh_token)

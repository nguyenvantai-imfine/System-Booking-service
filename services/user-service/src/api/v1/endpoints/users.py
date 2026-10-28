from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models import TaiKhoanModel, VaiTroEnum
from src.schemas.user_schema import TaiKhoanResponse, NguoiDungUpdate, UserActionResponse
from src.services.user_service import UserService
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["👤 Quản lý Tài khoản Cá nhân"])

@router.get(
    "/me",
    response_model=TaiKhoanResponse,
    summary="Lấy thông tin tài khoản đang đăng nhập",
    description="Trả về thông tin tài khoản và profile cá nhân từ JWT token.",
)
def get_my_info(
    current_user: TaiKhoanModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService.get_me(db, current_user.id_tai_khoan)

@router.put(
    "/me",
    response_model=TaiKhoanResponse,
    summary="Cập nhật hồ sơ cá nhân",
    description="Cập nhật họ tên, ngày sinh, giới tính, địa chỉ, số điện thoại, avatar, CCCD.",
)
def update_my_profile(
    req: NguoiDungUpdate,
    current_user: TaiKhoanModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService.update_profile(db, current_user.id_tai_khoan, req)

@router.delete(
    "/me",
    response_model=UserActionResponse,
    summary="Xóa tài khoản cá nhân",
    description="Người dùng tự xóa vĩnh viễn tài khoản của chính mình khỏi hệ thống.",
)
def delete_my_account(
    current_user: TaiKhoanModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService.delete_user_self(db, current_user.id_tai_khoan)

@router.get(
    "/{user_id}",
    response_model=TaiKhoanResponse,
    summary="Tìm kiếm thông tin người dùng theo ID",
    description="Lấy thông tin tài khoản và profile cơ bản theo id_tai_khoan.",
)
def get_user_by_id(
    user_id: int,
    current_user: TaiKhoanModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id_tai_khoan != user_id and current_user.vai_tro != VaiTroEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập thông tin của tài khoản khác.",
        )
    return UserService.get_me(db, user_id)


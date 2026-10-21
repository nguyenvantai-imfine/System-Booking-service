from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models import TaiKhoanModel, VaiTroEnum, TrangThaiTaiKhoanEnum
from src.schemas.user_schema import (
    TaiKhoanResponse,
    UserStatusUpdate,
    UserPaginatedResponse,
    UserActionResponse,
)
from src.schemas.auth_schema import RegisterRequest
from src.services.user_service import UserService
from src.api.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["🛡️ Quản trị Người Dùng (Admin)"])

@router.get(
    "/users",
    response_model=UserPaginatedResponse,
    summary="[Admin] Danh sách toàn bộ người dùng",
    description="Chỉ dành cho Quản trị viên (Admin). Hỗ trợ tìm kiếm theo từ khóa, lọc theo vai trò và trạng thái.",
)
def get_all_users(
    role: Optional[VaiTroEnum] = Query(None, description="Lọc theo vai trò (ADMIN, PARTNER, CUSTOMER)"),
    vai_tro: Optional[VaiTroEnum] = Query(None, description="Lọc theo vai trò (alias)"),
    status: Optional[TrangThaiTaiKhoanEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, LOCKED, INACTIVE)"),
    trang_thai: Optional[TrangThaiTaiKhoanEnum] = Query(None, description="Lọc theo trạng thái (alias)"),
    keyword: Optional[str] = Query(None, description="Tìm theo ID, tên đăng nhập, email, họ tên, SĐT"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    selected_role = role or vai_tro
    selected_status = status or trang_thai
    return UserService.get_users_admin(
        db=db,
        role=selected_role,
        status_val=selected_status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

@router.post(
    "/users",
    response_model=TaiKhoanResponse,
    status_code=201,
    summary="[Admin] Tạo mới tài khoản người dùng",
    description="Quản trị viên tạo tài khoản mới với vai trò tùy chọn (ADMIN, PARTNER, CUSTOMER).",
)
def create_user_admin(
    req: RegisterRequest,
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService.admin_create_user(db, req)

@router.patch(
    "/users/{user_id}/status",
    response_model=TaiKhoanResponse,
    summary="[Admin] Khóa hoặc Mở khóa tài khoản",
    description="Thay đổi trạng thái tài khoản: ACTIVE (Hoạt động) hoặc LOCKED (Khóa).",
)
def change_user_status(
    user_id: int,
    body: UserStatusUpdate,
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService.change_user_status(db, user_id, body.trang_thai)

@router.get(
    "/users/{user_id}",
    response_model=TaiKhoanResponse,
    summary="[Admin] Tìm kiếm chi tiết 1 người dùng theo ID",
    description="Tra cứu thông tin tài khoản và hồ sơ người dùng dựa vào id_tai_khoan.",
)
def get_user_by_id_admin(
    user_id: int,
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService.get_me(db, user_id)

@router.delete(
    "/users/{user_id}",
    response_model=UserActionResponse,
    summary="[Admin] Xóa tài khoản người dùng",
    description="Chỉ dành cho Quản trị viên (Admin). Xóa vĩnh viễn tài khoản người dùng và toàn bộ hồ sơ liên quan.",
)
def delete_user_admin(
    user_id: int,
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService.delete_user_admin(
        db=db,
        user_id=user_id,
        current_admin_id=admin_user.id_tai_khoan,
    )


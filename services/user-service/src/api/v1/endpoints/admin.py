from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models import TaiKhoanModel, VaiTroEnum, TrangThaiTaiKhoanEnum
from src.schemas.user_schema import TaiKhoanResponse, UserStatusUpdate, UserPaginatedResponse
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
    status: Optional[TrangThaiTaiKhoanEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, LOCKED, INACTIVE)"),
    keyword: Optional[str] = Query(None, description="Tìm theo tên đăng nhập, email, họ tên, SĐT"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    admin_user: TaiKhoanModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService.get_users_admin(
        db=db,
        role=role,
        status_val=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.security import decode_token
from src.models import TaiKhoanModel, VaiTroEnum, TrangThaiTaiKhoanEnum

security_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT Bearer Token (format: `Bearer <token>`)",
    auto_error=False,
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> TaiKhoanModel:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập: Vui lòng cung cấp Bearer token trong header Authorization.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không phải là access token hợp lệ.",
            )
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(TaiKhoanModel).filter(TaiKhoanModel.id_tai_khoan == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại.",
        )

    if user.trang_thai == TrangThaiTaiKhoanEnum.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa. Vui lòng liên hệ Quản trị viên.",
        )

    if user.trang_thai == TrangThaiTaiKhoanEnum.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt hoặc đã ngừng hoạt động.",
        )

    return user

def require_admin(
    current_user: TaiKhoanModel = Depends(get_current_user),
) -> TaiKhoanModel:
    if current_user.vai_tro != VaiTroEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quyền truy cập bị từ chối: Thao tác này chỉ dành riêng cho Quản Trị Viên (Admin).",
        )
    return current_user

def require_partner_or_admin(
    current_user: TaiKhoanModel = Depends(get_current_user),
) -> TaiKhoanModel:
    if current_user.vai_tro not in [VaiTroEnum.PARTNER, VaiTroEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quyền truy cập bị từ chối: Chỉ Partner hoặc Admin mới có quyền thực hiện.",
        )
    return current_user

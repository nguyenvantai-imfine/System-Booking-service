"""
dependencies.py - Các dependency dùng chung cho toàn bộ API Hotel Service.
Bao gồm: Xác thực JWT token từ Auth / User Service, phân quyền Partner/Admin, cung cấp DB session.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from src.core.database import get_db
from src.core.security import decode_token

# ─────────────────────────────────────────────
# Bảo mật: Lược đồ Bearer Token
# ─────────────────────────────────────────────
security_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT Bearer token từ User Service (format: `Bearer <token>`)",
    auto_error=False,
)


def get_current_partner_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> int:
    """
    Dependency: Xác thực JWT Bearer Token, trích xuất partner_id (sub) và kiểm tra
    vai trò người dùng (phải là PARTNER hoặc ADMIN).

    Hỗ trợ fallback chế độ demo nếu token là chuỗi số nguyên ID.

    Raises:
        401 UNAUTHORIZED: Chưa đăng nhập hoặc token hết hạn / không hợp lệ.
        403 FORBIDDEN: Tài khoản không có vai trò PARTNER hoặc ADMIN.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu xác thực: Vui lòng cung cấp Bearer token trong header Authorization.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()

    # 1. Thử giải mã JWT thật từ user-service
    try:
        payload = decode_token(token)
        
        # Kiểm tra loại token nếu có
        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Loại token không hợp lệ (yêu cầu access token).",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Trích xuất partner_id từ subject
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không chứa thông tin định danh người dùng.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        partner_id = int(sub)

        # Xác thực quyền hạn: role phải là PARTNER hoặc ADMIN
        role = str(payload.get("role", "")).upper()
        if role not in ["PARTNER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ tài khoản Đối tác (Partner) hoặc Quản trị viên (Admin) mới có quyền thực hiện thao tác này.",
            )

        return partner_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        # 2. Fallback chế độ demo cũ nếu token là số id trực tiếp
        try:
            demo_id = int(token)
            if demo_id > 0:
                return demo_id
        except (ValueError, TypeError):
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Định dạng định danh người dùng trong token không hợp lệ.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─────────────────────────────────────────────
# Re-export tiện ích: DB Session
# ─────────────────────────────────────────────
__all__ = [
    "get_db",
    "get_current_partner_id",
]

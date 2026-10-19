"""
dependencies.py - Các dependency dùng chung cho toàn bộ API.
Bao gồm: Giả lập xác thực JWT Partner, cung cấp DB session.
"""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.core.database import get_db

# ─────────────────────────────────────────────
# Bảo mật: Lược đồ Bearer Token
# ─────────────────────────────────────────────
security_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT Bearer token từ Auth Service (format: `Bearer <token>`)",
    auto_error=False,   # Cho phép xử lý thủ công để cung cấp thông báo lỗi rõ ràng hơn
)


def get_current_partner_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> int:
    """
    Dependency: Giả lập / xác thực JWT để lấy id_tai_khoan của Partner hiện tại.

    ── Chế độ DEMO ────────────────────────────────────────────────────────────
    Trong giai đoạn phát triển, token được hiểu là chính số id_tai_khoan
    (ví dụ: token = "1" → partner_id = 1).
    Khi tích hợp Auth Service thật, thay phần decode bằng logic verify JWT.
    ────────────────────────────────────────────────────────────────────────────

    Raises:
        401 UNAUTHORIZED - Không có token hoặc token không hợp lệ
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu xác thực: Vui lòng cung cấp Bearer token trong header Authorization.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # ── Thay thế khối này bằng logic decode JWT thật khi có Auth Service ──
    try:
        partner_id = int(token)   # DEMO: token = str(id_tai_khoan)
        if partner_id <= 0:
            raise ValueError("ID không hợp lệ")
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # ─────────────────────────────────────────────────────────────────────────

    return partner_id


# ─────────────────────────────────────────────
# Re-export tiện ích: DB Session
# ─────────────────────────────────────────────
__all__ = [
    "get_db",
    "get_current_partner_id",
]

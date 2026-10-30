from typing import Optional
import secrets

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.core.database import get_db
from src.core.security import decode_token


security_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT Bearer token từ User Service (format: Bearer <token>)",
    auto_error=False,
)


# =========================================================
# HÀM HỖ TRỢ
# =========================================================

INTERNAL_SECRET_PLACEHOLDERS = {
    "booking_internal_secret_key_2026",
    "replace_with_a_long_random_secret",
}


def unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def is_valid_internal_secret(supplied_secret: Optional[str]) -> bool:
    expected_secret = str(
        settings.INTERNAL_SERVICE_SECRET or ""
    ).strip()

    supplied_secret = str(
        supplied_secret or ""
    ).strip()

    if not expected_secret or not supplied_secret:
        return False

    if (
        expected_secret in INTERNAL_SECRET_PLACEHOLDERS
        or supplied_secret in INTERNAL_SECRET_PLACEHOLDERS
    ):
        return False

    return secrets.compare_digest(
        supplied_secret,
        expected_secret,
    )


# =========================================================
# 1. XÁC THỰC JWT
# =========================================================

def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security_scheme
    ),
) -> dict:
    """
    Xác thực access token JWT và trả về payload.
    """

    if credentials is None or not credentials.credentials:
        raise unauthorized(
            "Yêu cầu đăng nhập: Vui lòng cung cấp Bearer token."
        )

    token = credentials.credentials.strip()

    if not token:
        raise unauthorized("Token xác thực không được để trống.")

    try:
        payload = decode_token(token)

        if not isinstance(payload, dict):
            raise unauthorized("Payload token không hợp lệ.")

        # Nếu User Service có trường type thì phải là access.
        # Tạm thời vẫn chấp nhận token không có trường type
        # để tương thích với JWT hiện tại của hệ thống.
        token_type = payload.get("type")

        if token_type is not None and token_type != "access":
            raise unauthorized(
                "Loại token không hợp lệ. Yêu cầu access token."
            )

        subject = payload.get("sub")

        if subject is None or not str(subject).strip():
            raise unauthorized(
                "Token không chứa thông tin định danh người dùng."
            )

        return payload

    except jwt.ExpiredSignatureError as exc:
        raise unauthorized(
            "Token đã hết hạn. Vui lòng đăng nhập lại."
        ) from exc

    except HTTPException:
        raise

    except jwt.PyJWTError as exc:
        raise unauthorized(
            "Token không hợp lệ hoặc đã hết hạn."
        ) from exc

    except (ValueError, TypeError) as exc:
        raise unauthorized(
            "Định dạng token không hợp lệ."
        ) from exc


# =========================================================
# 2. XÁC THỰC SERVICE NỘI BỘ
# =========================================================

def require_internal_service(
    x_internal_service_secret: Optional[str] = Header(
        default=None,
        alias="X-Internal-Service-Secret",
    ),
) -> None:
    """
    Chỉ cho phép request có internal secret hợp lệ.
    """

    if not is_valid_internal_secret(x_internal_service_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dịch vụ nội bộ chưa được xác thực.",
        )


# =========================================================
# 3. CHO PHÉP USER HOẶC SERVICE NỘI BỘ
# =========================================================

def get_current_user_or_internal_service(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security_scheme
    ),
    x_internal_service_secret: Optional[str] = Header(
        default=None,
        alias="X-Internal-Service-Secret",
    ),
) -> dict:
    """
    Cho phép JWT hợp lệ hoặc service nội bộ đã xác thực.
    """

    if is_valid_internal_secret(x_internal_service_secret):
        return {
            "sub": "0",
            "role": "SERVICE",
        }

    return get_current_user_payload(credentials)


# =========================================================
# 4. CHỈ CHO PHÉP ADMIN
# =========================================================

def require_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    """
    Chỉ cho phép tài khoản ADMIN thực hiện thao tác quản trị.
    """

    role = str(payload.get("role", "")).upper()

    if role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị viên (Admin) mới có quyền thực hiện thao tác này.",
        )

    return payload


__all__ = [
    "get_db",
    "get_current_user_payload",
    "get_current_user_or_internal_service",
    "require_admin",
    "require_internal_service",
]
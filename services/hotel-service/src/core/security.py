"""
security.py - Xử lý giải mã và xác thực JWT cho hotel-service.
Đồng bộ cấu hình bí mật và thuật toán mã hóa với user-service.
"""
from typing import Dict, Any
import jwt
from src.core.config import settings

def _candidate_jwt_secrets() -> list[str]:
    configured = settings.JWT_SECRET_KEY.strip()
    return [configured] if configured else []


def decode_token(token: str) -> Dict[str, Any]:
    """
    Giải mã và xác thực chữ ký JWT bằng Secret Key và Algorithm dùng chung.
    Raises:
        jwt.ExpiredSignatureError: Token đã hết hạn.
        jwt.PyJWTError: Token không hợp lệ.
    """
    last_exc: Exception | None = None
    for secret in _candidate_jwt_secrets():
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.PyJWTError as exc:
            last_exc = exc
    raise last_exc or jwt.InvalidTokenError("Token không hợp lệ")

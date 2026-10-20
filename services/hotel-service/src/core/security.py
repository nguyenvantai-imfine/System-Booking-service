"""
security.py - Xử lý giải mã và xác thực JWT cho hotel-service.
Đồng bộ cấu hình bí mật và thuật toán mã hóa với user-service.
"""
from typing import Dict, Any
import jwt
from src.core.config import settings

def decode_token(token: str) -> Dict[str, Any]:
    """
    Giải mã và xác thực chữ ký JWT bằng Secret Key và Algorithm dùng chung.
    Raises:
        jwt.ExpiredSignatureError: Token đã hết hạn.
        jwt.PyJWTError: Token không hợp lệ.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

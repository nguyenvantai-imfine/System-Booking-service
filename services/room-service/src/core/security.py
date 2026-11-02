from typing import Dict, Any
import jwt
from fastapi import HTTPException, status
from src.core.config import settings

def decode_token(token: str) -> Dict[str, Any]:
    """Giải mã và xác thực chữ ký JWT bằng Secret Key và Algorithm dùng chung."""
    if not settings.JWT_SECRET_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Xác thực chưa được cấu hình.",
        )
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

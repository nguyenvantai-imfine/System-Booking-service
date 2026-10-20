from typing import Dict, Any
import jwt
from src.core.config import settings

def decode_token(token: str) -> Dict[str, Any]:
    """Giải mã và xác thực chữ ký JWT bằng Secret Key và Algorithm dùng chung."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

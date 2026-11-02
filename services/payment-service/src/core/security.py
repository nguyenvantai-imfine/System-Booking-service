from typing import Dict, Any
import jwt
from src.core.config import settings

def decode_token(token: str) -> Dict[str, Any]:
    if not settings.JWT_SECRET_KEY.strip():
        raise ValueError("JWT_SECRET_KEY is not configured.")
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

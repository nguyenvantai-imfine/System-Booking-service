from typing import Dict, Any
import jwt
from fastapi import HTTPException, status
from src.core.config import settings

def _candidate_jwt_secrets() -> list[str]:
    configured = settings.JWT_SECRET_KEY.strip()
    return [configured] if configured else []


def decode_token(token: str) -> Dict[str, Any]:
    """Giải mã và xác thực chữ ký JWT bằng Secret Key và Algorithm dùng chung."""
    secrets = _candidate_jwt_secrets()
    if not secrets:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Xác thực chưa được cấu hình.",
        )

    last_exc: Exception | None = None
    for secret in secrets:
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.PyJWTError as exc:
            last_exc = exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token xác thực không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    ) from last_exc

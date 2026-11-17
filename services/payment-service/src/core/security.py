from typing import Dict, Any
import jwt
from src.core.config import settings

def _candidate_jwt_secrets() -> list[str]:
    configured = settings.JWT_SECRET_KEY.strip()
    return [configured] if configured else []


def decode_token(token: str) -> Dict[str, Any]:
    secrets = _candidate_jwt_secrets()
    if not secrets:
        raise ValueError("JWT_SECRET_KEY is not configured.")

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

    raise ValueError("JWT token is invalid or expired.") from last_exc


from typing import Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError

from src.core.config import settings

def _candidate_jwt_secrets() -> list[str]:
    configured = settings.JWT_SECRET_KEY.strip()
    return [configured] if configured else []


def decode_token(token: str) -> Dict[str, Any]:
    if not token or not token.strip():
        raise ValueError("Token khong duoc de trong.")

    secrets = _candidate_jwt_secrets()
    if not secrets:
        raise ValueError("JWT_SECRET_KEY chua duoc cau hinh.")

    last_exception: Exception | None = None
    for secret in secrets:
        try:
            payload = jwt.decode(
                token.strip(),
                secret,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if not isinstance(payload, dict):
                raise ValueError("Token payload khong hop le.")
            return payload
        except InvalidTokenError as exc:
            last_exception = exc
        except ValueError:
            raise

    raise ValueError("Token khong hop le hoac da het han.") from last_exception

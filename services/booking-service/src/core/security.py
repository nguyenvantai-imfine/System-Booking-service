
from typing import Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError

from src.core.config import settings


def decode_token(token: str) -> Dict[str, Any]:
    if not token or not token.strip():
        raise ValueError("Token khong duoc de trong.")

    try:
        payload = jwt.decode(
            token.strip(),
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if not isinstance(payload, dict):
            raise ValueError("Token payload khong hop le.")

        return payload

    except InvalidTokenError as exc:
        raise ValueError("Token khong hop le hoac da het han.") from exc

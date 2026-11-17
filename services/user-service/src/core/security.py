from datetime import datetime, timedelta
from typing import Optional, Any
import jwt
import bcrypt
from src.core.config import settings

def _configured_jwt_secret() -> str:
    configured = settings.JWT_SECRET_KEY.strip()
    if configured:
        return configured
    raise RuntimeError("JWT_SECRET_KEY is not configured.")

def hash_password(password: str) -> str:
    """
    Băm mật khẩu bằng Bcrypt với cost factor (rounds) = 12.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Accept bcrypt hashes only; migrate legacy passwords explicitly."""
    if not hashed_password or not hashed_password.startswith("$2"):
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Tạo JWT Access Token (hết hạn 60 phút)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, _configured_jwt_secret(), algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Tạo JWT Refresh Token (hết hạn 7 ngày)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, _configured_jwt_secret(), algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Giải mã và xác thực chữ ký JWT."""
    return jwt.decode(token, _configured_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])

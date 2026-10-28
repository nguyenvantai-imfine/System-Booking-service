from datetime import datetime, timedelta
from typing import Optional, Any
import jwt
import bcrypt
from src.core.config import settings

def hash_password(password: str) -> str:
    """
    Băm mật khẩu bằng Bcrypt với cost factor (rounds) = 12.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu:
    - Nếu hashed_password bắt đầu bằng '$2', dùng bcrypt.checkpw(...)
    - Fallback: so sánh trực tiếp plain_password == hashed_password
      chỉ để tương thích với các tài khoản seed cũ chưa được cập nhật hash bcrypt.
    """
    if not hashed_password:
        return False

    try:
        if hashed_password.startswith("$2"):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
    except Exception:
        return False

    # Fallback so sánh trực tiếp cho tài khoản seed cũ chưa mã hóa
    return plain_password == hashed_password

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
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
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
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Giải mã và xác thực chữ ký JWT."""
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )

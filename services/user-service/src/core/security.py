from datetime import datetime, timedelta
from typing import Optional, Any
import jwt
import bcrypt
from src.core.config import settings

def hash_password(password: str) -> str:
    """
    Tạm thời bỏ mã hóa mật khẩu, lưu dạng plain text (Mở lại bcrypt sau này).
    """
    # [TODO: Mở lại bcrypt sau]
    # salt = bcrypt.gensalt(rounds=12)
    # return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu:
    - So sánh trực tiếp plain text: plain_password == hashed_password
    - Vẫn hỗ trợ fallback nếu chuỗi trong DB còn lưu hash bcrypt cũ
    """
    # 1. So sánh trực tiếp chuỗi mật khẩu (plain text)
    if plain_password == hashed_password:
        return True

    # 2. [TODO: Mở lại bcrypt sau]
    # try:
    #     return bcrypt.checkpw(
    #         plain_password.encode("utf-8"),
    #         hashed_password.encode("utf-8"),
    #     )
    # except Exception:
    #     return False

    try:
        if hashed_password and hashed_password.startswith("$2"):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
    except Exception:
        pass

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

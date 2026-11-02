from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import json
import logging
import urllib.error
import urllib.request
from src.core.database import get_db
from src.core.security import decode_token
from src.core.config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT Bearer token từ User Service",
    auto_error=False,
)

def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui lòng đăng nhập và cung cấp Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không được để trống.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không phải là access token hợp lệ.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không chứa thông tin định danh người dùng.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_partner_or_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    role = str(payload.get("role", "")).upper()
    if role not in {"PARTNER", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản Chủ khách sạn (Partner) hoặc Quản trị viên (Admin) mới có quyền thao tác.",
        )
    return payload


def check_hotel_ownership(hotel_id: int, user: dict) -> None:
    """
    Kiểm tra quyền sở hữu khách sạn cho phòng/loại phòng:
    - Admin (role == 'ADMIN') có toàn quyền quản lý mọi khách sạn/phòng.
    - Partner (role == 'PARTNER') chỉ được sửa/xóa phòng thuộc khách sạn do mình sở hữu.
    Không cho phép Partner sửa phòng thuộc khách sạn của Partner khác (403 Forbidden).
    """
    role = str(user.get("role", "")).upper()
    if role == "ADMIN":
        return

    current_uid = None
    try:
        current_uid = int(user.get("sub"))
    except (ValueError, TypeError):
        current_uid = None

    if current_uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không xác định được danh tính người dùng từ token.",
        )

    # 1. Kiểm tra nếu token có gắn claim id_khach_san / hotel_id
    token_hotel_id = user.get("id_khach_san")
    if token_hotel_id is None:
        token_hotel_id = user.get("hotel_id")
    if token_hotel_id is not None:
        try:
            claim_hotel_id = int(token_hotel_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Thông tin khách sạn trong token không hợp lệ.",
            ) from exc
        if claim_hotel_id != hotel_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền sửa hoặc thao tác phòng thuộc khách sạn của đối tác khác.",
            )

    # Verify ownership with Hotel Service even when a hotel claim is present;
    # an unavailable or malformed response must never grant the operation.
    try:
        hotel_service_url = settings.HOTEL_SERVICE_URL.rstrip("/")
        if not hotel_service_url:
            raise ValueError("Hotel Service URL is not configured.")
        req = urllib.request.Request(
            f"{hotel_service_url}/hotels/{hotel_id}",
            headers={"User-Agent": "room-service", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
        if not isinstance(data, dict):
            raise ValueError("Hotel Service response must be an object.")
        owner_id = data.get("id_tai_khoan")
        if owner_id is None:
            owner_id = data.get("id_chu_so_huu")
        if isinstance(owner_id, bool):
            raise ValueError("Hotel Service returned an invalid owner ID.")
        try:
            owner_id = int(owner_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Hotel Service did not return a valid owner ID.") from exc
        if owner_id <= 0:
            raise ValueError("Hotel Service returned an invalid owner ID.")
        if owner_id != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền sửa hoặc thao tác phòng thuộc khách sạn của đối tác khác.",
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy khách sạn.",
            ) from exc
        logger.warning(
            "Could not verify hotel ownership; upstream_status=%s",
            exc.code,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác minh quyền sở hữu khách sạn lúc này.",
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "Could not verify hotel ownership; error_type=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác minh quyền sở hữu khách sạn lúc này.",
        ) from exc


__all__ = [
    "get_db",
    "get_current_user_payload",
    "require_partner_or_admin",
    "check_hotel_ownership",
]

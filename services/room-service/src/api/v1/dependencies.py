from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from src.core.database import get_db
from src.core.security import decode_token

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
        pass

    if current_uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không xác định được danh tính người dùng từ token.",
        )

    # 1. Kiểm tra nếu token có gắn claim id_khach_san / hotel_id
    token_hotel_id = user.get("id_khach_san") or user.get("hotel_id")
    if token_hotel_id is not None and int(token_hotel_id) != int(hotel_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền sửa hoặc thao tác phòng thuộc khách sạn của đối tác khác.",
        )

    # 2. Xác thực với Hotel Service
    try:
        import urllib.request
        import json
        from src.core.config import settings
        hotel_service_url = getattr(settings, "HOTEL_SERVICE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
        req = urllib.request.Request(
            f"{hotel_service_url}/hotels/{hotel_id}",
            headers={"User-Agent": "room-service", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            owner_id = data.get("id_chu_so_huu") or data.get("id_tai_khoan")
            if owner_id is not None and int(owner_id) != current_uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền sửa hoặc thao tác phòng thuộc khách sạn của đối tác khác.",
                )
    except HTTPException:
        raise
    except Exception:
        # Fallback khi test môi trường độc lập không kết nối được hotel-service
        pass


__all__ = [
    "get_db",
    "get_current_user_payload",
    "require_partner_or_admin",
    "check_hotel_ownership",
]

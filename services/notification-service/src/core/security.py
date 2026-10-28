import hmac
import ipaddress
import logging

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from src.core.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(
    scheme_name="BearerToken",
    description="JWT access token từ User Service",
    auto_error=False,
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token xác thực không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials.strip():
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials.strip(),
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise unauthorized
        user_id = int(payload["sub"])
        if user_id <= 0:
            raise unauthorized
        return user_id
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise unauthorized from exc


def _is_trusted_internal_request(request: Request) -> bool:
    if request.client is None:
        return False

    try:
        peer_ip = ipaddress.ip_address(request.client.host)
    except ValueError:
        return False

    try:
        networks = (
            ipaddress.ip_network(cidr.strip())
            for cidr in settings.TRUSTED_INTERNAL_CIDRS.split(",")
            if cidr.strip()
        )
        return any(
            peer_ip.version == network.version and peer_ip in network
            for network in networks
        )
    except ValueError:
        logger.exception("Invalid TRUSTED_INTERNAL_CIDRS configuration.")
        return False


def get_notification_actor_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
) -> int | None:
    """Allow service-to-service send calls only from a trusted peer or with the shared secret."""
    configured_secret = settings.INTERNAL_SERVICE_SECRET.strip()
    has_valid_secret = bool(
        configured_secret
        and x_internal_secret
        and hmac.compare_digest(x_internal_secret, configured_secret)
    )

    if has_valid_secret or _is_trusted_internal_request(request):
        return None

    return get_current_user_id(credentials)

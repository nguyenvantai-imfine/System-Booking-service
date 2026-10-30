import logging
import time
import uuid

from contextvars import ContextVar
from fastapi import Request


logger = logging.getLogger(__name__)

correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id",
    default="",
)


def get_correlation_id() -> str:
    return correlation_id_ctx.get()


def set_correlation_id(cid: str) -> None:
    correlation_id_ctx.set(cid)


async def correlation_id_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    # Nhận Correlation ID từ service gọi đến.
    cid = request.headers.get("X-Correlation-ID", "").strip()

    # Nếu không có hoặc quá dài thì tạo ID mới.
    if not cid or len(cid) > 128:
        cid = str(uuid.uuid4())

    token = correlation_id_ctx.set(cid)
    request.state.correlation_id = cid

    try:
        response = await call_next(request)

        response.headers["X-Correlation-ID"] = cid

        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.info(
            "[CORRELATION_ID: %s] %s %s -> %s (%.2fms)",
            cid,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response

    except Exception:
        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "[CORRELATION_ID: %s] %s %s failed (%.2fms)",
            cid,
            request.method,
            request.url.path,
            elapsed_ms,
        )

        raise

    finally:
        correlation_id_ctx.reset(token)
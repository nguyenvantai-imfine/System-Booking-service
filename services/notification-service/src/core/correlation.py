import time
import uuid
from contextvars import ContextVar
from fastapi import Request

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    return correlation_id_ctx.get()

def set_correlation_id(cid: str) -> None:
    correlation_id_ctx.set(cid)

async def correlation_id_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    cid = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
    if not cid:
        cid = str(uuid.uuid4())
    token = correlation_id_ctx.set(cid)
    request.state.correlation_id = cid
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"[CORRELATION_ID: {cid}] {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.2f}ms)")
        return response
    finally:
        correlation_id_ctx.reset(token)

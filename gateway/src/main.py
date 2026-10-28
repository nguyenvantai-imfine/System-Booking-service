import os
import sys
import re
from contextlib import asynccontextmanager
from typing import Dict
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.core.config import settings, GatewaySettings

# HTTP Client dùng chung cho toàn bộ Gateway proxy
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    print(f">>> [API GATEWAY] Ready on port {settings.PORT}!")
    print(f"    - Hotel Service:        {settings.HOTEL_SERVICE_URL}")
    print(f"    - User Service:         {settings.USER_SERVICE_URL}")
    print(f"    - Room Service:         {settings.ROOM_SERVICE_URL}")
    print(f"    - Booking Service:      {settings.BOOKING_SERVICE_URL}")
    print(f"    - Payment Service:      {settings.PAYMENT_SERVICE_URL}")
    print(f"    - Notification Service: {settings.NOTIFICATION_SERVICE_URL}")
    yield
    await http_client.aclose()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Cổng API Gateway tập trung cho Hệ thống Đặt phòng Khách sạn",
    lifespan=lifespan,
)

import time
import uuid

# Cấu hình CORS Header tập trung
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*", "X-Correlation-ID"],
)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    cid = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
    if not cid:
        cid = str(uuid.uuid4())
    request.state.correlation_id = cid

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    print(f"[CORRELATION_ID: {cid}] {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.2f}ms)")
    return response

# Bản đồ định tuyến theo tiền tố URL
def resolve_target_url(full_path: str) -> str:
    path = full_path.lstrip("/")
    parts = path.split("/")

    # path dạng: api/v1/<service>/...
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
        # 1. Các route thuộc Room Service:
        #    - api/v1/room-types/...
        #    - api/v1/hotels/{hotel_id}/rooms hoặc api/v1/hotels/{hotel_id}/room-types
        if parts[2].lower() == "room-types":
            return f"{settings.ROOM_SERVICE_URL}/{path}"

        if re.match(r"^api/v1/hotels/\d+/(rooms|room-types)", path, re.IGNORECASE):
            return f"{settings.ROOM_SERVICE_URL}/{path}"

        service = parts[2].lower()
        if service in ("auth", "users", "profiles", "admin"):
            return f"{settings.USER_SERVICE_URL}/{path}"
        elif service == "hotels":
            return f"{settings.HOTEL_SERVICE_URL}/{path}"
        elif service == "rooms":
            return f"{settings.ROOM_SERVICE_URL}/{path}"
        elif service == "bookings":
            return f"{settings.BOOKING_SERVICE_URL}/{path}"
        elif service == "payments":
            return f"{settings.PAYMENT_SERVICE_URL}/{path}"
        elif service == "notifications":
            return f"{settings.NOTIFICATION_SERVICE_URL}/{path}"

    return None

HOP_BY_HOP_HEADERS = {
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade"
}

@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_api_v1(request: Request, path: str):
    """Định tuyến ngược động tất cả các request /api/v1/** về đúng microservice đích"""
    full_path = f"/api/v1/{path}"
    target_base = resolve_target_url(full_path)

    if not target_base:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"API Gateway: Tuyến đường không hợp lệ '{full_path}'"},
        )

    # Thêm query parameters nếu có
    query_str = request.url.query
    target_url = f"{target_base}?{query_str}" if query_str else target_base

    cid = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    # Lọc header và đảm bảo chuyển tiếp đầy đủ X-Correlation-ID, Authorization, X-Idempotency-Key...
    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }
    forward_headers["X-Correlation-ID"] = cid

    body = await request.body()

    try:
        resp = await http_client.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            content=body,
        )

        response_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        }
        response_headers["X-Correlation-ID"] = cid

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type"),
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"API Gateway: Không thể kết nối tới dịch vụ đích tại {target_url}"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"API Gateway Proxy Error: {str(e)}"},
        )

@app.get("/", tags=["Gateway"])
def gateway_info():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "port": settings.PORT,
        "description": "Cổng API Gateway duy nhất cho toàn bộ hệ thống đặt phòng khách sạn",
        "routes": {
            "/api/v1/auth/**": settings.USER_SERVICE_URL,
            "/api/v1/users/**": settings.USER_SERVICE_URL,
            "/api/v1/admin/**": settings.USER_SERVICE_URL,
            "/api/v1/hotels/**": settings.HOTEL_SERVICE_URL,
            "/api/v1/hotels/{hotel_id}/rooms/**": settings.ROOM_SERVICE_URL,
            "/api/v1/hotels/{hotel_id}/room-types/**": settings.ROOM_SERVICE_URL,
            "/api/v1/rooms/**": settings.ROOM_SERVICE_URL,
            "/api/v1/room-types/**": settings.ROOM_SERVICE_URL,
            "/api/v1/bookings/**": settings.BOOKING_SERVICE_URL,
            "/api/v1/payments/**": settings.PAYMENT_SERVICE_URL,
            "/api/v1/notifications/**": settings.NOTIFICATION_SERVICE_URL,
        },
    }

@app.get("/health", tags=["Gateway"])
async def gateway_health():
    services = {
        "hotel-service": settings.HOTEL_SERVICE_URL,
        "user-service": settings.USER_SERVICE_URL,
        "room-service": settings.ROOM_SERVICE_URL,
        "booking-service": settings.BOOKING_SERVICE_URL,
        "payment-service": settings.PAYMENT_SERVICE_URL,
        "notification-service": settings.NOTIFICATION_SERVICE_URL,
    }

    health_report = {}
    for name, base_url in services.items():
        try:
            r = await http_client.get(f"{base_url}/health", timeout=2.0)
            if r.status_code == 200:
                health_report[name] = "UP"
            else:
                r2 = await http_client.get(f"{base_url}/", timeout=2.0)
                health_report[name] = "UP" if r2.status_code == 200 else f"STATUS_{r.status_code}"
        except Exception:
            health_report[name] = "DOWN"

    return {
        "gateway": "UP",
        "services": health_report,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)

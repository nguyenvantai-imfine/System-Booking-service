import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.payment_service import PaymentService
from src.api.v1.router import api_router
import src.models

def verify_payment_schema(connection) -> None:
    inspector = inspect(connection)
    if not set(Base.metadata.tables).issubset(inspector.get_table_names()):
        raise RuntimeError("Payment schema missing; initialize the isolated database first.")
    otp_column = next(c for c in inspector.get_columns("giao_dich_otp") if c["name"] == "otp_code")
    length = getattr(otp_column["type"], "length", None)
    if length is not None and length < 64:
        raise RuntimeError("Apply payment migration 20261117_otp_hash_width.sql before startup.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        verify_payment_schema(connection)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 💳 Payment Service API\n\n"
        "Microservice xử lý thanh toán đa kênh (VNPAY, MoMo, Thẻ tín dụng) và mô phỏng Sandbox IPN Callback.\n\n"
        "### Các tính năng chính:\n"
        "- Khởi tạo giao dịch thanh toán đơn đặt phòng.\n"
        "- Sinh mã OTP và xác thực thanh toán bảo mật 2 lớp.\n"
        "- Mô phỏng Sandbox checkout và IPN Callback.\n"
        "- Tự động gửi webhook chuyển trạng thái đơn sang CONFIRMED khi thanh toán thành công.\n"
        "- Thống kê tổng doanh thu và lịch sử giao dịch.\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*", "X-Correlation-ID"],
)

from src.core.correlation import correlation_id_middleware
app.middleware("http")(correlation_id_middleware)

# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database operation failed.",
            "type": "DatabaseError",
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error.",
            "type": "InternalServerError",
        },
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"], summary="Health Check")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "port": settings.PORT,
    }


@app.get("/health", tags=["Health"])
def health():
    from sqlalchemy import text
    from src.core.database import engine as health_engine
    try:
        with health_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database_connected": True}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "database_connected": False})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=settings.PORT, reload=True)

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
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.payment_service import PaymentService
from src.api.v1.router import api_router
import src.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng dữ liệu
    try:
        Base.metadata.create_all(bind=engine)
        print(">>> [Payment Service] Database tables verified.")
        db = SessionLocal()
        try:
            PaymentService.seed_default_payments(db)
        finally:
            db.close()
    except Exception as e:
        print(">>> [Payment Service] Startup warning:", str(e))
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 💳 Payment Service API\n\n"
        "Microservice xử lý thanh toán đa kênh (VNPAY, MoMo, Thẻ tín dụng) và mô phỏng Sandbox IPN Callback.\n\n"
        "### Các tính năng chính:\n"
        "- Khởi tạo giao dịch thanh toán đơn đặt phòng.\n"
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Lỗi cơ sở dữ liệu: {str(exc)}",
            "type": "DatabaseError",
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Lỗi hệ thống: {str(exc)}",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=settings.PORT, reload=True)

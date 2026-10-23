import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.booking_service import BookingService
from src.api.v1.router import api_router
import src.models

async def expired_holds_background_cleaner():
    """Chạy nền định kỳ mỗi 60 giây để quét và hủy các đơn quá hạn giữ chỗ 15 phút."""
    while True:
        try:
            await asyncio.sleep(60)
            db = SessionLocal()
            try:
                BookingService.release_expired_holds(db)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(">>> [Booking Service] Expired holds cleaner error:", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleaner_task = None
    try:
        Base.metadata.create_all(bind=engine)
        print(">>> [Booking Service] Database tables verified.")
        db = SessionLocal()
        try:
            BookingService.seed_default_bookings(db)
            BookingService.release_expired_holds(db)
        finally:
            db.close()
        cleaner_task = asyncio.create_task(expired_holds_background_cleaner())
    except Exception as e:
        print(">>> [Booking Service] Startup warning:", str(e))
    yield
    if cleaner_task:
        cleaner_task.cancel()
        try:
            await cleaner_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 📋 Booking Service API\n\n"
        "Microservice quản lý Đơn đặt phòng & Chống trùng phòng (Overbooking Protection) trong kiến trúc SOA.\n\n"
        "### Các tính năng chính:\n"
        "- Tạo đơn đặt phòng, kiểm tra lịch trống chính xác tuyệt đối.\n"
        "- Khóa giữ chỗ tạm thời trong 15 phút (Hold Lock).\n"
        "- Tự động hủy đơn và giải phóng phòng nếu sau 15 phút chưa thanh toán.\n"
        "- Xác nhận đơn sau khi nhận callback từ Payment Service.\n"
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

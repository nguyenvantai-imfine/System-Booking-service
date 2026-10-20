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
from src.services.room_service import RoomService
from src.api.v1.router import api_router
import src.models  # Nạp toàn bộ models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng dữ liệu nếu chưa có
    try:
        Base.metadata.create_all(bind=engine)
        print(">>> [Room Service] Database tables verified.")
        # Khởi tạo dữ liệu mẫu nếu bảng trống
        db = SessionLocal()
        try:
            RoomService.seed_default_data(db)
        finally:
            db.close()
    except Exception as e:
        print(">>> [Room Service] Startup warning:", str(e))
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 🚪 Room Service API\n\n"
        "Microservice quản lý Hạng phòng & Kho phòng vật lý trong kiến trúc đặt phòng SOA.\n\n"
        "### Các tính năng chính:\n"
        "- Quản lý Loại phòng (Hạng phòng, giá, sức chứa, tiện ích, quy tắc, khuyến mãi).\n"
        "- Quản lý Phòng vật lý (Tạo lẻ, tạo hàng loạt theo dải số phòng, đổi trạng thái).\n"
        "- Tìm kiếm phòng khả dụng (available) theo khoảng ngày nhận/trả phòng.\n"
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

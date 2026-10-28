import sys
import os

# Đảm bảo thư mục gốc của hotel-service luôn nằm trong sys.path khi chạy trực tiếp
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.api.v1.router import api_router

# ─────────────────────────────────────────────────────────────────────────────
# Khởi tạo ứng dụng FastAPI với metadata Swagger
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 🏨 Hotel Service API\n\n"
        "Microservice quản lý khách sạn trong hệ thống đặt phòng SOA.\n\n"
        "### Xác thực\n"
        "Các endpoint yêu cầu xác thực sử dụng **Bearer Token** trong header:\n"
        "```\nAuthorization: Bearer <partner_id>\n```\n"
        "> **DEMO MODE**: Token = `id_tai_khoan` (số nguyên). "
        "Ví dụ: Token `1` = Partner có ID = 1.\n\n"
        "### Nhóm API\n"
        "| Nhóm | Prefix | Mô tả |\n"
        "|------|--------|-------|\n"
        "| Khách sạn | `/api/v1/hotels` | CRUD, Soft Delete, Restore |\n"
        "| Hình ảnh | `/api/v1/hotels/{id}/images` | Thêm, đặt ảnh chính, xóa |\n"
        "| Tiện nghi | `/api/v1/hotels/{id}/amenities` | Danh mục & chi tiết |\n"
        "| Chính sách | `/api/v1/hotels/{id}/policies` | Quy tắc & chính sách |\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "🏨 Quản lý Khách Sạn", "description": "Tạo, tìm kiếm, cập nhật, xóa mềm & khôi phục khách sạn."},
        {"name": "🖼️ Hình Ảnh Khách Sạn", "description": "Quản lý hình ảnh: thêm batch, đặt ảnh đại diện, xóa."},
        {"name": "🛎️ Tiện Nghi Khách Sạn", "description": "Quản lý danh mục & chi tiết tiện nghi."},
        {"name": "📋 Chính Sách Khách Sạn", "description": "Quản lý các chính sách: check-in/out, hủy phòng, trẻ em, đặt cọc..."},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware CORS
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# Global Exception Handlers – xử lý lỗi tập trung
# ─────────────────────────────────────────────────────────────────────────────
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Bắt mọi lỗi SQLAlchemy chưa được xử lý bởi service layer."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Lỗi cơ sở dữ liệu không xác định. Vui lòng thử lại sau.",
            "type": "DatabaseError",
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Bắt mọi exception chưa được xử lý."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Lỗi hệ thống không xác định: {str(exc)}",
            "type": "InternalServerError",
        },
    )

# ─────────────────────────────────────────────────────────────────────────────
# Tích hợp Router v1
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)

# ─────────────────────────────────────────────────────────────────────────────
# Health Check endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"], summary="Health Check")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
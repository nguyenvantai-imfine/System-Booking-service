import sys
import os

# Đảm bảo thư mục gốc của hotel-service luôn nằm trong sys.path khi chạy trực tiếp
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from fastapi import FastAPI
from src.core.config import settings
from src.api.v1.router import api_router

# Khởi tạo ứng dụng FastAPI với thông tin từ config
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",  # Giao diện Swagger UI để test API
    redoc_url="/redoc" # Giao diện ReDoc thay thế
)

# Tích hợp toàn bộ router của phiên bản v1 vào ứng dụng kèm tiền tố (ví dụ: /api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Endpoint gốc kiểm tra trạng thái server
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Hotel Service API (FastAPI & SQL Server)",
        "docs": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
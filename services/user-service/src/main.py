import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.user_service import UserService
from src.api.v1.router import api_router
import src.models  # Nạp toàn bộ models để Base.metadata nạp đủ schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        inspector = inspect(connection)
        for table in Base.metadata.sorted_tables:
            columns = {column["name"] for column in inspector.get_columns(table.name)}
            if not set(table.columns.keys()).issubset(columns):
                raise RuntimeError("User schema is outdated; apply the documented migrations before startup.")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## 👤 User Service & Auth API\n\n"
        "Microservice quản lý Tài Khoan & Người Dùng trong hệ thống đặt phòng SOA.\n\n"
        "### 3 Vai trò người dùng:\n"
        "- **ADMIN**: Toàn quyền quản trị hệ thống, xem và khóa tài khoản.\n"
        "- **PARTNER**: Đối tác chủ khách sạn, tạo và quản lý khách sạn / phòng.\n"
        "- **CUSTOMER**: Khách hàng đặt phòng.\n\n"
        "### Tài khoản mặc định:\n"
        "- Admin: `admin@hotel.com` / `123456`\n"
        "- Partner: `partner@hotel.com` / `123456`\n"
        "- Customer: `customer@gmail.com` / `123456`\n"
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

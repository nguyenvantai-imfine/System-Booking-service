import os
import sys
import logging

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
from src.core.database import engine, Base
from src.api.v1.router import api_router
import src.models

logger = logging.getLogger(__name__)


def verify_room_schema(connection) -> None:
    expected_tables = set(Base.metadata.tables)
    existing_tables = set(inspect(connection).get_table_names())
    missing_tables = expected_tables - existing_tables
    if missing_tables:
        raise RuntimeError(
            "Room database is missing required tables: "
            f"{', '.join(sorted(missing_tables))}. Run the Room database "
            "initialization script; service startup does not create schema."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            verify_room_schema(connection)
    except SQLAlchemyError as exc:
        logger.error(
            "Room Service database readiness check failed; error_type=%s",
            type(exc).__name__,
        )
        raise
    logger.info("Room Service database connection verified.")
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
    logger.exception("Unhandled SQLAlchemy error while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Đã xảy ra lỗi khi truy cập cơ sở dữ liệu.",
            "type": "DatabaseError",
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
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

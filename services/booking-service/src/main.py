
import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.booking_service import BookingService
from src.api.v1.router import api_router
from src.core.correlation import correlation_id_middleware

import src.models


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("booking-service")


async def expired_holds_background_cleaner():
    """Quet va giai phong cac booking het han moi 60 giay."""

    while True:
        try:
            await asyncio.sleep(60)

            db = SessionLocal()
            try:
                BookingService.release_expired_holds(db)
            finally:
                db.close()

        except asyncio.CancelledError:
            logger.info("Expired holds cleaner stopped.")
            raise

        except Exception:
            logger.exception("Expired holds cleaner error.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleaner_task = None

    try:
        # Kiem tra va tao cac bang neu chua ton tai.
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")

        # Giai phong cac booking da het han khi service khoi dong.
        db = SessionLocal()
        try:
            BookingService.release_expired_holds(db)
        finally:
            db.close()

        # Khoi dong tac vu don dep booking het han.
        cleaner_task = asyncio.create_task(
            expired_holds_background_cleaner()
        )

        logger.info("Booking Service started.")

    except Exception:
        logger.exception("Booking Service startup failed.")
        raise

    try:
        yield
    finally:
        if cleaner_task:
            cleaner_task.cancel()

            try:
                await cleaner_task
            except asyncio.CancelledError:
                pass

        logger.info("Booking Service stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "## Booking Service API\n\n"
        "Microservice quan ly don dat phong va chong trung phong.\n\n"
        "### Cac tinh nang chinh:\n"
        "- Tao don dat phong.\n"
        "- Kiem tra tinh trang phong.\n"
        "- Giu cho tam thoi trong 15 phut.\n"
        "- Tu dong huy booking het han.\n"
        "- Xac nhan booking sau callback tu Payment Service.\n"
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
    expose_headers=["X-Correlation-ID"],
)


# Correlation ID middleware
app.middleware("http")(correlation_id_middleware)


# SQLAlchemy exception handler
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.exception("Database error.")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Loi khi xu ly du lieu co so du lieu.",
            "type": "DatabaseError",
        },
    )


# General exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception("Unexpected system error.")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Da xay ra loi he thong. Vui long thu lai sau.",
            "type": "InternalServerError",
        },
    )


# API routes
app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)


# Root health check
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

    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=True,
    )

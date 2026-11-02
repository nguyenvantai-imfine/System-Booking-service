from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from src.core.config import settings
from src.api.v1.router import api_router
from src.core.database import engine
from src.core.rabbitmq_consumer import rabbitmq_consumer
from src.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)


def verify_notification_schema(connection) -> None:
    inspector = inspect(connection)
    required_tables = {"thong_bao", "noi_dung_thong_bao"}
    existing_tables = set(inspector.get_table_names())
    if not required_tables.issubset(existing_tables):
        missing_tables = ", ".join(sorted(required_tables - existing_tables))
        raise RuntimeError(
            "Notification database is missing required tables: "
            f"{missing_tables}. Initialize the database before startup."
        )

    notification_columns = {
        column["name"] for column in inspector.get_columns("thong_bao")
    }
    if not {"event_key", "is_read"}.issubset(notification_columns):
        raise RuntimeError(
            "Notification database schema is outdated; apply the documented "
            "Notification migration before startup."
        )

    event_key_index_ready = any(
        index.get("unique")
        and index.get("column_names") == ["event_key"]
        and any(
            "event_key" in str(expression).lower()
            and "is not null" in str(expression).lower()
            for key, expression in (index.get("dialect_options") or {}).items()
            if key.endswith("_where")
        )
        for index in inspector.get_indexes("thong_bao")
    )
    try:
        content_unique_ready = any(
            constraint.get("column_names") == ["id_thong_bao"]
            for constraint in inspector.get_unique_constraints(
                "noi_dung_thong_bao"
            )
        )
    except NotImplementedError:
        content_unique_ready = False

    if not content_unique_ready:
        content_unique_ready = any(
            index.get("unique")
            and index.get("column_names") == ["id_thong_bao"]
            for index in inspector.get_indexes("noi_dung_thong_bao")
        )
    if not event_key_index_ready or not content_unique_ready:
        raise RuntimeError(
            "Notification database uniqueness constraints are missing or "
            "incompatible; apply the documented Notification migration."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            verify_notification_schema(connection)
    except SQLAlchemyError:
        logger.error("Notification Service database readiness check failed.")
        raise
    except RuntimeError as exc:
        logger.error("Notification Service schema readiness check failed: %s", exc)
        raise

    logger.info("Starting RabbitMQ notification consumer.")
    rabbitmq_consumer.start(on_message_callback=NotificationService.handle_message_queue_event)
    try:
        yield
    finally:
        logger.info("Stopping RabbitMQ notification consumer.")
        rabbitmq_consumer.stop()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Microservice gửi Email và thông báo qua Message Queue (RabbitMQ)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Cấu hình CORS
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

# Include Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"], summary="Health Check")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "port": settings.PORT,
    }

@app.get("/health", tags=["Health"])
def health_check(response: Response):
    rabbitmq_connected = (
        rabbitmq_consumer.connection is not None
        and rabbitmq_consumer.connection.is_open
    )
    database_connected = False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_connected = True
    except SQLAlchemyError as exc:
        logger.warning(
            "Notification health check database failure; error_type=%s",
            type(exc).__name__,
        )

    healthy = database_connected and rabbitmq_connected
    if not healthy:
        response.status_code = 503

    return {
        "status": "healthy" if healthy else "degraded",
        "service": settings.APP_NAME,
        "database_connected": database_connected,
        "rabbitmq_enabled": settings.RABBITMQ_ENABLED,
        "rabbitmq_connected": rabbitmq_connected,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=settings.PORT, reload=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.v1.router import api_router
from src.core.rabbitmq_consumer import rabbitmq_consumer
from src.services.notification_service import NotificationService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start RabbitMQ Consumer background thread
    print(">>> [NOTIFICATION SERVICE] Starting RabbitMQ Consumer...")
    rabbitmq_consumer.start(on_message_callback=NotificationService.handle_message_queue_event)
    yield
    # Stop consumer on shutdown
    print(">>> [NOTIFICATION SERVICE] Stopping RabbitMQ Consumer...")
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
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "rabbitmq_connected": rabbitmq_consumer.connection is not None and rabbitmq_consumer.connection.is_open,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=settings.PORT, reload=True)

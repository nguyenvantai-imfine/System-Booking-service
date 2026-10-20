from fastapi import APIRouter
from src.api.v1.endpoints import notifications

api_router = APIRouter()
api_router.include_router(notifications.router)

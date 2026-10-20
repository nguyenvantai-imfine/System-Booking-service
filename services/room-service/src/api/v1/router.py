from fastapi import APIRouter
from src.api.v1.endpoints.room_types import router as room_types_router
from src.api.v1.endpoints.rooms import router as rooms_router

api_router = APIRouter()
api_router.include_router(room_types_router)
api_router.include_router(rooms_router)

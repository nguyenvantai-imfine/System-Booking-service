from fastapi import APIRouter
from src.api.v1.endpoints.hotel_router import router as hotel_router

api_router = APIRouter()

# Gắn router khách sạn vào bộ định tuyến chung của v1
api_router.include_router(hotel_router)
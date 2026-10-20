from fastapi import APIRouter
from src.api.v1.endpoints.bookings import router as bookings_router

api_router = APIRouter()
api_router.include_router(bookings_router)

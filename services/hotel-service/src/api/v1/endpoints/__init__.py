from src.api.v1.endpoints.hotels import router as hotels_router
from src.api.v1.endpoints.images import router as images_router
from src.api.v1.endpoints.amenities import router as amenities_router
from src.api.v1.endpoints.policies import router as policies_router

__all__ = [
    "hotels_router",
    "images_router",
    "amenities_router",
    "policies_router",
]

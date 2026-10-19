"""
router.py - Bộ định tuyến tổng hợp cho API v1.
Gắn kết toàn bộ 4 nhóm endpoint vào prefix /api/v1.
"""
from fastapi import APIRouter

from src.api.v1.endpoints.hotels import router as hotels_router
from src.api.v1.endpoints.images import router as images_router
from src.api.v1.endpoints.amenities import router as amenities_router
from src.api.v1.endpoints.policies import router as policies_router

api_router = APIRouter()

# ── Nhóm 1: Khách sạn (/hotels) ──────────────────────────────────────────────
api_router.include_router(hotels_router)

# ── Nhóm 2: Hình ảnh (/hotels/{hotel_id}/images) ─────────────────────────────
api_router.include_router(images_router)

# ── Nhóm 3: Tiện nghi (/hotels/{hotel_id}/amenities) ─────────────────────────
api_router.include_router(amenities_router)

# ── Nhóm 4: Chính sách (/hotels/{hotel_id}/policies) ─────────────────────────
api_router.include_router(policies_router)
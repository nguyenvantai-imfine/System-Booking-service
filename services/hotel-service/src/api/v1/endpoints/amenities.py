"""
amenities.py - Endpoints Nhóm 3: Quản lý Tiện Nghi Khách Sạn

  POST   /hotels/{hotel_id}/amenities/categories                    → Thêm danh mục tiện nghi
  POST   /hotels/{hotel_id}/amenities/categories/{cat_id}/items     → Thêm chi tiết tiện nghi vào danh mục
  DELETE /hotels/{hotel_id}/amenities/items/{item_id}               → Xóa chi tiết tiện nghi
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_partner_id, get_db
from src.schemas.hotel_schema import (
    ChiTietTienNghiCreate,
    ChiTietTienNghiResponse,
    DanhMucTienIchCreate,
    DanhMucTienIchResponse,
)
from src.services.hotel_service import AmenityService

router = APIRouter(
    prefix="/hotels/{hotel_id}/amenities",
    tags=["🛎️ Tiện Nghi Khách Sạn"],
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/{hotel_id}/amenities/categories — Thêm danh mục tiện nghi
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/categories",
    response_model=DanhMucTienIchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm danh mục tiện nghi",
    description=(
        "Tạo một danh mục tiện nghi mới cho khách sạn (ví dụ: Tiện nghi phòng, Giải trí & Thể thao). "
        "Có thể kèm danh sách chi tiết tiện nghi trong cùng request."
    ),
)
async def add_amenity_category(
    hotel_id: int,
    category_in: DanhMucTienIchCreate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await AmenityService.add_category(
        db=db,
        id_khach_san=hotel_id,
        category_in=category_in,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/{hotel_id}/amenities/categories/{cat_id}/items — Thêm chi tiết tiện nghi
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/categories/{cat_id}/items",
    response_model=ChiTietTienNghiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm chi tiết tiện nghi vào danh mục",
    description=(
        "Thêm một tiện nghi cụ thể vào danh mục đã có "
        "(ví dụ: Wifi miễn phí, Bể bơi vô cực, Phòng gym 24/7)."
    ),
)
async def add_amenity_item(
    hotel_id: int,
    cat_id: int,
    item_in: ChiTietTienNghiCreate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await AmenityService.add_item(
        db=db,
        id_khach_san=hotel_id,
        id_danh_muc=cat_id,
        item_in=item_in,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /hotels/{hotel_id}/amenities/items/{item_id} — Xóa chi tiết tiện nghi
# ──────────────────────────────────────────────────────────────────────────────
@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa chi tiết tiện nghi",
    description="Xóa một tiện nghi cụ thể khỏi danh mục. Chỉ partner sở hữu mới có quyền.",
)
async def delete_amenity_item(
    hotel_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await AmenityService.delete_item(
        db=db,
        id_khach_san=hotel_id,
        id_tien_nghi=item_id,
        partner_id=partner_id,
    )

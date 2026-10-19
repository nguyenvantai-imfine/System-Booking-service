"""
images.py - Endpoints Nhóm 2: Quản lý Hình Ảnh Khách Sạn

  POST   /hotels/{hotel_id}/images/                     → Thêm danh sách ảnh
  PUT    /hotels/{hotel_id}/images/{image_id}/primary   → Đặt làm ảnh đại diện (chỉ 1 ảnh chính)
  DELETE /hotels/{hotel_id}/images/{image_id}           → Xóa ảnh
"""
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_partner_id, get_db
from src.schemas.hotel_schema import HinhAnhCreate, HinhAnhResponse
from src.services.hotel_service import ImageService

router = APIRouter(
    prefix="/hotels/{hotel_id}/images",
    tags=["🖼️ Hình Ảnh Khách Sạn"],
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/{hotel_id}/images/ — Thêm danh sách ảnh
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=List[HinhAnhResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm danh sách ảnh cho khách sạn",
    description=(
        "Thêm một hoặc nhiều ảnh vào khách sạn. "
        "Nếu ảnh được đánh dấu `la_anh_chinh=true`, hệ thống tự động bỏ cờ ảnh chính cũ "
        "và đặt ảnh mới làm đại diện (chỉ duy nhất 1 ảnh chính tại mọi thời điểm)."
    ),
)
async def add_images(
    hotel_id: int,
    images: List[HinhAnhCreate],
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await ImageService.add_images(
        db=db,
        id_khach_san=hotel_id,
        images_in=images,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PUT /hotels/{hotel_id}/images/{image_id}/primary — Đặt ảnh đại diện
# ──────────────────────────────────────────────────────────────────────────────
@router.put(
    "/{image_id}/primary",
    response_model=HinhAnhResponse,
    summary="Đặt ảnh làm ảnh đại diện",
    description=(
        "Đặt ảnh `image_id` làm ảnh đại diện (primary) của khách sạn. "
        "Hệ thống tự động bỏ cờ `la_anh_chinh` của ảnh cũ, đảm bảo chỉ 1 ảnh chính."
    ),
)
async def set_primary_image(
    hotel_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await ImageService.set_primary(
        db=db,
        id_khach_san=hotel_id,
        id_hinh_anh=image_id,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /hotels/{hotel_id}/images/{image_id} — Xóa ảnh
# ──────────────────────────────────────────────────────────────────────────────
@router.delete(
    "/{image_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa ảnh khách sạn",
    description="Xóa vĩnh viễn ảnh có `image_id` khỏi khách sạn. Chỉ partner sở hữu mới có quyền.",
)
async def delete_image(
    hotel_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await ImageService.delete_image(
        db=db,
        id_khach_san=hotel_id,
        id_hinh_anh=image_id,
        partner_id=partner_id,
    )

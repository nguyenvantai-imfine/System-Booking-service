"""
policies.py - Endpoints Nhóm 4: Quản lý Chính Sách Khách Sạn

  POST   /hotels/{hotel_id}/policies/              → Thêm chính sách mới
  PUT    /hotels/{hotel_id}/policies/{policy_id}   → Cập nhật chính sách
  DELETE /hotels/{hotel_id}/policies/{policy_id}   → Xóa chính sách
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_partner_id, get_db
from src.schemas.hotel_schema import (
    QuyTacKhachSanCreate,
    QuyTacKhachSanResponse,
    QuyTacKhachSanUpdate,
)
from src.services.hotel_service import PolicyService

router = APIRouter(
    prefix="/hotels/{hotel_id}/policies",
    tags=["📋 Chính Sách Khách Sạn"],
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/{hotel_id}/policies/ — Thêm chính sách mới
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=QuyTacKhachSanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm chính sách khách sạn",
    description=(
        "Thêm một chính sách mới cho khách sạn. Loại chính sách (loai_chinh_sach) bao gồm:\n"
        "- **CHECK_IN_OUT**: Giờ nhận / trả phòng\n"
        "- **HUY_PHONG**: Chính sách hủy đặt phòng & hoàn tiền\n"
        "- **TRE_EM**: Chính sách trẻ em, độ tuổi & giường phụ\n"
        "- **DAT_COC**: Quy định thanh toán / đặt cọc trước\n"
        "- **QUY_DINH_CHUNG**: Thú cưng, hút thuốc, tổ chức tiệc tùng..."
    ),
)
async def add_policy(
    hotel_id: int,
    policy_in: QuyTacKhachSanCreate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await PolicyService.add_policy(
        db=db,
        id_khach_san=hotel_id,
        policy_in=policy_in,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PUT /hotels/{hotel_id}/policies/{policy_id} — Cập nhật chính sách
# ──────────────────────────────────────────────────────────────────────────────
@router.put(
    "/{policy_id}",
    response_model=QuyTacKhachSanResponse,
    summary="Cập nhật chính sách",
    description="Cập nhật nội dung / giá trị của một chính sách hiện có. Chỉ truyền các trường cần thay đổi.",
)
async def update_policy(
    hotel_id: int,
    policy_id: int,
    policy_in: QuyTacKhachSanUpdate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await PolicyService.update_policy(
        db=db,
        id_khach_san=hotel_id,
        id_quy_tac=policy_id,
        policy_in=policy_in,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /hotels/{hotel_id}/policies/{policy_id} — Xóa chính sách
# ──────────────────────────────────────────────────────────────────────────────
@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa chính sách",
    description="Xóa vĩnh viễn một chính sách khỏi khách sạn. Chỉ partner sở hữu mới có quyền.",
)
async def delete_policy(
    hotel_id: int,
    policy_id: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await PolicyService.delete_policy(
        db=db,
        id_khach_san=hotel_id,
        id_quy_tac=policy_id,
        partner_id=partner_id,
    )

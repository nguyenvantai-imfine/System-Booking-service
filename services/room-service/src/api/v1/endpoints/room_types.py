from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.api.v1.dependencies import get_db, require_partner_or_admin, check_hotel_ownership
from src.models import LoaiPhongModel
from src.schemas import (
    LoaiPhongCreate,
    LoaiPhongUpdate,
    LoaiPhongResponse,
)
from src.services import RoomTypeService

router = APIRouter(tags=["🛏️ Quản lý Loại Phòng"])

# 1. Thêm mới loại phòng cho khách sạn
@router.post(
    "/hotels/{hotel_id}/room-types",
    response_model=LoaiPhongResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm mới loại phòng cho khách sạn",
)
def create_room_type(
    hotel_id: int,
    payload: LoaiPhongCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    check_hotel_ownership(hotel_id, user)
    return RoomTypeService.create_room_type(db, hotel_id, payload)

# 2. Danh sách loại phòng của khách sạn
@router.get(
    "/hotels/{hotel_id}/room-types",
    response_model=List[LoaiPhongResponse],
    summary="Danh sách loại phòng của khách sạn",
)
def get_room_types_by_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
):
    return RoomTypeService.get_room_types_by_hotel(db, hotel_id)

# 3. Xem chi tiết loại phòng theo ID
@router.get(
    "/room-types/{id}",
    response_model=LoaiPhongResponse,
    summary="Chi tiết loại phòng",
)
def get_room_type_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    return RoomTypeService.get_room_type_by_id(db, id)

# 4. Cập nhật thông tin và giá loại phòng
@router.put(
    "/room-types/{id}",
    response_model=LoaiPhongResponse,
    summary="Cập nhật giá và thông tin hạng phòng",
)
def update_room_type(
    id: int,
    payload: LoaiPhongUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    rt = db.query(LoaiPhongModel).filter(LoaiPhongModel.id_loai_phong == id).first()
    if rt:
        check_hotel_ownership(rt.id_khach_san, user)
    return RoomTypeService.update_room_type(db, id, payload)

# 5. Xóa loại phòng
@router.delete(
    "/room-types/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa loại phòng",
)
def delete_room_type(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    rt = db.query(LoaiPhongModel).filter(LoaiPhongModel.id_loai_phong == id).first()
    if rt:
        check_hotel_ownership(rt.id_khach_san, user)
    RoomTypeService.delete_room_type(db, id)
    return None

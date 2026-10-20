from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.api.v1.dependencies import get_db, require_partner_or_admin
from src.schemas import (
    PhongCreate,
    BatchCreateRoomsRequest,
    PhongStatusUpdate,
    PhongResponse,
    PaginatedRoomsResponse,
)
from src.services import RoomService

router = APIRouter(tags=["🚪 Quản lý Phòng Vật Lý"])

# 1. Tra cứu phòng khả dụng (phải đặt trước /rooms/{id} để tránh xung đột routing)
@router.get(
    "/rooms/available",
    response_model=List[PhongResponse],
    summary="Tra cứu phòng khả dụng theo khách sạn và ngày nhận/trả phòng",
)
def get_available_rooms(
    hotel_id: int = Query(..., description="ID khách sạn"),
    check_in: date = Query(..., description="Ngày nhận phòng (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Ngày trả phòng (YYYY-MM-DD)"),
    num_guests: int = Query(1, ge=1, description="Số lượng khách"),
    db: Session = Depends(get_db),
):
    return RoomService.get_available_rooms(
        db=db,
        hotel_id=hotel_id,
        check_in=check_in,
        check_out=check_out,
        num_guests=num_guests,
    )

# 2. Tạo hàng loạt số phòng cho loại phòng
@router.post(
    "/room-types/{type_id}/rooms/batch",
    response_model=List[PhongResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hàng loạt số phòng (ví dụ: từ phòng 201 đến 210)",
)
def batch_create_rooms(
    type_id: int,
    payload: BatchCreateRoomsRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    return RoomService.batch_create_rooms(db, type_id, payload)

# 3. Tạo 1 phòng đơn lẻ
@router.post(
    "/room-types/{type_id}/rooms",
    response_model=PhongResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm một phòng vật lý mới",
)
def create_single_room(
    type_id: int,
    payload: PhongCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    return RoomService.create_room(db, type_id, payload)

# 4. Lấy danh sách tất cả phòng của khách sạn
@router.get(
    "/hotels/{hotel_id}/rooms",
    response_model=PaginatedRoomsResponse,
    summary="Lấy danh sách tất cả phòng vật lý của khách sạn",
)
def get_hotel_rooms(
    hotel_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="AVAILABLE, OCCUPIED, MAINTENANCE, INACTIVE"),
    room_type_id: Optional[int] = Query(None, description="Lọc theo loại phòng"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total, total_pages = RoomService.get_all_rooms(
        db=db,
        hotel_id=hotel_id,
        status_filter=status_filter,
        room_type_id=room_type_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

# 5. Lấy danh sách toàn bộ phòng trong hệ thống (Hỗ trợ Admin Dashboard)
@router.get(
    "/rooms",
    response_model=PaginatedRoomsResponse,
    summary="Lấy toàn bộ danh sách phòng kèm tìm kiếm & lọc",
)
def get_all_rooms(
    hotel_id: Optional[int] = Query(None, description="Lọc theo ID khách sạn"),
    room_type_id: Optional[int] = Query(None, description="Lọc theo ID loại phòng"),
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái"),
    keyword: Optional[str] = Query(None, description="Từ khóa số phòng hoặc tên loại phòng"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total, total_pages = RoomService.get_all_rooms(
        db=db,
        hotel_id=hotel_id,
        status_filter=status_filter,
        room_type_id=room_type_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

# 6. Xem chi tiết phòng theo ID
@router.get(
    "/rooms/{id}",
    response_model=PhongResponse,
    summary="Xem chi tiết thông tin một phòng",
)
def get_room_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    return RoomService.get_room_by_id(db, id)

# 7. Cập nhật trạng thái phòng (AVAILABLE, OCCUPIED, MAINTENANCE, INACTIVE)
@router.patch(
    "/rooms/{id}/status",
    response_model=PhongResponse,
    summary="Cập nhật trạng thái phòng",
)
def update_room_status(
    id: int,
    payload: PhongStatusUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    return RoomService.update_room_status(db, id, payload)

# 8. Xóa phòng
@router.delete(
    "/rooms/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa phòng vật lý",
)
def delete_room(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_partner_or_admin),
):
    RoomService.delete_room(db, id)
    return None

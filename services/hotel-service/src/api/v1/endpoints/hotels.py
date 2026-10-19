"""
hotels.py - Endpoints Nhóm 1: Quản lý Khách Sạn (/hotels)

Danh sách endpoints:
  POST   /hotels/            → Tạo khách sạn mới (tự động gán partner từ JWT)
  GET    /hotels/            → Tìm kiếm & lọc danh sách (Brief format + phân trang)
  GET    /hotels/my-hotels   → Danh sách KS của partner đang đăng nhập
  GET    /hotels/{id}        → Xem chi tiết (Full format)
  PUT    /hotels/{id}        → Cập nhật thông tin
  PATCH  /hotels/{id}/status → Đổi trạng thái
  DELETE /hotels/{id}        → Xóa mềm (Soft Delete)
  POST   /hotels/{id}/restore → Khôi phục KS đã xóa
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_partner_id, get_db
from src.models.khach_san import TrangThaiKhachSan
from src.schemas.hotel_schema import (
    KhachSanBriefResponse,
    KhachSanCreate,
    KhachSanDetailResponse,
    KhachSanStatusUpdate,
    KhachSanUpdate,
    PaginatedResponse,
)
from src.services.hotel_service import HotelService, SearchService

router = APIRouter(
    prefix="/hotels",
    tags=["🏨 Quản lý Khách Sạn"],
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/ — Tạo khách sạn mới
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=KhachSanDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo khách sạn mới",
    description=(
        "Tạo một khách sạn mới thuộc về partner đang đăng nhập (lấy từ JWT token). "
        "Hỗ trợ tạo kèm hình ảnh, thông tin phụ, quy tắc và danh mục tiện ích trong 1 request."
    ),
)
async def create_hotel(
    hotel_in: KhachSanCreate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await HotelService.create(db=db, hotel_in=hotel_in, partner_id=partner_id)


# ──────────────────────────────────────────────────────────────────────────────
# GET /hotels/my-hotels — Khách sạn của partner hiện tại
# (Phải đặt TRƯỚC /{id} để tránh conflict routing)
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/my-hotels",
    response_model=PaginatedResponse[KhachSanBriefResponse],
    summary="Danh sách khách sạn của tôi",
    description="Trả về danh sách tất cả khách sạn thuộc partner đang đăng nhập, kèm phân trang.",
)
async def get_my_hotels(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    result = await HotelService.get_my_hotels(db=db, partner_id=partner_id, page=page, page_size=page_size)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# GET /hotels/ — Tìm kiếm & lọc danh sách
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PaginatedResponse[KhachSanBriefResponse],
    summary="Tìm kiếm & lọc danh sách khách sạn",
    description=(
        "Tìm kiếm & lọc đa tiêu chí: tên, thành phố, quận/huyện, tiện nghi, trạng thái. "
        "Kết quả trả về dạng Brief (gọn nhẹ) kèm phân trang chuẩn."
    ),
)
async def search_hotels(
    keyword: Optional[str] = Query(None, description="Từ khóa tìm theo tên khách sạn hoặc địa chỉ"),
    city: Optional[str] = Query(None, description="Thành phố hoặc Tỉnh"),
    district: Optional[str] = Query(None, description="Quận / Huyện"),
    amenities: Optional[List[str]] = Query(None, description="Lọc theo tiện nghi (ví dụ: Wifi, Bể bơi)"),
    trang_thai: Optional[TrangThaiKhachSan] = Query(None, description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    db: Session = Depends(get_db),
):
    result = await SearchService.search(
        db=db,
        keyword=keyword,
        city=city,
        district=district,
        amenities=amenities,
        trang_thai=trang_thai,
        page=page,
        page_size=page_size,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# GET /hotels/{id} — Xem chi tiết khách sạn
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/{id_khach_san}",
    response_model=KhachSanDetailResponse,
    summary="Xem chi tiết khách sạn",
    description="Trả về toàn bộ thông tin khách sạn (Full format) bao gồm ảnh, tiện nghi, chính sách.",
)
async def get_hotel_detail(
    id_khach_san: int,
    db: Session = Depends(get_db),
):
    return await HotelService.get_by_id(db=db, id_khach_san=id_khach_san)


# ──────────────────────────────────────────────────────────────────────────────
# PUT /hotels/{id} — Cập nhật thông tin khách sạn
# ──────────────────────────────────────────────────────────────────────────────
@router.put(
    "/{id_khach_san}",
    response_model=KhachSanDetailResponse,
    summary="Cập nhật thông tin khách sạn",
    description="Cập nhật một phần hoặc toàn bộ thông tin khách sạn. Chỉ partner sở hữu mới có quyền.",
)
async def update_hotel(
    id_khach_san: int,
    hotel_in: KhachSanUpdate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await HotelService.update(db=db, id_khach_san=id_khach_san, hotel_in=hotel_in, partner_id=partner_id)


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /hotels/{id}/status — Đổi trạng thái khách sạn
# ──────────────────────────────────────────────────────────────────────────────
@router.patch(
    "/{id_khach_san}/status",
    response_model=KhachSanDetailResponse,
    summary="Đổi trạng thái khách sạn",
    description=(
        "Thay đổi trạng thái kinh doanh: HOAT_DONG (mở cửa) | TAM_DUNG (tạm dừng) | CHO_DUYET. "
        "Không cho phép đặt DA_XOA qua endpoint này (dùng DELETE /{id})."
    ),
)
async def change_hotel_status(
    id_khach_san: int,
    body: KhachSanStatusUpdate,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await HotelService.change_status(
        db=db,
        id_khach_san=id_khach_san,
        trang_thai=body.trang_thai,
        partner_id=partner_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /hotels/{id} — Xóa mềm (Soft Delete)
# ──────────────────────────────────────────────────────────────────────────────
@router.delete(
    "/{id_khach_san}",
    status_code=status.HTTP_200_OK,
    summary="Xóa mềm khách sạn (Soft Delete)",
    description=(
        "Đánh dấu khách sạn là đã xóa (is_deleted=True, trang_thai=DA_XOA). "
        "Dữ liệu không bị xóa khỏi DB, có thể khôi phục bằng POST /{id}/restore."
    ),
)
async def soft_delete_hotel(
    id_khach_san: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await HotelService.soft_delete(db=db, id_khach_san=id_khach_san, partner_id=partner_id)


# ──────────────────────────────────────────────────────────────────────────────
# POST /hotels/{id}/restore — Khôi phục khách sạn đã xóa
# ──────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{id_khach_san}/restore",
    response_model=KhachSanDetailResponse,
    summary="Khôi phục khách sạn đã xóa mềm",
    description=(
        "Khôi phục khách sạn về trạng thái TAM_DUNG. "
        "Chỉ partner sở hữu mới có quyền. Khách sạn phải đang ở trạng thái DA_XOA."
    ),
)
async def restore_hotel(
    id_khach_san: int,
    db: Session = Depends(get_db),
    partner_id: int = Depends(get_current_partner_id),
):
    return await HotelService.restore(db=db, id_khach_san=id_khach_san, partner_id=partner_id)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from src.core.database import get_db
from src.schemas.hotel_schema import KhachSanCreate, KhachSanUpdate, KhachSanResponse
from src.repositories.hotel_repository import HotelRepository

router = APIRouter(prefix="/hotels", tags=["Quản lý Khách Sạn"])

# 1. Thêm mới khách sạn
@router.post("/", response_model=KhachSanResponse, summary="Thêm mới một khách sạn")
def create_hotel(hotel_in: KhachSanCreate, db: Session = Depends(get_db)):
    return HotelRepository.create(db=db, hotel_in=hotel_in)

# 2. Lấy danh sách khách sạn (Hỗ trợ tích hợp Tìm kiếm cơ bản qua query params)
@router.get("/", response_model=List[KhachSanResponse], summary="Lấy danh sách khách sạn hoặc tìm kiếm")
def get_hotels(
    keyword: Optional[str] = Query(None, description="Tìm theo tên khách sạn hoặc địa chỉ"),
    city: Optional[str] = Query(None, description="Tìm theo thành phố hoặc tỉnh"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    if keyword or city:
        return HotelRepository.search(db=db, keyword=keyword, city=city, skip=skip, limit=limit)
    return HotelRepository.get_all(db=db, skip=skip, limit=limit)

# 3. Lấy danh sách khách sạn theo Partner ID (id_tai_khoan)
@router.get("/partner/{id_tai_khoan}", response_model=List[KhachSanResponse], summary="Lấy danh sách khách sạn theo Partner ID")
def get_hotels_by_partner(id_tai_khoan: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return HotelRepository.get_by_partner_id(db=db, id_tai_khoan=id_tai_khoan, skip=skip, limit=limit)

# 4. Lấy chi tiết khách sạn theo ID
@router.get("/{id_khach_san}", response_model=KhachSanResponse, summary="Lấy thông tin khách sạn theo ID")
def get_hotel_by_id(id_khach_san: int, db: Session = Depends(get_db)):
    hotel = HotelRepository.get_by_id(db=db, id_khach_san=id_khach_san)
    if not hotel:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách sạn")
    return hotel

# 5. Cập nhật thông tin khách sạn
@router.put("/{id_khach_san}", response_model=KhachSanResponse, summary="Cập nhật thông tin khách sạn")
def update_hotel(id_khach_san: int, hotel_in: KhachSanUpdate, db: Session = Depends(get_db)):
    hotel = HotelRepository.update(db=db, id_khach_san=id_khach_san, hotel_in=hotel_in)
    if not hotel:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách sạn để cập nhật")
    return hotel

# 6. Vô hiệu hóa khách sạn (Soft Delete / Đổi trạng thái)
@router.patch("/{id_khach_san}/disable", response_model=KhachSanResponse, summary="Vô hiệu hóa/Ngừng hoạt động khách sạn")
def disable_hotel(id_khach_san: int, trang_thai: str = "Ngừng hoạt động", db: Session = Depends(get_db)):
    hotel = HotelRepository.disable(db=db, id_khach_san=id_khach_san, trang_thai=trang_thai)
    if not hotel:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách sạn")
    return hotel

# 7. Xóa cứng khách sạn khỏi CSDL
@router.delete("/{id_khach_san}", summary="Xóa vĩnh viễn khách sạn")
def delete_hotel(id_khach_san: int, db: Session = Depends(get_db)):
    success = HotelRepository.delete(db=db, id_khach_san=id_khach_san)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách sạn để xóa")
    return {"message": "Xóa khách sạn thành công"}
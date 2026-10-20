from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from src.models import (
    KhachSanModel,
    ThongTinKhachSanModel,
    QuyTacKhachSanModel,
    DanhMucTienIchModel,
    ChiTietTienNghiModel,
)
from src.schemas.hotel_schema import KhachSanCreate, KhachSanUpdate

class HotelRepository:

    @staticmethod
    def _base_query(db: Session):
        """Truy vấn cơ sở kèm nạp trước các quan hệ 1:N để tối ưu hóa hiệu năng và tránh lazy loading"""
        return db.query(KhachSanModel).options(
            selectinload(KhachSanModel.thong_tin),
            selectinload(KhachSanModel.quy_tac),
            selectinload(KhachSanModel.danh_muc_tien_ich).selectinload(DanhMucTienIchModel.chi_tiet_tien_nghi)
        )

    # 1. Lấy thông tin khách sạn theo ID
    @staticmethod
    def get_by_id(db: Session, id_khach_san: int) -> Optional[KhachSanModel]:
        return HotelRepository._base_query(db).filter(KhachSanModel.id_khach_san == id_khach_san).first()

    # 2. Lấy toàn bộ danh sách khách sạn (có phân trang)
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[KhachSanModel]:
        return HotelRepository._base_query(db).order_by(KhachSanModel.id_khach_san.desc()).offset(skip).limit(limit).all()

    # 3. Lấy danh sách khách sạn theo Partner ID (id_tai_khoan)
    @staticmethod
    def get_by_partner_id(db: Session, id_tai_khoan: int, skip: int = 0, limit: int = 100) -> List[KhachSanModel]:
        return HotelRepository._base_query(db)\
                 .filter(KhachSanModel.id_tai_khoan == id_tai_khoan)\
                 .order_by(KhachSanModel.id_khach_san.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()

    # 4. Tìm kiếm cơ bản (Theo tên khách sạn, thành phố, hoặc tỉnh)
    @staticmethod
    def search(db: Session, keyword: Optional[str] = None, city: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[KhachSanModel]:
        query = HotelRepository._base_query(db)
        
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    KhachSanModel.ten_khach_san.ilike(search_pattern),
                    KhachSanModel.dia_chi.ilike(search_pattern)
                )
            )
            
        if city:
            query = query.filter(
                or_(
                    KhachSanModel.thanh_pho.ilike(f"%{city}%"),
                    KhachSanModel.tinh.ilike(f"%{city}%")
                )
            )

        return query.order_by(KhachSanModel.id_khach_san.desc()).offset(skip).limit(limit).all()

    # 5. Thêm mới khách sạn (bao gồm hỗ trợ tạo kèm dữ liệu con)
    @staticmethod
    def create(db: Session, hotel_in: KhachSanCreate) -> KhachSanModel:
        db_hotel = KhachSanModel(
            id_tai_khoan=hotel_in.id_tai_khoan,
            ten_khach_san=hotel_in.ten_khach_san,
            email_khach_san=hotel_in.email_khach_san,
            sdt_khach_san=hotel_in.sdt_khach_san,
            trang_thai=hotel_in.trang_thai or "Hoạt động",
            dia_chi=hotel_in.dia_chi,
            thanh_pho=hotel_in.thanh_pho,
            tinh=hotel_in.tinh
        )

        # Lưu thông tin khách sạn phụ
        if hotel_in.thong_tin:
            for tt in hotel_in.thong_tin:
                db_hotel.thong_tin.append(
                    ThongTinKhachSanModel(
                        loai_thong_tin=tt.loai_thong_tin,
                        noi_dung=tt.noi_dung
                    )
                )

        # Lưu quy tắc khách sạn
        if hotel_in.quy_tac:
            for qt in hotel_in.quy_tac:
                db_hotel.quy_tac.append(
                    QuyTacKhachSanModel(
                        ten=qt.ten,
                        gia_tri_chon=qt.gia_tri_chon,
                        mo_ta=qt.mo_ta
                    )
                )

        # Lưu danh mục tiện ích & chi tiết tiện nghi
        if hotel_in.danh_muc_tien_ich:
            for dm in hotel_in.danh_muc_tien_ich:
                dm_model = DanhMucTienIchModel(
                    ten_danh_muc=dm.ten_danh_muc,
                    icon_danh_muc=dm.icon_danh_muc
                )
                if dm.chi_tiet_tien_nghi:
                    for ct in dm.chi_tiet_tien_nghi:
                        dm_model.chi_tiet_tien_nghi.append(
                            ChiTietTienNghiModel(ten_tien_ich=ct.ten_tien_ich)
                        )
                db_hotel.danh_muc_tien_ich.append(dm_model)

        db.add(db_hotel)
        db.commit()
        db.refresh(db_hotel)
        return db_hotel

    # 6. Cập nhật thông tin khách sạn
    @staticmethod
    def update(db: Session, id_khach_san: int, hotel_in: KhachSanUpdate) -> Optional[KhachSanModel]:
        db_hotel = HotelRepository.get_by_id(db, id_khach_san)
        if not db_hotel:
            return None
        
        # Lấy dữ liệu update dạng dict (loại bỏ các trường None/chưa truyền)
        update_data = hotel_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_hotel, key, value)

        db.commit()
        db.refresh(db_hotel)
        return db_hotel

    # 7. Vô hiệu hóa khách sạn (Soft Delete/Disable - Đổi trang_thai)
    @staticmethod
    def disable(db: Session, id_khach_san: int, trang_thai: str = "Ngừng hoạt động") -> Optional[KhachSanModel]:
        db_hotel = db.query(KhachSanModel).filter(KhachSanModel.id_khach_san == id_khach_san).first()
        if not db_hotel:
            return None
        
        db_hotel.trang_thai = trang_thai
        db.commit()
        db.refresh(db_hotel)
        return db_hotel

    # 8. Xóa cứng khách sạn khỏi CSDL (Hard Delete)
    @staticmethod
    def delete(db: Session, id_khach_san: int) -> bool:
        db_hotel = db.query(KhachSanModel).filter(KhachSanModel.id_khach_san == id_khach_san).first()
        if db_hotel:
            db.delete(db_hotel)
            db.commit()
            return True
        return False
"""
hotel_service.py - Tầng Service xử lý toàn bộ nghiệp vụ của Hotel Service.
Tách biệt hoàn toàn với tầng Repository (dữ liệu) và tầng API (trình bày).

Bao gồm:
  - HotelService:     Nghiệp vụ CRUD khách sạn + quyền partner + soft delete/restore
  - SearchService:    Tìm kiếm & lọc đa tiêu chí + phân trang
  - ImageService:     Thêm/xóa ảnh, gán ảnh đại diện (chỉ 1 ảnh chính)
  - AmenityService:   Thêm/xóa danh mục & chi tiết tiện nghi
  - PolicyService:    Thêm/sửa/xóa chính sách khách sạn
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from src.core.database import run_in_threadpool
from src.models import (
    ChiTietTienNghiModel,
    DanhMucTienIchModel,
    HinhAnhKhachSanModel,
    KhachSanModel,
    QuyTacKhachSanModel,
    TrangThaiKhachSan,
    ThongTinKhachSanModel,
)
from src.schemas.hotel_schema import (
    ChiTietTienNghiCreate,
    DanhMucTienIchCreate,
    HinhAnhCreate,
    KhachSanCreate,
    KhachSanUpdate,
    QuyTacKhachSanCreate,
    QuyTacKhachSanUpdate,
)

# ==============================================================================
# HELPER – truy vấn chung có eager-load đầy đủ quan hệ
# ==============================================================================

def _eager_query(db: Session):
    """Trả về query KhachSanModel kèm toàn bộ quan hệ con (tránh N+1)."""
    return db.query(KhachSanModel).options(
        selectinload(KhachSanModel.hinh_anh),
        selectinload(KhachSanModel.thong_tin),
        selectinload(KhachSanModel.quy_tac),
        selectinload(KhachSanModel.danh_muc_tien_ich).selectinload(
            DanhMucTienIchModel.chi_tiet_tien_nghi
        ),
    )


async def _get_hotel_or_404(db: Session, id_khach_san: int) -> KhachSanModel:
    """Lấy khách sạn (chưa xóa mềm). Raise 404 nếu không tìm thấy."""
    hotel = (
        _eager_query(db)
        .filter(
            KhachSanModel.id_khach_san == id_khach_san,
            KhachSanModel.is_deleted == False,
        )
        .first()
    )
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách sạn có ID = {id_khach_san}.",
        )
    return hotel


def _check_ownership(hotel: KhachSanModel, partner_id: int) -> None:
    """Kiểm tra quyền sở hữu. Cho phép Admin (partner_id == 1) hoặc chính chủ sở hữu."""
    if partner_id == 1 or hotel.id_tai_khoan == partner_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bạn không có quyền thực hiện thao tác này với khách sạn.",
    )


# ==============================================================================
# 1. HOTEL SERVICE – nghiệp vụ cốt lõi khách sạn
# ==============================================================================

class HotelService:

    # ── 1.1 Tạo mới khách sạn ──────────────────────────────────────────────
    @staticmethod
    async def create(db: Session, hotel_in: KhachSanCreate, partner_id: int) -> KhachSanModel:
        """
        Tạo khách sạn mới, tự động gán id_tai_khoan từ JWT (partner_id).
        Hỗ trợ tạo kèm hình ảnh, thông tin, quy tắc và danh mục tiện ích trong 1 request.
        """
        try:
            db_hotel = KhachSanModel(
                id_tai_khoan=partner_id,          # Gán từ token, không nhận từ body
                ten_khach_san=hotel_in.ten_khach_san,
                email_khach_san=hotel_in.email_khach_san,
                sdt_khach_san=hotel_in.sdt_khach_san,
                trang_thai=hotel_in.trang_thai,
                dia_chi=hotel_in.dia_chi,
                phuong_xa=hotel_in.phuong_xa,
                quan_huyen=hotel_in.quan_huyen,
                thanh_pho=hotel_in.thanh_pho,
                tinh=hotel_in.tinh,
                quoc_gia=hotel_in.quoc_gia,
                kinh_do=hotel_in.kinh_do,
                vi_do=hotel_in.vi_do,
                ma_buu_chinh=hotel_in.ma_buu_chinh,
                ten_nguoi_lien_he=hotel_in.ten_nguoi_lien_he,
                sdt_nguoi_lien_he=hotel_in.sdt_nguoi_lien_he,
            )

            # Hình ảnh kèm theo
            for idx, anh in enumerate(hotel_in.hinh_anh or []):
                # Đảm bảo chỉ có đúng 1 ảnh chính
                la_anh_chinh = anh.la_anh_chinh and idx == 0
                db_hotel.hinh_anh.append(
                    HinhAnhKhachSanModel(
                        duong_dan_anh=anh.duong_dan_anh,
                        loai_anh=anh.loai_anh,
                        la_anh_chinh=la_anh_chinh,
                        thu_tu=anh.thu_tu,
                    )
                )

            # Thông tin phụ
            for tt in hotel_in.thong_tin or []:
                db_hotel.thong_tin.append(
                    ThongTinKhachSanModel(
                        loai_thong_tin=tt.loai_thong_tin,
                        noi_dung=tt.noi_dung,
                    )
                )

            # Quy tắc / chính sách
            for qt in hotel_in.quy_tac or []:
                db_hotel.quy_tac.append(
                    QuyTacKhachSanModel(
                        loai_chinh_sach=qt.loai_chinh_sach,
                        ten=qt.ten,
                        gia_tri_chon=qt.gia_tri_chon,
                        mo_ta=qt.mo_ta,
                    )
                )

            # Danh mục tiện ích & chi tiết
            for dm in hotel_in.danh_muc_tien_ich or []:
                dm_model = DanhMucTienIchModel(
                    ten_danh_muc=dm.ten_danh_muc,
                    icon_danh_muc=dm.icon_danh_muc,
                )
                for ct in dm.chi_tiet_tien_nghi or []:
                    dm_model.chi_tiet_tien_nghi.append(
                        ChiTietTienNghiModel(ten_tien_ich=ct.ten_tien_ich)
                    )
                db_hotel.danh_muc_tien_ich.append(dm_model)

            db.add(db_hotel)
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, db_hotel)
            return db_hotel

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi tạo khách sạn: {str(exc)}",
            ) from exc

    # ── 1.2 Lấy chi tiết khách sạn theo ID ───────────────────────────────
    @staticmethod
    async def get_by_id(db: Session, id_khach_san: int) -> KhachSanModel:
        return await _get_hotel_or_404(db, id_khach_san)

    # ── 1.3 Lấy danh sách khách sạn của partner ───────────────────────────
    @staticmethod
    async def get_my_hotels(
        db: Session,
        partner_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = (
            db.query(KhachSanModel)
            .filter(
                KhachSanModel.id_tai_khoan == partner_id,
                KhachSanModel.is_deleted == False,
            )
        )
        total = await run_in_threadpool(query.count)
        items = await run_in_threadpool(
            lambda: query.order_by(KhachSanModel.id_khach_san.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    # ── 1.4 Cập nhật thông tin khách sạn ─────────────────────────────────
    @staticmethod
    async def update(
        db: Session,
        id_khach_san: int,
        hotel_in: KhachSanUpdate,
        partner_id: int,
    ) -> KhachSanModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        try:
            update_data = hotel_in.model_dump(exclude_unset=True)
            # Không cho phép thay đổi id_tai_khoan qua update
            update_data.pop("id_tai_khoan", None)

            for key, value in update_data.items():
                setattr(hotel, key, value)

            hotel.ngay_cap_nhat = datetime.utcnow()
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, hotel)
            return hotel

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi cập nhật khách sạn: {str(exc)}",
            ) from exc

    # ── 1.5 Đổi trạng thái khách sạn ──────────────────────────────────────
    @staticmethod
    async def change_status(
        db: Session,
        id_khach_san: int,
        trang_thai: TrangThaiKhachSan,
        partner_id: int,
    ) -> KhachSanModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        # Không cho phép set trạng thái DA_XOA qua endpoint này
        if trang_thai == TrangThaiKhachSan.DA_XOA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể đặt trạng thái DA_XOA. Hãy dùng endpoint DELETE /{id}.",
            )

        try:
            hotel.trang_thai = trang_thai
            hotel.ngay_cap_nhat = datetime.utcnow()
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, hotel)
            return hotel

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi đổi trạng thái: {str(exc)}",
            ) from exc

    # ── 1.6 Soft Delete ────────────────────────────────────────────────────
    @staticmethod
    async def soft_delete(db: Session, id_khach_san: int, partner_id: int) -> dict:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        try:
            hotel.is_deleted = True
            hotel.deleted_at = datetime.utcnow()
            hotel.trang_thai = TrangThaiKhachSan.DA_XOA
            hotel.ngay_cap_nhat = datetime.utcnow()
            await run_in_threadpool(db.commit)
            return {
                "message": f"Đã xóa mềm khách sạn '{hotel.ten_khach_san}' (ID={id_khach_san}) thành công.",
                "id_khach_san": id_khach_san,
            }

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi xóa khách sạn: {str(exc)}",
            ) from exc

    # ── 1.7 Restore (Khôi phục) ────────────────────────────────────────────
    @staticmethod
    async def restore(db: Session, id_khach_san: int, partner_id: int) -> KhachSanModel:
        """Khôi phục khách sạn đã bị xóa mềm."""
        hotel = (
            _eager_query(db)
            .filter(
                KhachSanModel.id_khach_san == id_khach_san,
                KhachSanModel.is_deleted == True,
            )
            .first()
        )
        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy khách sạn đã xóa có ID = {id_khach_san}.",
            )
        _check_ownership(hotel, partner_id)

        try:
            hotel.is_deleted = False
            hotel.deleted_at = None
            hotel.trang_thai = TrangThaiKhachSan.TAM_DUNG   # Khôi phục ở trạng thái Tạm dừng
            hotel.ngay_cap_nhat = datetime.utcnow()
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, hotel)
            return hotel

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi khôi phục khách sạn: {str(exc)}",
            ) from exc


# ==============================================================================
# 2. SEARCH SERVICE – tìm kiếm & lọc đa tiêu chí
# ==============================================================================

class SearchService:

    @staticmethod
    async def search(
        db: Session,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        amenities: Optional[List[str]] = None,
        trang_thai: Optional[TrangThaiKhachSan] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Lọc danh sách khách sạn theo nhiều tiêu chí kết hợp:
          - keyword:   Tìm trong tên khách sạn hoặc địa chỉ (LIKE)
          - city:      Thành phố hoặc Tỉnh (LIKE)
          - district:  Quận / Huyện (LIKE)
          - amenities: Danh sách tên tiện nghi (khách sạn phải có ÍT NHẤT 1 trong số đó)
          - trang_thai: Lọc theo trạng thái
        """
        from sqlalchemy import or_

        query = db.query(KhachSanModel).filter(KhachSanModel.is_deleted == False)

        # Mặc định chỉ trả về khách sạn đang hoạt động (khi không lọc theo trạng thái)
        if trang_thai:
            query = query.filter(KhachSanModel.trang_thai == trang_thai)
        else:
            query = query.filter(KhachSanModel.trang_thai != TrangThaiKhachSan.DA_XOA)

        if keyword:
            pattern = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    KhachSanModel.ten_khach_san.ilike(pattern),
                    KhachSanModel.dia_chi.ilike(pattern),
                )
            )

        if city:
            pattern = f"%{city.strip()}%"
            query = query.filter(
                or_(
                    KhachSanModel.thanh_pho.ilike(pattern),
                    KhachSanModel.tinh.ilike(pattern),
                )
            )

        if district:
            query = query.filter(
                KhachSanModel.quan_huyen.ilike(f"%{district.strip()}%")
            )

        if amenities:
            # Lọc khách sạn có ÍT NHẤT 1 tiện nghi khớp (subquery JOIN)
            query = query.filter(
                KhachSanModel.danh_muc_tien_ich.any(
                    DanhMucTienIchModel.chi_tiet_tien_nghi.any(
                        ChiTietTienNghiModel.ten_tien_ich.in_(amenities)
                    )
                )
            )

        total = await run_in_threadpool(query.count)
        items = await run_in_threadpool(
            lambda: query.order_by(KhachSanModel.id_khach_san.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


# ==============================================================================
# 3. IMAGE SERVICE – nghiệp vụ hình ảnh
# ==============================================================================

class ImageService:

    # ── 3.1 Thêm danh sách ảnh ────────────────────────────────────────────
    @staticmethod
    async def add_images(
        db: Session,
        id_khach_san: int,
        images_in: List[HinhAnhCreate],
        partner_id: int,
    ) -> List[HinhAnhKhachSanModel]:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        if not images_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Danh sách ảnh không được rỗng.",
            )

        try:
            created: List[HinhAnhKhachSanModel] = []
            for anh in images_in:
                # Nếu ảnh này được đánh dấu la_anh_chinh, bỏ cờ tất cả ảnh cũ trước
                if anh.la_anh_chinh:
                    await run_in_threadpool(
                        lambda: db.query(HinhAnhKhachSanModel).filter(
                            HinhAnhKhachSanModel.id_khach_san == id_khach_san,
                            HinhAnhKhachSanModel.la_anh_chinh == True,
                        ).update({"la_anh_chinh": False})
                    )

                new_image = HinhAnhKhachSanModel(
                    id_khach_san=id_khach_san,
                    duong_dan_anh=anh.duong_dan_anh,
                    loai_anh=anh.loai_anh,
                    la_anh_chinh=anh.la_anh_chinh,
                    thu_tu=anh.thu_tu,
                )
                db.add(new_image)
                created.append(new_image)

            await run_in_threadpool(db.commit)
            for img in created:
                await run_in_threadpool(db.refresh, img)
            return created

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi thêm ảnh: {str(exc)}",
            ) from exc

    # ── 3.2 Đặt ảnh đại diện (Primary) ───────────────────────────────────
    @staticmethod
    async def set_primary(
        db: Session,
        id_khach_san: int,
        id_hinh_anh: int,
        partner_id: int,
    ) -> HinhAnhKhachSanModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        target = (
            db.query(HinhAnhKhachSanModel)
            .filter(
                HinhAnhKhachSanModel.id_hinh_anh == id_hinh_anh,
                HinhAnhKhachSanModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy ảnh ID={id_hinh_anh} thuộc khách sạn ID={id_khach_san}.",
            )

        try:
            # Bỏ cờ ảnh chính cũ
            await run_in_threadpool(
                lambda: db.query(HinhAnhKhachSanModel).filter(
                    HinhAnhKhachSanModel.id_khach_san == id_khach_san,
                    HinhAnhKhachSanModel.la_anh_chinh == True,
                ).update({"la_anh_chinh": False})
            )

            # Đặt ảnh mới làm ảnh chính
            target.la_anh_chinh = True
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, target)
            return target

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi đặt ảnh đại diện: {str(exc)}",
            ) from exc

    # ── 3.3 Xóa ảnh ───────────────────────────────────────────────────────
    @staticmethod
    async def delete_image(
        db: Session,
        id_khach_san: int,
        id_hinh_anh: int,
        partner_id: int,
    ) -> dict:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        target = (
            db.query(HinhAnhKhachSanModel)
            .filter(
                HinhAnhKhachSanModel.id_hinh_anh == id_hinh_anh,
                HinhAnhKhachSanModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy ảnh ID={id_hinh_anh} thuộc khách sạn ID={id_khach_san}.",
            )

        try:
            await run_in_threadpool(db.delete, target)
            await run_in_threadpool(db.commit)
            return {"message": f"Đã xóa ảnh ID={id_hinh_anh} thành công."}

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi xóa ảnh: {str(exc)}",
            ) from exc


# ==============================================================================
# 4. AMENITY SERVICE – nghiệp vụ tiện nghi
# ==============================================================================

class AmenityService:

    # ── 4.1 Thêm danh mục tiện nghi ───────────────────────────────────────
    @staticmethod
    async def add_category(
        db: Session,
        id_khach_san: int,
        category_in: DanhMucTienIchCreate,
        partner_id: int,
    ) -> DanhMucTienIchModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        try:
            dm = DanhMucTienIchModel(
                id_khach_san=id_khach_san,
                ten_danh_muc=category_in.ten_danh_muc,
                icon_danh_muc=category_in.icon_danh_muc,
            )
            for ct in category_in.chi_tiet_tien_nghi or []:
                dm.chi_tiet_tien_nghi.append(
                    ChiTietTienNghiModel(ten_tien_ich=ct.ten_tien_ich)
                )
            db.add(dm)
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, dm)
            return dm

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi thêm danh mục tiện nghi: {str(exc)}",
            ) from exc

    # ── 4.2 Thêm chi tiết tiện nghi vào danh mục ─────────────────────────
    @staticmethod
    async def add_item(
        db: Session,
        id_khach_san: int,
        id_danh_muc: int,
        item_in: ChiTietTienNghiCreate,
        partner_id: int,
    ) -> ChiTietTienNghiModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        danh_muc = (
            db.query(DanhMucTienIchModel)
            .filter(
                DanhMucTienIchModel.id_danh_muc == id_danh_muc,
                DanhMucTienIchModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not danh_muc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy danh mục tiện nghi ID={id_danh_muc} của khách sạn ID={id_khach_san}.",
            )

        try:
            item = ChiTietTienNghiModel(
                id_danh_muc=id_danh_muc,
                ten_tien_ich=item_in.ten_tien_ich,
            )
            db.add(item)
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, item)
            return item

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi thêm tiện nghi: {str(exc)}",
            ) from exc

    # ── 4.3 Xóa chi tiết tiện nghi ────────────────────────────────────────
    @staticmethod
    async def delete_item(
        db: Session,
        id_khach_san: int,
        id_tien_nghi: int,
        partner_id: int,
    ) -> dict:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        item = (
            db.query(ChiTietTienNghiModel)
            .join(DanhMucTienIchModel, ChiTietTienNghiModel.id_danh_muc == DanhMucTienIchModel.id_danh_muc)
            .filter(
                ChiTietTienNghiModel.id_tien_nghi == id_tien_nghi,
                DanhMucTienIchModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy tiện nghi ID={id_tien_nghi} thuộc khách sạn ID={id_khach_san}.",
            )

        try:
            await run_in_threadpool(db.delete, item)
            await run_in_threadpool(db.commit)
            return {"message": f"Đã xóa tiện nghi '{item.ten_tien_ich}' (ID={id_tien_nghi}) thành công."}

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi xóa tiện nghi: {str(exc)}",
            ) from exc


# ==============================================================================
# 5. POLICY SERVICE – nghiệp vụ chính sách khách sạn
# ==============================================================================

class PolicyService:

    # ── 5.1 Thêm chính sách ───────────────────────────────────────────────
    @staticmethod
    async def add_policy(
        db: Session,
        id_khach_san: int,
        policy_in: QuyTacKhachSanCreate,
        partner_id: int,
    ) -> QuyTacKhachSanModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        try:
            policy = QuyTacKhachSanModel(
                id_khach_san=id_khach_san,
                loai_chinh_sach=policy_in.loai_chinh_sach,
                ten=policy_in.ten,
                gia_tri_chon=policy_in.gia_tri_chon,
                mo_ta=policy_in.mo_ta,
            )
            db.add(policy)
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, policy)
            return policy

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi thêm chính sách: {str(exc)}",
            ) from exc

    # ── 5.2 Cập nhật chính sách ───────────────────────────────────────────
    @staticmethod
    async def update_policy(
        db: Session,
        id_khach_san: int,
        id_quy_tac: int,
        policy_in: QuyTacKhachSanUpdate,
        partner_id: int,
    ) -> QuyTacKhachSanModel:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        policy = (
            db.query(QuyTacKhachSanModel)
            .filter(
                QuyTacKhachSanModel.id_quy_tac == id_quy_tac,
                QuyTacKhachSanModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy chính sách ID={id_quy_tac} thuộc khách sạn ID={id_khach_san}.",
            )

        try:
            update_data = policy_in.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(policy, key, value)
            await run_in_threadpool(db.commit)
            await run_in_threadpool(db.refresh, policy)
            return policy

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi cập nhật chính sách: {str(exc)}",
            ) from exc

    # ── 5.3 Xóa chính sách ────────────────────────────────────────────────
    @staticmethod
    async def delete_policy(
        db: Session,
        id_khach_san: int,
        id_quy_tac: int,
        partner_id: int,
    ) -> dict:
        hotel = await _get_hotel_or_404(db, id_khach_san)
        _check_ownership(hotel, partner_id)

        policy = (
            db.query(QuyTacKhachSanModel)
            .filter(
                QuyTacKhachSanModel.id_quy_tac == id_quy_tac,
                QuyTacKhachSanModel.id_khach_san == id_khach_san,
            )
            .first()
        )
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy chính sách ID={id_quy_tac} thuộc khách sạn ID={id_khach_san}.",
            )

        try:
            await run_in_threadpool(db.delete, policy)
            await run_in_threadpool(db.commit)
            return {"message": f"Đã xóa chính sách '{policy.ten}' (ID={id_quy_tac}) thành công."}

        except SQLAlchemyError as exc:
            await run_in_threadpool(db.rollback)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi cơ sở dữ liệu khi xóa chính sách: {str(exc)}",
            ) from exc

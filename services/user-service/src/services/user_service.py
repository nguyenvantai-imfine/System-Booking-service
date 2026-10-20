from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from fastapi import HTTPException, status
from src.models import TaiKhoanModel, NguoiDungModel, VaiTroEnum, TrangThaiTaiKhoanEnum
from src.schemas.user_schema import (
    NguoiDungProfile,
    NguoiDungUpdate,
    TaiKhoanResponse,
    UserPaginatedResponse,
)
from src.core.security import hash_password

class UserService:

    @staticmethod
    def _to_response(u: TaiKhoanModel) -> TaiKhoanResponse:
        p = u.nguoi_dung
        profile = None
        if p:
            profile = NguoiDungProfile(
                id_nguoi_dung=p.id_nguoi_dung,
                ho=p.ho,
                ten=p.ten,
                ho_va_ten=p.ho_va_ten,
                ngay_sinh=p.ngay_sinh,
                gioi_tinh=p.gioi_tinh,
                dia_chi=p.dia_chi,
                avatar=p.avatar,
                cccd=p.cccd,
            )
        return TaiKhoanResponse(
            id_tai_khoan=u.id_tai_khoan,
            ten_dang_nhap=u.ten_dang_nhap,
            email=u.email,
            sdt=u.sdt,
            vai_tro=u.vai_tro,
            trang_thai=u.trang_thai,
            ngay_tao=u.ngay_tao,
            profile=profile,
        )

    @staticmethod
    def get_me(db: Session, user_id: int) -> TaiKhoanResponse:
        user = (
            db.query(TaiKhoanModel)
            .options(selectinload(TaiKhoanModel.nguoi_dung))
            .filter(TaiKhoanModel.id_tai_khoan == user_id)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản người dùng.",
            )
        return UserService._to_response(user)

    @staticmethod
    def update_profile(db: Session, user_id: int, req: NguoiDungUpdate) -> TaiKhoanResponse:
        user = (
            db.query(TaiKhoanModel)
            .options(selectinload(TaiKhoanModel.nguoi_dung))
            .filter(TaiKhoanModel.id_tai_khoan == user_id)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản người dùng.",
            )

        if req.sdt is not None:
            user.sdt = req.sdt

        p = user.nguoi_dung
        if not p:
            p = NguoiDungModel(id_tai_khoan=user.id_tai_khoan)
            db.add(p)

        if req.ho is not None: p.ho = req.ho
        if req.ten is not None: p.ten = req.ten
        if req.ngay_sinh is not None: p.ngay_sinh = req.ngay_sinh
        if req.gioi_tinh is not None: p.gioi_tinh = req.gioi_tinh
        if req.dia_chi is not None: p.dia_chi = req.dia_chi
        if req.avatar is not None: p.avatar = req.avatar
        if req.cccd is not None: p.cccd = req.cccd

        db.commit()
        db.refresh(user)
        return UserService._to_response(user)

    @staticmethod
    def get_users_admin(
        db: Session,
        role: Optional[VaiTroEnum] = None,
        status_val: Optional[TrangThaiTaiKhoanEnum] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserPaginatedResponse:
        query = db.query(TaiKhoanModel).options(selectinload(TaiKhoanModel.nguoi_dung))

        if role:
            query = query.filter(TaiKhoanModel.vai_tro == role)
        if status_val:
            query = query.filter(TaiKhoanModel.trang_thai == status_val)
        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.join(TaiKhoanModel.nguoi_dung, isouter=True).filter(
                or_(
                    TaiKhoanModel.ten_dang_nhap.ilike(kw),
                    TaiKhoanModel.email.ilike(kw),
                    TaiKhoanModel.sdt.ilike(kw),
                    NguoiDungModel.ho.ilike(kw),
                    NguoiDungModel.ten.ilike(kw),
                )
            )

        total = query.count()
        # Lưu ý: MSSQL bắt buộc order_by trước khi offset/limit
        items = (
            query.order_by(TaiKhoanModel.id_tai_khoan.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return UserPaginatedResponse(
            items=[UserService._to_response(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def change_user_status(
        db: Session, user_id: int, new_status: TrangThaiTaiKhoanEnum
    ) -> TaiKhoanResponse:
        user = (
            db.query(TaiKhoanModel)
            .options(selectinload(TaiKhoanModel.nguoi_dung))
            .filter(TaiKhoanModel.id_tai_khoan == user_id)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy người dùng có ID #{user_id}.",
            )

        user.trang_thai = new_status
        db.commit()
        db.refresh(user)
        return UserService._to_response(user)

    @staticmethod
    def seed_default_users(db: Session):
        """Khởi tạo tài khoản mẫu (Admin, Partner, Customer) nếu chưa có."""
        try:
            admin_acc = db.query(TaiKhoanModel).filter(
                or_(
                    TaiKhoanModel.ten_dang_nhap == "admin",
                    TaiKhoanModel.email == "admin@hotel.com",
                )
            ).first()

            if not admin_acc:
                admin_acc = TaiKhoanModel(
                    ten_dang_nhap="admin",
                    email="admin@hotel.com",
                    sdt="0901234567",
                    mat_khau_hash=hash_password("123456"),
                    vai_tro=VaiTroEnum.ADMIN,
                    trang_thai=TrangThaiTaiKhoanEnum.ACTIVE,
                )
                db.add(admin_acc)
                db.flush()
                profile_admin = NguoiDungModel(
                    id_tai_khoan=admin_acc.id_tai_khoan,
                    ho="Quản Trị",
                    ten="Viên Hệ Thống",
                    gioi_tinh="Nam",
                    dia_chi="Hà Nội, Việt Nam",
                )
                db.add(profile_admin)
                print(">>> Seeded Admin account: admin@hotel.com / 123456")

            # Seed Partner mẫu
            partner_acc = db.query(TaiKhoanModel).filter(
                TaiKhoanModel.email == "partner@hotel.com"
            ).first()
            if not partner_acc:
                partner_acc = TaiKhoanModel(
                    ten_dang_nhap="partner1",
                    email="partner@hotel.com",
                    sdt="0912345678",
                    mat_khau_hash=hash_password("123456"),
                    vai_tro=VaiTroEnum.PARTNER,
                    trang_thai=TrangThaiTaiKhoanEnum.ACTIVE,
                )
                db.add(partner_acc)
                db.flush()
                profile_partner = NguoiDungModel(
                    id_tai_khoan=partner_acc.id_tai_khoan,
                    ho="Nguyen",
                    ten="Doi Tac",
                    gioi_tinh="Nam",
                    dia_chi="Da Nang, Viet Nam",
                )
                db.add(profile_partner)
                print(">>> Seeded Partner account: partner@hotel.com / 123456")

            # Seed Customer mẫu
            cust_acc = db.query(TaiKhoanModel).filter(
                TaiKhoanModel.email == "customer@gmail.com"
            ).first()
            if not cust_acc:
                cust_acc = TaiKhoanModel(
                    ten_dang_nhap="customer1",
                    email="customer@gmail.com",
                    sdt="0987654321",
                    mat_khau_hash=hash_password("123456"),
                    vai_tro=VaiTroEnum.CUSTOMER,
                    trang_thai=TrangThaiTaiKhoanEnum.ACTIVE,
                )
                db.add(cust_acc)
                db.flush()
                profile_cust = NguoiDungModel(
                    id_tai_khoan=cust_acc.id_tai_khoan,
                    ho="Tran",
                    ten="Khach Hang",
                    gioi_tinh="Nu",
                    dia_chi="TP. Ho Chi Minh, Viet Nam",
                )
                db.add(profile_cust)
                print(">>> Seeded Customer account: customer@gmail.com / 123456")

            db.commit()
        except Exception as e:
            db.rollback()
            print("Warning seeding users:", str(e))

import math
import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, and_, desc, text
from sqlalchemy.orm import Session, selectinload
from src.core.config import settings
from src.models import (
    DatPhongModel,
    TrangThaiBookingEnum,
    ChiTietDatPhongModel,
    ThongTinKhachOModel,
    NhatKyBookingModel,
)
from src.schemas import (
    BookingCreateRequest,
    BookingStatusUpdate,
)

class BookingService:
    @staticmethod
    def release_expired_holds(db: Session) -> int:
        """Tự động hủy các đơn PENDING_PAYMENT đã quá hạn 15 phút giữ chỗ."""
        now_utc = datetime.utcnow()
        expired_bookings = (
            db.query(DatPhongModel)
            .filter(
                DatPhongModel.trang_thai == TrangThaiBookingEnum.PENDING_PAYMENT.value,
                DatPhongModel.han_giu_cho <= now_utc,
            )
            .all()
        )

        released_count = 0
        for bk in expired_bookings:
            bk.trang_thai = TrangThaiBookingEnum.CANCELLED.value
            bk.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=TrangThaiBookingEnum.PENDING_PAYMENT.value,
                    trang_thai_moi=TrangThaiBookingEnum.CANCELLED.value,
                    ly_do=f"Tự động hủy do quá hạn {settings.HOLD_MINUTES} phút giữ chỗ mà chưa thanh toán.",
                    thoi_gian=now_utc,
                )
            )
            released_count += 1

        if released_count > 0:
            db.commit()
            print(f">>> [Booking Service] Released {released_count} expired booking holds.")

        return released_count

    @staticmethod
    def create_booking(
        db: Session,
        payload: BookingCreateRequest,
        current_user_id: Optional[int] = None,
    ) -> DatPhongModel:
        """
        Tạo đơn đặt phòng mới với cơ chế chống Overbooking & Concurrency Protection tuyệt đối.
        - Khóa tài nguyên theo từng id_phong bằng sp_getapplock trong transaction (Deadlock-free nhờ sắp xếp id_phong).
        - Kết hợp table hints WITH (UPDLOCK, HOLDLOCK) trong truy vấn kiểm tra giao thoa ngày.
        - Điều kiện giao thoa: (new.CheckIn < old.CheckOut) AND (new.CheckOut > old.CheckIn).
        - Toàn bộ thao tác ghi (dat_phong, chi_tiet_dat_phong, thong_tin_khach_o, nhat_ky_booking) nằm trong một transaction nguyên tử; lỗi sẽ rollback hoàn toàn.
        - Tự động nhả các đơn quá hạn giữ chỗ 15 phút.
        """
        ngay_nhan = payload.ngay_nhan_phong
        ngay_tra = payload.ngay_tra_phong
        now_utc = datetime.utcnow()

        if ngay_nhan >= ngay_tra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngày nhận phòng phải trước ngày trả phòng.",
            )

        if not payload.rooms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đơn đặt phòng phải chứa ít nhất một phòng.",
            )

        nights = (ngay_tra - ngay_nhan).days
        if nights < 1:
            nights = 1

        # Sắp xếp danh sách id_phong tăng dần để triệt tiêu hoàn toàn khả năng Deadlock giữa các transaction (Canonical Ordering)
        sorted_phong_ids = sorted(list(set(r.id_phong for r in payload.rooms)))

        try:
            # 1. Khóa tài nguyên từng phòng bằng sp_getapplock trong transaction
            for id_phong in sorted_phong_ids:
                lock_resource = f"booking_lock_phong_{id_phong}"
                lock_sql = text("""
                    DECLARE @res INT;
                    EXEC @res = sp_getapplock 
                        @Resource = :res_name, 
                        @LockMode = 'Exclusive', 
                        @LockOwner = 'Transaction', 
                        @LockTimeout = 10000;
                    SELECT @res AS result;
                """)
                lock_res = db.execute(lock_sql, {"res_name": lock_resource}).scalar()
                if lock_res is not None and lock_res < 0:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Phòng #{id_phong} đang được xử lý trong một giao dịch khác. Vui lòng thử lại sau.",
                    )

            # 2. Giải phóng các đơn giữ chỗ đã hết hạn trước khi kiểm tra giao thoa
            BookingService.release_expired_holds(db)

            # 3. ── KIỂM TRA CHỐNG TRÙNG PHÒNG (CONCURRENCY PROTECTION) ──
            # Điều kiện giao thoa ngày: (DatPhongModel.ngay_nhan_phong < new.ngay_tra) AND (DatPhongModel.ngay_tra_phong > new.ngay_nhan)
            # Chỉ tính:
            #   - Đơn đã xác nhận (CONFIRMED / COMPLETED)
            #   - Đơn PENDING_PAYMENT còn trong hạn giữ chỗ (han_giu_cho > now_utc)
            conflicts = (
                db.query(
                    ChiTietDatPhongModel.id_phong,
                    ChiTietDatPhongModel.so_phong,
                    DatPhongModel.ma_booking,
                )
                .join(DatPhongModel, ChiTietDatPhongModel.id_dat_phong == DatPhongModel.id_dat_phong)
                .with_hint(ChiTietDatPhongModel, "WITH (UPDLOCK, HOLDLOCK)")
                .with_hint(DatPhongModel, "WITH (UPDLOCK, HOLDLOCK)")
                .filter(
                    ChiTietDatPhongModel.id_phong.in_(sorted_phong_ids),
                    DatPhongModel.ngay_nhan_phong < ngay_tra,
                    DatPhongModel.ngay_tra_phong > ngay_nhan,
                    or_(
                        DatPhongModel.trang_thai.in_([
                            TrangThaiBookingEnum.CONFIRMED.value,
                            TrangThaiBookingEnum.COMPLETED.value,
                        ]),
                        and_(
                            DatPhongModel.trang_thai == TrangThaiBookingEnum.PENDING_PAYMENT.value,
                            DatPhongModel.han_giu_cho > now_utc,
                        ),
                    ),
                )
                .all()
            )

            if conflicts:
                conflicted_names = ", ".join(
                    set(str(c[1] or f"#{c[0]}") for c in conflicts)
                )
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Phòng đã có người đặt trong thời gian này: {conflicted_names}",
                )

            # 4. Tính tổng tiền
            total_price_per_night = sum(float(r.gia) for r in payload.rooms)
            tong_tien = total_price_per_night * nights

            # Sinh mã booking duy nhất: BK-YYYYMM-XXXX
            random_suffix = uuid.uuid4().hex[:6].upper()
            ma_booking = f"BK-{now_utc.strftime('%Y%m')}-{random_suffix}"

            # Thiết lập thời hạn giữ chỗ 15 phút
            han_giu_cho = now_utc + timedelta(minutes=settings.HOLD_MINUTES)
            user_id = payload.id_tai_khoan or current_user_id or 1

            # 5. Khởi tạo toàn bộ dữ liệu trong cùng một transaction nguyên tử
            db_booking = DatPhongModel(
                ma_booking=ma_booking,
                id_tai_khoan=user_id,
                id_khach_san=payload.id_khach_san,
                ngay_nhan_phong=ngay_nhan,
                ngay_tra_phong=ngay_tra,
                tong_tien=tong_tien,
                trang_thai=TrangThaiBookingEnum.PENDING_PAYMENT.value,
                han_giu_cho=han_giu_cho,
            )

            # Thêm chi tiết các phòng
            for r in payload.rooms:
                db_booking.chi_tiet.append(
                    ChiTietDatPhongModel(
                        id_phong=r.id_phong,
                        id_loai_phong=r.id_loai_phong,
                        so_phong=r.so_phong,
                        ten_loai_phong=r.ten_loai_phong,
                        gia_tai_thoi_diem_dat=r.gia,
                    )
                )

            # Thêm thông tin khách ở
            db_booking.khach_o = ThongTinKhachOModel(
                ho_ten=payload.khach_o.ho_ten,
                email=payload.khach_o.email,
                sdt=payload.khach_o.sdt,
                ghi_chu_dac_biet=payload.khach_o.ghi_chu_dac_biet,
            )

            # Ghi nhật ký khởi tạo
            db_booking.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=None,
                    trang_thai_moi=TrangThaiBookingEnum.PENDING_PAYMENT.value,
                    ly_do=f"Khởi tạo đơn đặt phòng, giữ chỗ {settings.HOLD_MINUTES} phút.",
                    thoi_gian=now_utc,
                )
            )

            db.add(db_booking)
            db.commit()
            db.refresh(db_booking)
            return db_booking

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi xử lý tạo đơn đặt phòng: {str(e)}",
            )

    @staticmethod
    def get_all_bookings(
        db: Session,
        hotel_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DatPhongModel], int, int]:
        """Lấy danh sách toàn bộ đơn đặt phòng kèm phân trang MSSQL."""
        BookingService.release_expired_holds(db)

        query = (
            db.query(DatPhongModel)
            .options(
                selectinload(DatPhongModel.chi_tiet),
                selectinload(DatPhongModel.khach_o),
                selectinload(DatPhongModel.nhat_ky),
            )
        )

        if hotel_id is not None:
            query = query.filter(DatPhongModel.id_khach_san == hotel_id)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(DatPhongModel.trang_thai == status_filter.upper())

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.outerjoin(DatPhongModel.khach_o).filter(
                or_(
                    DatPhongModel.ma_booking.ilike(kw),
                    ThongTinKhachOModel.ho_ten.ilike(kw),
                    ThongTinKhachOModel.email.ilike(kw),
                    ThongTinKhachOModel.sdt.ilike(kw),
                )
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        items = (
            query.order_by(desc(DatPhongModel.id_dat_phong))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total, total_pages

    @staticmethod
    def get_booking_by_id_or_code(
        db: Session, id_or_code: str
    ) -> DatPhongModel:
        BookingService.release_expired_holds(db)

        query = (
            db.query(DatPhongModel)
            .options(
                selectinload(DatPhongModel.chi_tiet),
                selectinload(DatPhongModel.khach_o),
                selectinload(DatPhongModel.nhat_ky),
            )
        )

        if id_or_code.isdigit():
            bk = query.filter(DatPhongModel.id_dat_phong == int(id_or_code)).first()
        else:
            bk = query.filter(DatPhongModel.ma_booking == id_or_code).first()

        if not bk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn đặt phòng: {id_or_code}",
            )
        return bk

    @staticmethod
    def confirm_booking(
        db: Session, id_or_code: str, note: Optional[str] = None
    ) -> DatPhongModel:
        """Xác nhận đơn sau khi thanh toán thành công."""
        bk = BookingService.get_booking_by_id_or_code(db, id_or_code)

        if bk.trang_thai == TrangThaiBookingEnum.CONFIRMED.value:
            return bk

        if bk.trang_thai == TrangThaiBookingEnum.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đơn đặt phòng này đã bị hủy, không thể xác nhận thanh toán.",
            )

        old_status = bk.trang_thai
        bk.trang_thai = TrangThaiBookingEnum.CONFIRMED.value

        bk.nhat_ky.append(
            NhatKyBookingModel(
                trang_thai_cu=old_status,
                trang_thai_moi=TrangThaiBookingEnum.CONFIRMED.value,
                ly_do=note or "Xác nhận thanh toán thành công qua cổng thanh toán.",
                thoi_gian=datetime.utcnow(),
            )
        )

        db.commit()
        db.refresh(bk)

        # Bắn tin nhắn qua RabbitMQ / Notification Service
        try:
            from src.core.publisher import publish_notification_event
            payload = {
                "ma_booking": bk.ma_booking,
                "id_dat_phong": bk.id_dat_phong,
                "id_tai_khoan": bk.id_tai_khoan,
                "id_khach_san": bk.id_khach_san,
                "ngay_nhan_phong": str(bk.ngay_nhan_phong),
                "ngay_tra_phong": str(bk.ngay_tra_phong),
                "tong_tien": float(bk.tong_tien),
                "ten_khach": bk.khach_o.ho_ten if bk.khach_o else "Quý khách",
                "email": bk.khach_o.email if bk.khach_o else "customer@hotel.com",
                "sdt": bk.khach_o.sdt if bk.khach_o else "",
                "danh_sach_phong": [
                    {
                        "so_phong": ct.so_phong or f"Phòng #{ct.id_phong}",
                        "ten_loai_phong": ct.ten_loai_phong or "Tiêu chuẩn",
                        "gia_tai_thoi_diem_dat": float(ct.gia_tai_thoi_diem_dat),
                    }
                    for ct in bk.chi_tiet
                ],
            }
            publish_notification_event("notification.booking.confirmed", payload)
        except Exception as mq_err:
            print(">>> [Booking Service] MQ Publish Warning:", mq_err)

        return bk

    @staticmethod
    def cancel_booking(
        db: Session, id_or_code: str, reason: Optional[str] = None
    ) -> DatPhongModel:
        """Hủy đơn đặt phòng và nhả phòng."""
        bk = BookingService.get_booking_by_id_or_code(db, id_or_code)

        if bk.trang_thai == TrangThaiBookingEnum.CANCELLED.value:
            return bk

        old_status = bk.trang_thai
        bk.trang_thai = TrangThaiBookingEnum.CANCELLED.value

        bk.nhat_ky.append(
            NhatKyBookingModel(
                trang_thai_cu=old_status,
                trang_thai_moi=TrangThaiBookingEnum.CANCELLED.value,
                ly_do=reason or "Hủy đơn đặt phòng.",
                thoi_gian=datetime.utcnow(),
            )
        )

        db.commit()
        db.refresh(bk)

        # Bắn tin nhắn hủy đơn qua RabbitMQ / Notification Service
        try:
            from src.core.publisher import publish_notification_event
            payload = {
                "ma_booking": bk.ma_booking,
                "id_dat_phong": bk.id_dat_phong,
                "id_tai_khoan": bk.id_tai_khoan,
                "ten_khach": bk.khach_o.ho_ten if bk.khach_o else "Quý khách",
                "email": bk.khach_o.email if bk.khach_o else "customer@hotel.com",
                "ly_do": reason or "Quá thời hạn giữ chỗ 15 phút hoặc quản trị viên hủy",
            }
            publish_notification_event("notification.booking.cancelled", payload)
        except Exception as mq_err:
            print(">>> [Booking Service] MQ Cancel Publish Warning:", mq_err)

        return bk

    @staticmethod
    def seed_default_bookings(db: Session) -> None:
        """Tạo đơn mẫu nếu CSDL chưa có đơn nào."""
        try:
            count = db.query(DatPhongModel).count()
            if count == 0:
                print(">>> [Booking Service] Seeding default sample booking...")
                now_utc = datetime.utcnow()
                sample = DatPhongModel(
                    ma_booking="BK-202610-8912",
                    id_tai_khoan=4,  # customer1
                    id_khach_san=1,
                    ngay_nhan_phong=date(2026, 11, 10),
                    ngay_tra_phong=date(2026, 11, 13),
                    tong_tien=3750000,
                    trang_thai=TrangThaiBookingEnum.CONFIRMED.value,
                    han_giu_cho=now_utc + timedelta(hours=24),
                )
                sample.chi_tiet.append(
                    ChiTietDatPhongModel(
                        id_phong=1,
                        id_loai_phong=1,
                        so_phong="P.101",
                        ten_loai_phong="Deluxe Ocean View",
                        gia_tai_thoi_diem_dat=1250000,
                    )
                )
                sample.khach_o = ThongTinKhachOModel(
                    ho_ten="Nguyễn Văn An",
                    email="customer@gmail.com",
                    sdt="0900000003",
                    ghi_chu_dac_biet="Yêu cầu phòng tầng cao, giường đôi king size.",
                )
                sample.nhat_ky.append(
                    NhatKyBookingModel(
                        trang_thai_cu=None,
                        trang_thai_moi=TrangThaiBookingEnum.CONFIRMED.value,
                        ly_do="Đơn mẫu hệ thống đã thanh toán qua VNPay.",
                        thoi_gian=now_utc,
                    )
                )
                db.add(sample)
                db.commit()
                print(">>> [Booking Service] Seeded default booking BK-202610-8912 successfully.")
        except Exception as e:
            db.rollback()
            print(">>> [Booking Service] Seed warning:", str(e))

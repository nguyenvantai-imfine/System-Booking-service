
import math
import uuid
import logging

from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import List, Optional, Tuple

import httpx

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
from src.schemas import BookingCreateRequest


logger = logging.getLogger(__name__)


class BookingService:

    # =========================================================
    # 1. KIEM TRA PHONG DA DUOC DAT
    # =========================================================

    @staticmethod
    def get_booked_room_ids(
        db: Session,
        hotel_id: int,
        check_in: date,
        check_out: date,
    ) -> List[int]:

        if check_in >= check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay nhan phong phai truoc ngay tra phong.",
            )

        BookingService.release_expired_holds(db)

        now_utc = datetime.utcnow()

        rows = (
            db.query(ChiTietDatPhongModel.id_phong)
            .join(
                DatPhongModel,
                ChiTietDatPhongModel.id_dat_phong
                == DatPhongModel.id_dat_phong,
            )
            .filter(
                DatPhongModel.id_khach_san == hotel_id,
                DatPhongModel.ngay_nhan_phong < check_out,
                DatPhongModel.ngay_tra_phong > check_in,
                or_(
                    DatPhongModel.trang_thai.in_([
                        TrangThaiBookingEnum.CONFIRMED.value,
                        TrangThaiBookingEnum.COMPLETED.value,
                    ]),
                    and_(
                        DatPhongModel.trang_thai
                        == TrangThaiBookingEnum.PENDING_PAYMENT.value,
                        DatPhongModel.han_giu_cho > now_utc,
                    ),
                ),
            )
            .distinct()
            .all()
        )

        return [
            row[0]
            for row in rows
            if row[0] is not None
        ]

    # =========================================================
    # 2. TU DONG HUY BOOKING HET HAN
    # =========================================================

    @staticmethod
    def release_expired_holds(
        db: Session,
        commit: bool = True,
    ) -> int:

        now_utc = datetime.utcnow()

        expired_bookings = (
            db.query(DatPhongModel)
            .filter(
                DatPhongModel.trang_thai
                == TrangThaiBookingEnum.PENDING_PAYMENT.value,
                DatPhongModel.han_giu_cho.isnot(None),
                DatPhongModel.han_giu_cho <= now_utc,
            )
            .with_hint(
                DatPhongModel,
                "WITH (UPDLOCK, READPAST, ROWLOCK)",
                dialect_name="mssql",
            )
            .all()
        )

        released_count = 0

        for booking in expired_bookings:

            old_status = booking.trang_thai

            booking.trang_thai = (
                TrangThaiBookingEnum.CANCELLED.value
            )

            booking.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=old_status,
                    trang_thai_moi=(
                        TrangThaiBookingEnum.CANCELLED.value
                    ),
                    ly_do=(
                        f"Tu dong huy do qua han "
                        f"{settings.HOLD_MINUTES} phut giu cho "
                        "ma chua thanh toan."
                    ),
                    thoi_gian=now_utc,
                )
            )

            released_count += 1

        if released_count > 0:
            db.flush()

            if commit:
                db.commit()

                logger.info(
                    "Released %s expired booking holds.",
                    released_count,
                )

        return released_count

    # =========================================================
    # 3. XAC THUC PHONG VA LAY GIA TU ROOM SERVICE
    # =========================================================

    @staticmethod
    def _verify_and_get_room_info(
        id_phong: int,
        id_khach_san: int,
        id_loai_phong: Optional[int] = None,
    ) -> dict:

        room_service_url = settings.ROOM_SERVICE_URL.rstrip("/")
        url = f"{room_service_url}/rooms/{id_phong}"

        headers = {
            "User-Agent": "booking-service",
            "Accept": "application/json",
        }

        try:
            from src.core.correlation import get_correlation_id

            correlation_id = get_correlation_id()

            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id

        except Exception:
            logger.debug(
                "Could not retrieve correlation ID.",
                exc_info=True,
            )

        try:
            with httpx.Client(timeout=5.0) as client:

                response = client.get(
                    url,
                    headers=headers,
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Phong ID {id_phong} khong ton tai.",
                    )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=(
                            "Khong the xac thuc phong tu Room Service. "
                            "Vui long thu lai sau."
                        ),
                    )

                try:
                    data = response.json()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Room Service tra ve JSON khong hop le.",
                    )

                if not isinstance(data, dict):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Du lieu phong tu Room Service khong hop le.",
                    )

                room_hotel_id = data.get("id_khach_san")

                if room_hotel_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            "Room Service khong tra ve "
                            "thong tin khach san."
                        ),
                    )

                try:
                    room_hotel_id = int(room_hotel_id)
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="ID khach san tu Room Service khong hop le.",
                    )

                if room_hotel_id != int(id_khach_san):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Phong #{id_phong} khong thuoc "
                            f"khach san ID {id_khach_san}."
                        ),
                    )

                room_status = str(
                    data.get("trang_thai", "")
                ).upper()

                if room_status != "AVAILABLE":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Phong #{id_phong} hien khong kha dung. "
                            f"Trang thai: {room_status or 'UNKNOWN'}."
                        ),
                    )

                actual_type_id = data.get("id_loai_phong")

                if (
                    id_loai_phong is not None
                    and actual_type_id is not None
                ):
                    try:
                        if int(id_loai_phong) != int(actual_type_id):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=(
                                    f"Loai phong cua phong #{id_phong} "
                                    "khong hop le."
                                ),
                            )
                    except (ValueError, TypeError):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="ID loai phong tu Room Service khong hop le.",
                        )

                room_type = data.get("loai_phong") or {}

                if not isinstance(room_type, dict):
                    room_type = {}

                listed_price = room_type.get(
                    "gia_co_ban_mot_dem"
                )

                room_type_name = room_type.get(
                    "ten_loai_phong"
                )

                target_type_id = (
                    actual_type_id or id_loai_phong
                )

                if listed_price is None:

                    if target_type_id is None:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=(
                                "Khong xac dinh duoc loai phong "
                                "de lay gia."
                            ),
                        )

                    type_url = (
                        f"{room_service_url}/room-types/{target_type_id}"
                    )

                    type_response = client.get(
                        type_url,
                        headers=headers,
                    )

                    if type_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=(
                                "Khong the lay gia phong "
                                "tu Room Service."
                            ),
                        )

                    try:
                        type_data = type_response.json()
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Du lieu loai phong khong hop le.",
                        )

                    if not isinstance(type_data, dict):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Du lieu loai phong khong hop le.",
                        )

                    # Neu Room Service tra ve ID loai phong,
                    # phai dam bao ID do dung voi phong dang kiem tra.
                    returned_type_id = type_data.get(
                        "id_loai_phong"
                    )

                    if (
                        returned_type_id is not None
                        and target_type_id is not None
                    ):
                        if int(returned_type_id) != int(target_type_id):
                            raise HTTPException(
                                status_code=status.HTTP_502_BAD_GATEWAY,
                                detail="Thong tin loai phong khong khop.",
                            )

                    listed_price = type_data.get(
                        "gia_co_ban_mot_dem"
                    )

                    if not room_type_name:
                        room_type_name = type_data.get(
                            "ten_loai_phong"
                        )

                if listed_price is None:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Room Service khong cung cap gia phong.",
                    )

                try:
                    price = Decimal(str(listed_price))
                except (InvalidOperation, ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gia phong tu Room Service khong hop le.",
                    )

                if not price.is_finite() or price <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gia phong phai lon hon 0.",
                    )

                return {
                    "gia_co_ban_mot_dem": price,
                    "so_phong": data.get("so_phong"),
                    "ten_loai_phong": room_type_name,
                    "id_loai_phong": target_type_id,
                }

        except HTTPException:
            raise

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Room Service phan hoi qua thoi gian cho.",
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Khong the ket noi Room Service.",
            )

        except Exception:
            logger.exception(
                "Unexpected error while verifying room %s.",
                id_phong,
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Co loi khi xac thuc phong tu Room Service.",
            )

    # =========================================================
    # 4. TAO BOOKING
    # =========================================================

    @staticmethod
    def create_booking(
        db: Session,
        payload: BookingCreateRequest,
        current_user_id: Optional[int] = None,
    ) -> DatPhongModel:

        ngay_nhan = payload.ngay_nhan_phong
        ngay_tra = payload.ngay_tra_phong

        if current_user_id is None or current_user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Yeu cau xac thuc tai khoan de dat phong.",
            )

        if ngay_nhan < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay nhan phong khong duoc nam trong qua khu.",
            )

        if ngay_nhan >= ngay_tra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay nhan phong phai truoc ngay tra phong.",
            )

        if not payload.rooms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Don dat phong phai chua it nhat mot phong.",
            )

        room_ids = [
            room.id_phong
            for room in payload.rooms
        ]

        if len(room_ids) != len(set(room_ids)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Mot phong khong the duoc dat nhieu lan "
                    "trong cung yeu cau."
                ),
            )

        nights = (ngay_tra - ngay_nhan).days
        verified_rooms = []

        # 4.1. Xac thuc phong va lay gia chinh thuc.

        for room in payload.rooms:

            room_info = BookingService._verify_and_get_room_info(
                id_phong=room.id_phong,
                id_khach_san=payload.id_khach_san,
                id_loai_phong=room.id_loai_phong,
            )

            listed_price = room_info["gia_co_ban_mot_dem"]

            try:
                client_price = Decimal(str(room.gia))
            except (InvalidOperation, ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Gia phong #{room.id_phong} khong hop le. "
                        "Vui long tai lai thong tin phong."
                    ),
                )

            if not client_price.is_finite() or client_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gia phong #{room.id_phong} khong hop le.",
                )

            if abs(client_price - listed_price) > Decimal("0.01"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Gia phong #{room.id_phong} da thay doi. "
                        "Vui long tai lai thong tin phong."
                    ),
                )

            verified_rooms.append({
                "id_phong": room.id_phong,
                "id_loai_phong": room_info["id_loai_phong"],
                "so_phong": (
                    room_info["so_phong"] or room.so_phong
                ),
                "ten_loai_phong": (
                    room_info["ten_loai_phong"]
                    or room.ten_loai_phong
                ),
                "gia": listed_price,
            })

        sorted_phong_ids = sorted(room_ids)

        try:

            # 4.2. Khoa cac phong theo thu tu tang dan.

            for id_phong in sorted_phong_ids:

                lock_resource = f"booking_lock_phong_{id_phong}"

                lock_sql = text("""
                    SET NOCOUNT ON;

                    DECLARE @res INT;

                    EXEC @res = sp_getapplock
                        @Resource = :res_name,
                        @LockMode = 'Exclusive',
                        @LockOwner = 'Transaction',
                        @LockTimeout = 10000;

                    SELECT @res AS result;
                """)

                lock_result = db.execute(
                    lock_sql,
                    {"res_name": lock_resource},
                ).scalar()

                if lock_result is None or lock_result < 0:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=(
                            f"Phong #{id_phong} dang duoc xu ly "
                            "trong giao dich khac. Vui long thu lai."
                        ),
                    )

            # 4.3. Giai phong booking het han trong transaction hien tai.

            BookingService.release_expired_holds(
                db,
                commit=False,
            )

            now_utc = datetime.utcnow()

            # 4.4. Kiem tra booking trung thoi gian.

            conflicts = (
                db.query(
                    ChiTietDatPhongModel.id_phong,
                    ChiTietDatPhongModel.so_phong,
                    DatPhongModel.ma_booking,
                )
                .join(
                    DatPhongModel,
                    ChiTietDatPhongModel.id_dat_phong
                    == DatPhongModel.id_dat_phong,
                )
                .with_hint(
                    ChiTietDatPhongModel,
                    "WITH (UPDLOCK, HOLDLOCK)",
                    dialect_name="mssql",
                )
                .with_hint(
                    DatPhongModel,
                    "WITH (UPDLOCK, HOLDLOCK)",
                    dialect_name="mssql",
                )
                .filter(
                    ChiTietDatPhongModel.id_phong.in_(
                        sorted_phong_ids
                    ),
                    DatPhongModel.id_khach_san
                    == payload.id_khach_san,
                    DatPhongModel.ngay_nhan_phong < ngay_tra,
                    DatPhongModel.ngay_tra_phong > ngay_nhan,
                    or_(
                        DatPhongModel.trang_thai.in_([
                            TrangThaiBookingEnum.CONFIRMED.value,
                            TrangThaiBookingEnum.COMPLETED.value,
                        ]),
                        and_(
                            DatPhongModel.trang_thai
                            == TrangThaiBookingEnum.PENDING_PAYMENT.value,
                            DatPhongModel.han_giu_cho > now_utc,
                        ),
                    ),
                )
                .all()
            )

            if conflicts:

                conflicted_names = ", ".join(
                    sorted({
                        str(row[1] or f"#{row[0]}")
                        for row in conflicts
                    })
                )

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Phong da co nguoi dat trong thoi gian nay: "
                        f"{conflicted_names}"
                    ),
                )

            # 4.5. Tinh tien bang Decimal.

            total_price_per_night = sum(
                (
                    item["gia"]
                    for item in verified_rooms
                ),
                Decimal("0.00"),
            )

            tien_phong = (
                total_price_per_night * Decimal(nights)
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            thue_phi = (
                tien_phong * Decimal("0.10")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            tong_tien = tien_phong + thue_phi

            # 4.6. Tao ma booking.

            ma_booking = (
                f"BK-{now_utc.strftime('%Y%m')}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )

            han_giu_cho = now_utc + timedelta(
                minutes=settings.HOLD_MINUTES
            )

            # 4.7. Tao booking chinh.

            db_booking = DatPhongModel(
                ma_booking=ma_booking,
                id_tai_khoan=current_user_id,
                id_khach_san=payload.id_khach_san,
                ngay_nhan_phong=ngay_nhan,
                ngay_tra_phong=ngay_tra,
                tien_phong=tien_phong,
                thue_phi=thue_phi,
                tong_tien=tong_tien,
                trang_thai=(
                    TrangThaiBookingEnum.PENDING_PAYMENT.value
                ),
                han_giu_cho=han_giu_cho,
            )

            # 4.8. Them chi tiet phong.

            for item in verified_rooms:

                db_booking.chi_tiet.append(
                    ChiTietDatPhongModel(
                        id_phong=item["id_phong"],
                        id_loai_phong=item["id_loai_phong"],
                        so_phong=item["so_phong"],
                        ten_loai_phong=item["ten_loai_phong"],
                        gia_tai_thoi_diem_dat=item["gia"],
                    )
                )

            # 4.9. Them thong tin khach o.

            db_booking.khach_o = ThongTinKhachOModel(
                ho_ten=payload.khach_o.ho_ten,
                email=payload.khach_o.email,
                sdt=payload.khach_o.sdt,
                ghi_chu_dac_biet=(
                    payload.khach_o.ghi_chu_dac_biet
                ),
            )

            # 4.10. Ghi lich su tao booking.

            db_booking.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=None,
                    trang_thai_moi=(
                        TrangThaiBookingEnum.PENDING_PAYMENT.value
                    ),
                    ly_do=(
                        f"Khoi tao don dat phong, "
                        f"giu cho {settings.HOLD_MINUTES} phut."
                    ),
                    thoi_gian=now_utc,
                )
            )

            db.add(db_booking)
            db.commit()
            db.refresh(db_booking)

            logger.info(
                "Created booking %s for user %s.",
                ma_booking,
                current_user_id,
            )

            return db_booking

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            logger.exception("Error while creating booking.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Co loi xay ra khi tao don dat phong.",
            )

    # =========================================================
    # 5. LAY DANH SACH BOOKING
    # =========================================================

    @staticmethod
    def get_all_bookings(
        db: Session,
        hotel_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DatPhongModel], int, int]:

        if page < 1 or page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thong tin phan trang khong hop le.",
            )

        BookingService.release_expired_holds(db)

        query = (
            db.query(DatPhongModel)
            .options(
                selectinload(DatPhongModel.chi_tiet),
                selectinload(DatPhongModel.khach_o),
                selectinload(DatPhongModel.nhat_ky),
            )
        )

        if user_id is not None:
            query = query.filter(
                DatPhongModel.id_tai_khoan == user_id
            )

        if hotel_id is not None:
            query = query.filter(
                DatPhongModel.id_khach_san == hotel_id
            )

        if status_filter and status_filter.upper() != "ALL":

            valid_statuses = {
                item.value
                for item in TrangThaiBookingEnum
            }

            normalized_status = status_filter.upper()

            if normalized_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Trang thai booking khong hop le.",
                )

            query = query.filter(
                DatPhongModel.trang_thai == normalized_status
            )

        if keyword and keyword.strip():

            search_keyword = f"%{keyword.strip()}%"

            query = (
                query.outerjoin(DatPhongModel.khach_o)
                .filter(
                    or_(
                        DatPhongModel.ma_booking.ilike(
                            search_keyword
                        ),
                        ThongTinKhachOModel.ho_ten.ilike(
                            search_keyword
                        ),
                        ThongTinKhachOModel.email.ilike(
                            search_keyword
                        ),
                        ThongTinKhachOModel.sdt.ilike(
                            search_keyword
                        ),
                    )
                )
            )

        total = query.count()

        total_pages = (
            math.ceil(total / page_size)
            if total > 0
            else 1
        )

        items = (
            query
            .order_by(desc(DatPhongModel.id_dat_phong))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total, total_pages

    # =========================================================
    # 6. LAY CHI TIET BOOKING
    # =========================================================

    @staticmethod
    def get_booking_by_id_or_code(
        db: Session,
        id_or_code: str,
        lock: bool = False,
        release_expired: bool = True,
    ) -> DatPhongModel:

        if release_expired:
            BookingService.release_expired_holds(db)

        query = (
            db.query(DatPhongModel)
            .options(
                selectinload(DatPhongModel.chi_tiet),
                selectinload(DatPhongModel.khach_o),
                selectinload(DatPhongModel.nhat_ky),
            )
        )

        if lock:
            query = query.with_hint(
                DatPhongModel,
                "WITH (UPDLOCK, ROWLOCK)",
                dialect_name="mssql",
            )

        if id_or_code.isdigit():
            booking = query.filter(
                DatPhongModel.id_dat_phong == int(id_or_code)
            ).first()
        else:
            booking = query.filter(
                DatPhongModel.ma_booking == id_or_code
            ).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay don dat phong: {id_or_code}",
            )

        return booking

    # =========================================================
    # 7. XAC NHAN BOOKING SAU THANH TOAN
    # =========================================================

    @staticmethod
    def confirm_booking(
        db: Session,
        id_or_code: str,
        note: Optional[str] = None,
    ) -> DatPhongModel:

        try:

            booking = BookingService.get_booking_by_id_or_code(
                db=db,
                id_or_code=id_or_code,
                lock=True,
                release_expired=False,
            )

            now_utc = datetime.utcnow()

            if booking.trang_thai == TrangThaiBookingEnum.CONFIRMED.value:
                db.rollback()
                return booking

            if (
                booking.trang_thai
                != TrangThaiBookingEnum.PENDING_PAYMENT.value
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Khong the xac nhan booking co trang thai "
                        f"{booking.trang_thai}."
                    ),
                )

            if (
                booking.han_giu_cho is None
                or booking.han_giu_cho <= now_utc
            ):

                old_status = booking.trang_thai

                booking.trang_thai = (
                    TrangThaiBookingEnum.CANCELLED.value
                )

                booking.nhat_ky.append(
                    NhatKyBookingModel(
                        trang_thai_cu=old_status,
                        trang_thai_moi=(
                            TrangThaiBookingEnum.CANCELLED.value
                        ),
                        ly_do=(
                            "Tu dong huy do booking da het han "
                            "giu cho truoc khi xac nhan thanh toan."
                        ),
                        thoi_gian=now_utc,
                    )
                )

                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Booking da het han giu cho, "
                        "khong the xac nhan."
                    ),
                )

            old_status = booking.trang_thai

            booking.trang_thai = (
                TrangThaiBookingEnum.CONFIRMED.value
            )

            booking.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=old_status,
                    trang_thai_moi=(
                        TrangThaiBookingEnum.CONFIRMED.value
                    ),
                    ly_do=(
                        note
                        or "Xac nhan thanh toan thanh cong qua cong thanh toan."
                    ),
                    thoi_gian=now_utc,
                )
            )

            db.commit()
            db.refresh(booking)

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            logger.exception("Error while confirming booking.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Co loi xay ra khi xac nhan booking.",
            )

        # Gui thong bao sau khi commit.

        try:

            from src.core.publisher import publish_notification_event

            notification_payload = {
                "ma_booking": booking.ma_booking,
                "id_dat_phong": booking.id_dat_phong,
                "id_tai_khoan": booking.id_tai_khoan,
                "id_khach_san": booking.id_khach_san,
                "ngay_nhan_phong": str(booking.ngay_nhan_phong),
                "ngay_tra_phong": str(booking.ngay_tra_phong),
                "tong_tien": str(booking.tong_tien),
                "ten_khach": (
                    booking.khach_o.ho_ten
                    if booking.khach_o
                    else "Quy khach"
                ),
                "email": (
                    booking.khach_o.email
                    if booking.khach_o
                    else None
                ),
                "sdt": (
                    booking.khach_o.sdt
                    if booking.khach_o
                    else ""
                ),
                "danh_sach_phong": [
                    {
                        "so_phong": (
                            detail.so_phong
                            or f"Phong #{detail.id_phong}"
                        ),
                        "ten_loai_phong": (
                            detail.ten_loai_phong or "Tieu chuan"
                        ),
                        "gia_tai_thoi_diem_dat": str(
                            detail.gia_tai_thoi_diem_dat
                        ),
                    }
                    for detail in booking.chi_tiet
                ],
            }

            publish_notification_event(
                "notification.booking.confirmed",
                notification_payload,
            )

        except Exception:
            logger.exception(
                "Notification publishing failed for confirmed booking %s.",
                booking.ma_booking,
            )

        return booking

    # =========================================================
    # 8. HUY BOOKING
    # =========================================================

    @staticmethod
    def cancel_booking(
        db: Session,
        id_or_code: str,
        reason: Optional[str] = None,
    ) -> DatPhongModel:

        try:

            booking = BookingService.get_booking_by_id_or_code(
                db=db,
                id_or_code=id_or_code,
                lock=True,
            )

            if booking.trang_thai == TrangThaiBookingEnum.CANCELLED.value:
                db.rollback()
                return booking

            if booking.trang_thai not in {
                TrangThaiBookingEnum.PENDING_PAYMENT.value,
                TrangThaiBookingEnum.CONFIRMED.value,
            }:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Khong the huy booking co trang thai "
                        f"{booking.trang_thai}."
                    ),
                )

            old_status = booking.trang_thai
            now_utc = datetime.utcnow()

            booking.trang_thai = (
                TrangThaiBookingEnum.CANCELLED.value
            )

            booking.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=old_status,
                    trang_thai_moi=(
                        TrangThaiBookingEnum.CANCELLED.value
                    ),
                    ly_do=reason or "Huy don dat phong.",
                    thoi_gian=now_utc,
                )
            )

            db.commit()
            db.refresh(booking)

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            logger.exception("Error while cancelling booking.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Co loi xay ra khi huy booking.",
            )

        # Gui thong bao sau khi commit.

        try:

            from src.core.publisher import publish_notification_event

            notification_payload = {
                "ma_booking": booking.ma_booking,
                "id_dat_phong": booking.id_dat_phong,
                "id_tai_khoan": booking.id_tai_khoan,
                "ten_khach": (
                    booking.khach_o.ho_ten
                    if booking.khach_o
                    else "Quy khach"
                ),
                "email": (
                    booking.khach_o.email
                    if booking.khach_o
                    else None
                ),
                "ly_do": reason or "Don dat phong da bi huy.",
            }

            publish_notification_event(
                "notification.booking.cancelled",
                notification_payload,
            )

        except Exception:
            logger.exception(
                "Notification publishing failed for cancelled booking %s.",
                booking.ma_booking,
            )

        return booking

    # =========================================================
    # 9. TAO BOOKING MAU
    # =========================================================

    @staticmethod
    def seed_default_bookings(db: Session) -> None:

        try:

            count = db.query(DatPhongModel).count()

            if count > 0:
                return

            logger.info("Seeding default sample booking.")

            now_utc = datetime.utcnow()

            tien_phong = Decimal("3750000.00")
            thue_phi = Decimal("375000.00")
            tong_tien = tien_phong + thue_phi

            sample = DatPhongModel(
                ma_booking=f"BK-{now_utc.strftime('%Y%m')}-8912",
                id_tai_khoan=4,
                id_khach_san=1,
                ngay_nhan_phong=date(2026, 11, 10),
                ngay_tra_phong=date(2026, 11, 13),
                tien_phong=tien_phong,
                thue_phi=thue_phi,
                tong_tien=tong_tien,
                trang_thai=(
                    TrangThaiBookingEnum.CONFIRMED.value
                ),
                han_giu_cho=None,
            )

            sample.chi_tiet.append(
                ChiTietDatPhongModel(
                    id_phong=1,
                    id_loai_phong=1,
                    so_phong="P.101",
                    ten_loai_phong="Deluxe Ocean View",
                    gia_tai_thoi_diem_dat=Decimal("1250000.00"),
                )
            )

            sample.khach_o = ThongTinKhachOModel(
                ho_ten="Nguyen Van An",
                email="customer@gmail.com",
                sdt="0900000003",
                ghi_chu_dac_biet=(
                    "Yeu cau phong tang cao, giuong doi king size."
                ),
            )

            sample.nhat_ky.append(
                NhatKyBookingModel(
                    trang_thai_cu=None,
                    trang_thai_moi=(
                        TrangThaiBookingEnum.CONFIRMED.value
                    ),
                    ly_do=(
                        "Don mau he thong da thanh toan qua VNPay."
                    ),
                    thoi_gian=now_utc,
                )
            )

            db.add(sample)
            db.commit()

            logger.info("Seeded default booking successfully.")

        except Exception:
            db.rollback()

            logger.exception("Could not seed default booking.")

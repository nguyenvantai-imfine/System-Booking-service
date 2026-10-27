import math
import json
import logging
import time
from urllib.parse import urlencode
from urllib.request import urlopen
from datetime import date
from typing import List, Optional, Set, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, selectinload
from src.core.config import settings
from src.models import (
    PhongModel,
    LoaiPhongModel,
    TrangThaiPhongEnum,
)
from src.schemas import (
    PhongCreate,
    BatchCreateRoomsRequest,
    PhongStatusUpdate,
)
from src.services.database_errors import handle_database_errors

logger = logging.getLogger(__name__)

ALLOWED_STATUS_TRANSITIONS = {
    TrangThaiPhongEnum.AVAILABLE: {
        TrangThaiPhongEnum.OCCUPIED,
        TrangThaiPhongEnum.MAINTENANCE,
        TrangThaiPhongEnum.INACTIVE,
    },
    TrangThaiPhongEnum.OCCUPIED: {
        TrangThaiPhongEnum.AVAILABLE,
    },
    TrangThaiPhongEnum.MAINTENANCE: {
        TrangThaiPhongEnum.AVAILABLE,
        TrangThaiPhongEnum.INACTIVE,
    },
    TrangThaiPhongEnum.INACTIVE: {
        TrangThaiPhongEnum.AVAILABLE,
    },
}


def _validate_status_transition(
    current_status: str, next_status: TrangThaiPhongEnum
) -> None:
    try:
        current = TrangThaiPhongEnum(current_status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trạng thái hiện tại của phòng không hợp lệ; cần kiểm tra dữ liệu phòng.",
        ) from exc

    if current == next_status:
        return

    allowed = ALLOWED_STATUS_TRANSITIONS[current]
    if next_status not in allowed:
        if next_status == TrangThaiPhongEnum.MAINTENANCE:
            detail = "Chỉ phòng đang ở trạng thái AVAILABLE mới được chuyển sang MAINTENANCE."
        else:
            detail = (
                f"Không thể chuyển trạng thái phòng từ {current.value} "
                f"sang {next_status.value}."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

class RoomService:
    @staticmethod
    def _get_booked_room_ids(
        hotel_id: int, check_in: date, check_out: date
    ) -> Optional[Set[int]]:
        """Return overlapping active booking room IDs, or None if Booking is unavailable."""
        base_url = settings.BOOKING_SERVICE_URL.rstrip("/")
        if not base_url.endswith("/api/v1"):
            base_url = f"{base_url}/api/v1"

        booked_room_ids: Set[int] = set()
        try:
            deadline = time.monotonic() + settings.BOOKING_SERVICE_TIMEOUT
            page = 1
            total_pages = 1
            while page <= total_pages:
                timeout = deadline - time.monotonic()
                if timeout <= 0:
                    raise TimeoutError("Booking Service request deadline exceeded.")
                query = urlencode(
                    {"hotel_id": hotel_id, "page": page, "page_size": 100}
                )
                url = f"{base_url}/bookings?{query}"
                with urlopen(url, timeout=timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                items = payload.get("items")
                if not isinstance(items, list):
                    raise ValueError("Booking Service response has no items list.")
                total_pages = int(payload["total_pages"])
                if total_pages < 1:
                    raise ValueError("Booking Service returned an invalid page count.")

                for booking in items:
                    if not isinstance(booking, dict):
                        raise ValueError("Booking Service returned an invalid booking.")
                    booking_status = str(
                        booking.get("trang_thai", "")
                    ).upper()
                    if booking_status not in {
                        "PENDING_PAYMENT",
                        "CONFIRMED",
                        "CANCELLED",
                        "COMPLETED",
                        "REFUNDED",
                    }:
                        raise ValueError(
                            "Booking Service returned an unknown booking status."
                        )
                    if booking_status not in {"PENDING_PAYMENT", "CONFIRMED"}:
                        continue

                    booking_check_in = date.fromisoformat(
                        str(booking["ngay_nhan_phong"])
                    )
                    booking_check_out = date.fromisoformat(
                        str(booking["ngay_tra_phong"])
                    )
                    if (
                        booking_check_in < check_out
                        and booking_check_out > check_in
                    ):
                        details = booking.get("chi_tiet", [])
                        if not isinstance(details, list) or not details:
                            raise ValueError(
                                "Booking Service returned invalid room details."
                            )
                        for detail in details:
                            if not isinstance(detail, dict):
                                raise ValueError(
                                    "Booking Service returned an invalid room detail."
                                )
                            room_id = detail.get("id_phong")
                            if room_id is None or int(room_id) < 1:
                                raise ValueError(
                                    "Booking Service returned an invalid room ID."
                                )
                            booked_room_ids.add(int(room_id))

                page += 1
            return booked_room_ids
        except Exception:
            logger.warning(
                "Booking Service unavailable or returned invalid data; "
                "availability will fall back to room status. URL: %s",
                settings.BOOKING_SERVICE_URL,
                exc_info=True,
            )
            return None

    @staticmethod
    @handle_database_errors("Không thể tạo phòng")
    def create_room(
        db: Session, type_id: int, payload: PhongCreate
    ) -> PhongModel:
        room_type = (
            db.query(LoaiPhongModel)
            .filter(LoaiPhongModel.id_loai_phong == type_id)
            .first()
        )
        if not room_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy loại phòng ID {type_id}",
            )

        # Kiểm tra trùng lặp số phòng trong cùng khách sạn
        existing = (
            db.query(PhongModel)
            .filter(
                PhongModel.id_khach_san == room_type.id_khach_san,
                PhongModel.so_phong == payload.so_phong,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Số phòng {payload.so_phong} đã tồn tại trong khách sạn này.",
            )

        db_room = PhongModel(
            id_loai_phong=type_id,
            id_khach_san=room_type.id_khach_san,
            so_phong=payload.so_phong,
            tang=payload.tang,
            trang_thai=payload.trang_thai.value,
            ghi_chu=payload.ghi_chu,
        )
        db.add(db_room)

        # Cập nhật số lượng phòng
        room_type.so_luong_phong += 1

        db.commit()
        db.refresh(db_room)
        return db_room

    @staticmethod
    @handle_database_errors("Không thể tạo hàng loạt phòng")
    def batch_create_rooms(
        db: Session, type_id: int, payload: BatchCreateRoomsRequest
    ) -> List[PhongModel]:
        room_type = (
            db.query(LoaiPhongModel)
            .filter(LoaiPhongModel.id_loai_phong == type_id)
            .first()
        )
        if not room_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy loại phòng ID {type_id}",
            )

        numbers_to_create: List[str] = []
        prefix = payload.prefix or ""

        if payload.from_number is not None and payload.to_number is not None:
            if payload.from_number > payload.to_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="from_number không được lớn hơn to_number.",
                )
            if (payload.to_number - payload.from_number + 1) > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Số lượng tạo hàng loạt tối đa là 100 phòng một lần.",
                )
            for n in range(payload.from_number, payload.to_number + 1):
                numbers_to_create.append(f"{prefix}{n}")
        elif payload.room_numbers and len(payload.room_numbers) > 0:
            numbers_to_create = payload.room_numbers
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cần cung cấp (from_number, to_number) hoặc mảng room_numbers.",
            )

        if len(set(numbers_to_create)) != len(numbers_to_create):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Danh sách tạo phòng chứa số phòng bị trùng; không có phòng nào được tạo.",
            )

        # Lấy danh sách số phòng đã tồn tại của khách sạn
        existing_rooms = {
            room_number
            for (room_number,) in db.query(PhongModel.so_phong)
            .filter(
                PhongModel.id_khach_san == room_type.id_khach_san,
                PhongModel.so_phong.in_(numbers_to_create),
            )
            .all()
        }
        duplicate_rooms = sorted(set(numbers_to_create).intersection(existing_rooms))
        if duplicate_rooms:
            duplicate_list = ", ".join(duplicate_rooms)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Số phòng đã tồn tại trong khách sạn này: {duplicate_list}. "
                    "Không có phòng nào được tạo."
                ),
            )

        created_rooms = [
            PhongModel(
                id_loai_phong=type_id,
                id_khach_san=room_type.id_khach_san,
                so_phong=num,
                tang=payload.tang if payload.tang is not None else 1,
                trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
            )
            for num in numbers_to_create
        ]
        db.add_all(created_rooms)

        # Cập nhật tổng số lượng phòng
        db.flush()
        total_count = (
            db.query(func.count(PhongModel.id_phong))
            .filter(PhongModel.id_loai_phong == type_id)
            .scalar()
        )
        room_type.so_luong_phong = total_count

        db.commit()
        for r in created_rooms:
            db.refresh(r)
        return created_rooms

    @staticmethod
    @handle_database_errors("Không thể tải danh sách phòng")
    def get_all_rooms(
        db: Session,
        hotel_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        room_type_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[PhongModel], int, int]:
        query = db.query(PhongModel).options(selectinload(PhongModel.loai_phong))

        if hotel_id is not None:
            query = query.filter(PhongModel.id_khach_san == hotel_id)

        if room_type_id is not None:
            query = query.filter(PhongModel.id_loai_phong == room_type_id)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(PhongModel.trang_thai == status_filter.upper())

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.join(PhongModel.loai_phong).filter(
                or_(
                    PhongModel.so_phong.ilike(kw),
                    PhongModel.ghi_chu.ilike(kw),
                    LoaiPhongModel.ten_loai_phong.ilike(kw),
                )
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # MSSQL Order By bắt buộc trước offset / limit
        items = (
            query.order_by(PhongModel.id_phong.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total, total_pages

    @staticmethod
    @handle_database_errors("Không thể tải thông tin phòng")
    def get_room_by_id(db: Session, room_id: int) -> PhongModel:
        room = (
            db.query(PhongModel)
            .options(selectinload(PhongModel.loai_phong))
            .filter(PhongModel.id_phong == room_id)
            .first()
        )
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy phòng ID {room_id}",
            )
        return room

    @staticmethod
    @handle_database_errors("Không thể cập nhật trạng thái phòng")
    def update_room_status(
        db: Session, room_id: int, payload: PhongStatusUpdate
    ) -> PhongModel:
        room = RoomService.get_room_by_id(db, room_id)
        _validate_status_transition(room.trang_thai, payload.trang_thai)
        room.trang_thai = payload.trang_thai.value
        if payload.ghi_chu is not None:
            room.ghi_chu = payload.ghi_chu

        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    @handle_database_errors("Không thể ngừng khai thác phòng")
    def delete_room(db: Session, room_id: int) -> None:
        room = RoomService.get_room_by_id(db, room_id)
        _validate_status_transition(
            room.trang_thai, TrangThaiPhongEnum.INACTIVE
        )
        room.trang_thai = TrangThaiPhongEnum.INACTIVE.value
        db.commit()

    @staticmethod
    @handle_database_errors("Không thể tra cứu phòng khả dụng")
    def get_available_rooms(
        db: Session,
        hotel_id: int,
        check_in: date,
        check_out: date,
        num_guests: int = 1,
    ) -> List[PhongModel]:
        """
        Truy vấn danh sách phòng khả dụng theo khách sạn và số lượng khách.
        """
        if check_in >= check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngày nhận phòng (check_in) phải trước ngày trả phòng (check_out).",
            )

        query = (
            db.query(PhongModel)
            .join(PhongModel.loai_phong)
            .options(selectinload(PhongModel.loai_phong))
            .filter(
                PhongModel.id_khach_san == hotel_id,
                PhongModel.trang_thai == TrangThaiPhongEnum.AVAILABLE.value,
                (LoaiPhongModel.suc_chua_nguoi_lon + LoaiPhongModel.suc_chua_tre_em)
                >= num_guests,
            )
            .order_by(PhongModel.so_phong.asc())
        )

        booked_room_ids = RoomService._get_booked_room_ids(
            hotel_id, check_in, check_out
        )
        if booked_room_ids:
            query = query.filter(~PhongModel.id_phong.in_(booked_room_ids))

        return query.all()

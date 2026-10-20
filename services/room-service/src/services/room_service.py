import math
from datetime import date
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, selectinload
from src.models import (
    PhongModel,
    LoaiPhongModel,
    TrangThaiPhongEnum,
    TienIchPhongModel,
    QuyTacPhongModel,
)
from src.schemas import (
    PhongCreate,
    BatchCreateRoomsRequest,
    PhongStatusUpdate,
)

class RoomService:
    @staticmethod
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
                status_code=status.HTTP_400_BAD_REQUEST,
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
            if (payload.to_number - payload.from_number) > 100:
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

        # Lấy danh sách số phòng đã tồn tại của khách sạn
        existing_rooms = set(
            db.query(PhongModel.so_phong)
            .filter(
                PhongModel.id_khach_san == room_type.id_khach_san,
                PhongModel.so_phong.in_(numbers_to_create),
            )
            .all()
        )
        existing_set = {r[0] for r in existing_rooms}

        created_rooms: List[PhongModel] = []
        for num in numbers_to_create:
            if num in existing_set:
                continue  # Bỏ qua nếu đã tồn tại

            new_room = PhongModel(
                id_loai_phong=type_id,
                id_khach_san=room_type.id_khach_san,
                so_phong=num,
                tang=payload.tang or 1,
                trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
            )
            db.add(new_room)
            created_rooms.append(new_room)

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
    def update_room_status(
        db: Session, room_id: int, payload: PhongStatusUpdate
    ) -> PhongModel:
        room = RoomService.get_room_by_id(db, room_id)
        room.trang_thai = payload.trang_thai.value
        if payload.ghi_chu is not None:
            room.ghi_chu = payload.ghi_chu

        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def delete_room(db: Session, room_id: int) -> None:
        room = RoomService.get_room_by_id(db, room_id)
        type_id = room.id_loai_phong
        db.delete(room)
        db.flush()

        # Cập nhật số lượng phòng của loại phòng
        room_type = (
            db.query(LoaiPhongModel)
            .filter(LoaiPhongModel.id_loai_phong == type_id)
            .first()
        )
        if room_type:
            total_count = (
                db.query(func.count(PhongModel.id_phong))
                .filter(PhongModel.id_loai_phong == type_id)
                .scalar()
            )
            room_type.so_luong_phong = total_count or 0

        db.commit()

    @staticmethod
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
        return query.all()

    @staticmethod
    def seed_default_data(db: Session) -> None:
        """Khởi tạo loại phòng mẫu và 10 phòng vật lý nếu CSDL còn trống."""
        try:
            count = db.query(LoaiPhongModel).count()
            if count == 0:
                print(">>> [Room Service] Seeding default room types and rooms...")
                # Hotel 1 (Khách sạn Mường Thanh hoặc Grand Hotel)
                hotel_id = 1

                # Loại 1: Deluxe Ocean View
                deluxe = LoaiPhongModel(
                    id_khach_san=hotel_id,
                    ten_loai_phong="Deluxe Ocean View",
                    mo_ta="Phòng Deluxe hướng biển cao cấp, đón bình minh tuyệt đẹp, ban công rộng.",
                    suc_chua_nguoi_lon=2,
                    suc_chua_tre_em=1,
                    gia_co_ban_mot_dem=1250000,
                    dien_tich_m2=35.5,
                    so_luong_phong=5,
                )
                deluxe.tien_ich.append(TienIchPhongModel(ten_tien_ich="Điều hòa 2 chiều", bieu_tuong="wind"))
                deluxe.tien_ich.append(TienIchPhongModel(ten_tien_ich="Ban công hướng biển", bieu_tuong="sun"))
                deluxe.tien_ich.append(TienIchPhongModel(ten_tien_ich="Bồn tắm nằm", bieu_tuong="bath"))
                deluxe.tien_ich.append(TienIchPhongModel(ten_tien_ich="Wifi tốc độ cao", bieu_tuong="wifi"))

                deluxe.quy_tac.append(QuyTacPhongModel(tieu_de="Không hút thuốc trong phòng", cho_phep=False))
                deluxe.quy_tac.append(QuyTacPhongModel(tieu_de="Không mang thú cưng", cho_phep=False))
                deluxe.quy_tac.append(QuyTacPhongModel(tieu_de="Giờ yên lặng từ 22:00", cho_phep=True))

                db.add(deluxe)
                db.flush()

                # Sinh 5 phòng Deluxe
                for i in range(101, 106):
                    db.add(
                        PhongModel(
                            id_loai_phong=deluxe.id_loai_phong,
                            id_khach_san=hotel_id,
                            so_phong=f"P.{i}",
                            tang=1,
                            trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
                            ghi_chu="Phòng mới nâng cấp",
                        )
                    )

                # Loại 2: Executive Suite
                suite = LoaiPhongModel(
                    id_khach_san=hotel_id,
                    ten_loai_phong="Executive Suite",
                    mo_ta="Phòng Suite sang trọng đẳng cấp với phòng khách riêng biệt và minibar cao cấp.",
                    suc_chua_nguoi_lon=4,
                    suc_chua_tre_em=2,
                    gia_co_ban_mot_dem=2500000,
                    dien_tich_m2=65.0,
                    so_luong_phong=5,
                )
                suite.tien_ich.append(TienIchPhongModel(ten_tien_ich="Phòng khách riêng", bieu_tuong="home"))
                suite.tien_ich.append(TienIchPhongModel(ten_tien_ich="Smart TV 65 inch", bieu_tuong="tv"))
                suite.tien_ich.append(TienIchPhongModel(ten_tien_ich="Minibar miễn phí", bieu_tuong="coffee"))
                suite.tien_ich.append(TienIchPhongModel(ten_tien_ich="Bồn tắm sục Jacuzzi", bieu_tuong="bath"))

                suite.quy_tac.append(QuyTacPhongModel(tieu_de="Không hút thuốc", cho_phep=False))

                db.add(suite)
                db.flush()

                # Sinh 5 phòng Suite
                for i in range(201, 206):
                    db.add(
                        PhongModel(
                            id_loai_phong=suite.id_loai_phong,
                            id_khach_san=hotel_id,
                            so_phong=f"P.{i}",
                            tang=2,
                            trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
                            ghi_chu="VIP Suite",
                        )
                    )

                db.commit()
                print(">>> [Room Service] Seeded 2 room types and 10 rooms successfully.")
        except Exception as e:
            db.rollback()
            print(">>> [Room Service] Seed warning:", str(e))

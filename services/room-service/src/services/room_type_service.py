from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from src.models import (
    LoaiPhongModel,
    TienIchPhongModel,
    QuyTacPhongModel,
    KhuyenMaiPhongModel,
)
from src.schemas import LoaiPhongCreate, LoaiPhongUpdate

class RoomTypeService:
    @staticmethod
    def create_room_type(
        db: Session, hotel_id: int, payload: LoaiPhongCreate
    ) -> LoaiPhongModel:
        db_type = LoaiPhongModel(
            id_khach_san=hotel_id,
            ten_loai_phong=payload.ten_loai_phong,
            mo_ta=payload.mo_ta,
            suc_chua_nguoi_lon=payload.suc_chua_nguoi_lon,
            suc_chua_tre_em=payload.suc_chua_tre_em,
            gia_co_ban_mot_dem=payload.gia_co_ban_mot_dem,
            dien_tich_m2=payload.dien_tich_m2,
            so_luong_phong=0,
        )

        for ti in payload.tien_ich or []:
            db_type.tien_ich.append(
                TienIchPhongModel(
                    ten_tien_ich=ti.ten_tien_ich,
                    bieu_tuong=ti.bieu_tuong,
                )
            )

        for qt in payload.quy_tac or []:
            db_type.quy_tac.append(
                QuyTacPhongModel(
                    tieu_de=qt.tieu_de,
                    cho_phep=qt.cho_phep,
                    ghi_chu=qt.ghi_chu,
                )
            )

        for km in payload.khuyen_mai or []:
            db_type.khuyen_mai.append(
                KhuyenMaiPhongModel(
                    ma_khuyen_mai=km.ma_khuyen_mai,
                    ngay_bat_dau=km.ngay_bat_dau,
                    ngay_ket_thuc=km.ngay_ket_thuc,
                    phan_tram_giam=km.phan_tram_giam,
                    mo_ta=km.mo_ta,
                )
            )

        db.add(db_type)
        db.commit()
        db.refresh(db_type)
        return db_type

    @staticmethod
    def get_room_types_by_hotel(db: Session, hotel_id: int) -> List[LoaiPhongModel]:
        return (
            db.query(LoaiPhongModel)
            .filter(LoaiPhongModel.id_khach_san == hotel_id)
            .options(
                selectinload(LoaiPhongModel.tien_ich),
                selectinload(LoaiPhongModel.quy_tac),
                selectinload(LoaiPhongModel.khuyen_mai),
            )
            .order_by(LoaiPhongModel.id_loai_phong.asc())
            .all()
        )

    @staticmethod
    def get_room_type_by_id(db: Session, id_loai_phong: int) -> LoaiPhongModel:
        db_type = (
            db.query(LoaiPhongModel)
            .filter(LoaiPhongModel.id_loai_phong == id_loai_phong)
            .options(
                selectinload(LoaiPhongModel.tien_ich),
                selectinload(LoaiPhongModel.quy_tac),
                selectinload(LoaiPhongModel.khuyen_mai),
            )
            .first()
        )
        if not db_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy loại phòng ID {id_loai_phong}",
            )
        return db_type

    @staticmethod
    def update_room_type(
        db: Session, id_loai_phong: int, payload: LoaiPhongUpdate
    ) -> LoaiPhongModel:
        db_type = RoomTypeService.get_room_type_by_id(db, id_loai_phong)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_type, key, value)

        db.commit()
        db.refresh(db_type)
        return db_type

    @staticmethod
    def delete_room_type(db: Session, id_loai_phong: int) -> None:
        db_type = RoomTypeService.get_room_type_by_id(db, id_loai_phong)
        db.delete(db_type)
        db.commit()

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Float,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship
from src.core.database import Base

class LoaiPhongModel(Base):
    __tablename__ = "loai_phong"

    id_loai_phong = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, nullable=False, index=True)
    ten_loai_phong = Column(String(100), nullable=False)
    mo_ta = Column(Text, nullable=True)
    suc_chua_nguoi_lon = Column(Integer, nullable=False, default=2)
    suc_chua_tre_em = Column(Integer, nullable=False, default=1)
    gia_co_ban_mot_dem = Column(Numeric(18, 2), nullable=False)
    dien_tich_m2 = Column(Float, nullable=True)
    so_luong_phong = Column(Integer, nullable=False, default=0)
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_cap_nhat = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Quan hệ
    phong = relationship(
        "PhongModel",
        back_populates="loai_phong",
        cascade="all, delete-orphan",
    )
    tien_ich = relationship(
        "TienIchPhongModel",
        back_populates="loai_phong",
        cascade="all, delete-orphan",
    )
    quy_tac = relationship(
        "QuyTacPhongModel",
        back_populates="loai_phong",
        cascade="all, delete-orphan",
    )
    khuyen_mai = relationship(
        "KhuyenMaiPhongModel",
        back_populates="loai_phong",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_loai_phong_khach_san", "id_khach_san"),
    )

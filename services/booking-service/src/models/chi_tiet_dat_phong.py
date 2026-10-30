from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class ChiTietDatPhongModel(Base):
    __tablename__ = "chi_tiet_dat_phong"

    id_chi_tiet = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    id_dat_phong = Column(
        Integer,
        ForeignKey(
            "dat_phong.id_dat_phong",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    id_phong = Column(
        Integer,
        nullable=False,
        index=True,
    )

    id_loai_phong = Column(
        Integer,
        nullable=False,
        index=True,
    )

    so_phong = Column(
        String(50),
        nullable=True,
    )

    ten_loai_phong = Column(
        String(100),
        nullable=True,
    )

    gia_tai_thoi_diem_dat = Column(
        Numeric(18, 2),
        nullable=False,
    )

    dat_phong = relationship(
        "DatPhongModel",
        back_populates="chi_tiet",
    )
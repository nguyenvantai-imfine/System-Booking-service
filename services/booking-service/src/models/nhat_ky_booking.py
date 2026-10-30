from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class NhatKyBookingModel(Base):
    __tablename__ = "nhat_ky_trang_thai_booking"

    id_nhat_ky = Column(
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

    trang_thai_cu = Column(
        String(50),
        nullable=True,
    )

    trang_thai_moi = Column(
        String(50),
        nullable=False,
    )

    ly_do = Column(
        String(255),
        nullable=True,
    )

    thoi_gian = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    dat_phong = relationship(
        "DatPhongModel",
        back_populates="nhat_ky",
    )
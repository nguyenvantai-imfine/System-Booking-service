import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Numeric,
    Index,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class TrangThaiBookingEnum(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"


class DatPhongModel(Base):
    __tablename__ = "dat_phong"

    id_dat_phong = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ma_booking = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    id_tai_khoan = Column(
        Integer,
        nullable=False,
    )

    id_khach_san = Column(
        Integer,
        nullable=False,
    )

    ngay_nhan_phong = Column(
        Date,
        nullable=False,
    )

    ngay_tra_phong = Column(
        Date,
        nullable=False,
    )

    tien_phong = Column(
        Numeric(18, 2),
        nullable=True,
        default=0,
    )

    thue_phi = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )

    tong_tien = Column(
        Numeric(18, 2),
        nullable=False,
    )

    trang_thai = Column(
        String(20),
        nullable=False,
        default=TrangThaiBookingEnum.PENDING_PAYMENT.value,
        index=True,
    )

    han_giu_cho = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    ngay_tao = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    ngay_cap_nhat = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Quan hệ với chi tiết đặt phòng
    chi_tiet = relationship(
        "ChiTietDatPhongModel",
        back_populates="dat_phong",
        cascade="all, delete-orphan",
    )

    # Quan hệ với thông tin khách ở
    khach_o = relationship(
        "ThongTinKhachOModel",
        back_populates="dat_phong",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Quan hệ với lịch sử booking
    nhat_ky = relationship(
        "NhatKyBookingModel",
        back_populates="dat_phong",
        cascade="all, delete-orphan",
        order_by="NhatKyBookingModel.id_nhat_ky.asc()",
    )

    __table_args__ = (
        Index(
            "idx_dat_phong_khach_san_ngay",
            "id_khach_san",
            "ngay_nhan_phong",
            "ngay_tra_phong",
        ),
        Index(
            "idx_dat_phong_tai_khoan",
            "id_tai_khoan",
        ),
    )
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index
from sqlalchemy.orm import relationship
from src.core.database import Base

class PhuongThucThanhToanEnum(str, enum.Enum):
    VNPAY = "VNPAY"
    MOMO = "MOMO"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"

class TrangThaiThanhToanEnum(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class ThanhToanModel(Base):
    __tablename__ = "thanh_toan"

    id_thanh_toan = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_dat_phong = Column(Integer, nullable=False, index=True)
    ma_booking = Column(String(50), nullable=False, index=True)
    so_tien = Column(Numeric(18, 2), nullable=False)
    phuong_thuc = Column(
        String(20),
        nullable=False,
        default=PhuongThucThanhToanEnum.VNPAY.value,
    )
    trang_thai = Column(
        String(20),
        nullable=False,
        default=TrangThaiThanhToanEnum.PENDING.value,
        index=True,
    )
    ma_giao_dich_gateway = Column(String(100), unique=True, nullable=False, index=True)
    payment_url = Column(String(500), nullable=True)
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_thanh_toan = Column(DateTime, nullable=True)
    ghi_chu = Column(String(255), nullable=True)

    hoan_tien = relationship(
        "HoanTienModel",
        back_populates="thanh_toan",
        cascade="all, delete-orphan",
    )
    giao_dich_otp = relationship(
        "GiaoDichOtpModel",
        back_populates="thanh_toan",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_thanh_toan_booking", "id_dat_phong", "ma_booking"),
    )

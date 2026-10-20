import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.core.database import Base

class VaiTroEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PARTNER = "PARTNER"
    CUSTOMER = "CUSTOMER"

class TrangThaiTaiKhoanEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    INACTIVE = "INACTIVE"

class TaiKhoanModel(Base):
    __tablename__ = "tai_khoan"

    id_tai_khoan = Column(Integer, primary_key=True, autoincrement=True, index=True)
    ten_dang_nhap = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    sdt = Column(String(20), nullable=True)
    mat_khau_hash = Column(String(255), nullable=False)
    
    vai_tro = Column(
        SQLEnum(VaiTroEnum, native_enum=False),
        nullable=False,
        default=VaiTroEnum.CUSTOMER,
        index=True,
    )
    trang_thai = Column(
        SQLEnum(TrangThaiTaiKhoanEnum, native_enum=False),
        nullable=False,
        default=TrangThaiTaiKhoanEnum.ACTIVE,
        index=True,
    )

    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_cap_nhat = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Quan hệ 1:1 với Profile người dùng
    nguoi_dung = relationship(
        "NguoiDungModel",
        back_populates="tai_khoan",
        uselist=False,
        cascade="all, delete-orphan",
    )

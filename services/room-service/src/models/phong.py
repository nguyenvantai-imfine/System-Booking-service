import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from src.core.database import Base

class TrangThaiPhongEnum(str, enum.Enum):
    AVAILABLE = "AVAILABLE"       # Phòng trống, sẵn sàng đón khách
    OCCUPIED = "OCCUPIED"         # Đang có khách lưu trú
    MAINTENANCE = "MAINTENANCE"   # Đang bảo trì / dọn dẹp
    INACTIVE = "INACTIVE"         # Ngừng kinh doanh

class PhongModel(Base):
    __tablename__ = "phong"

    id_phong = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_loai_phong = Column(
        Integer,
        ForeignKey("loai_phong.id_loai_phong", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_khach_san = Column(Integer, nullable=False, index=True)
    so_phong = Column(String(50), nullable=False)
    tang = Column(Integer, nullable=True, default=1)
    trang_thai = Column(
        String(20),
        nullable=False,
        default=TrangThaiPhongEnum.AVAILABLE.value,
    )
    ghi_chu = Column(String(255), nullable=True)
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_cap_nhat = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Quan hệ
    loai_phong = relationship("LoaiPhongModel", back_populates="phong")

    __table_args__ = (
        UniqueConstraint("id_khach_san", "so_phong", name="uq_phong_khach_san_so_phong"),
        Index("idx_phong_khach_san_trang_thai", "id_khach_san", "trang_thai"),
    )

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class DanhMucTienIchModel(Base):
    __tablename__ = "danh_muc_tien_ich"

    id_danh_muc = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, ForeignKey("khach_san.id_khach_san", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    ten_danh_muc = Column(String(255), nullable=False)
    icon_danh_muc = Column(String(255), nullable=True)

    # Quan hệ ngược lại với bảng khach_san và quan hệ 1:N tới chi tiết tiện ích
    khach_san = relationship("KhachSanModel", back_populates="danh_muc_tien_ich")
    chi_tiet_tien_nghi = relationship("ChiTietTienNghiModel", back_populates="danh_muc", cascade="all, delete-orphan")
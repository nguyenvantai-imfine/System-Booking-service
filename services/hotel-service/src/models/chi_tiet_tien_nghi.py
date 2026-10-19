from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class ChiTietTienNghiModel(Base):
    __tablename__ = "chi_tiet_tien_nghi"

    id_tien_nghi = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_danh_muc = Column(Integer, ForeignKey("danh_muc_tien_ich.id_danh_muc", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    ten_tien_ich = Column(String(255), nullable=False)  # Tên tiện ích cụ thể

    # Quan hệ ngược lại với bảng danh_muc_tien_ich
    danh_muc = relationship("DanhMucTienIchModel", back_populates="chi_tiet_tien_nghi")
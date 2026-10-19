from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class HinhAnhKhachSanModel(Base):
    __tablename__ = "hinh_anh_khach_san"

    id_hinh_anh = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, ForeignKey("khach_san.id_khach_san", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    duong_dan_anh = Column(String(500), nullable=False)  # URL hoặc đường dẫn ảnh
    loai_anh = Column(String(50), nullable=True, default="chung")  # ngoai_canh, sanh, phong_ngu, tien_ich, khac
    la_anh_chinh = Column(Boolean, default=False, nullable=False)   # True nếu là ảnh đại diện hiển thị ngoài danh sách
    thu_tu = Column(Integer, default=0, nullable=False)             # Thứ tự hiển thị ảnh
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Quan hệ ngược lại với bảng khach_san
    khach_san = relationship("KhachSanModel", back_populates="hinh_anh")

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class ThongTinKhachSanModel(Base):
    __tablename__ = "thong_tin_khach_san"

    id_thong_tin = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, ForeignKey("khach_san.id_khach_san", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    loai_thong_tin = Column(String(255), nullable=False)
    noi_dung = Column(Text, nullable=True)

    # Thiết lập quan hệ N:1 với bảng KhachSanModel
    khach_san = relationship("KhachSanModel", back_populates="thong_tin")
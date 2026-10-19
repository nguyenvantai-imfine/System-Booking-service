from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class QuyTacKhachSanModel(Base):
    __tablename__ = "quy_tac_khach_san"

    id_quy_tac = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, ForeignKey("khach_san.id_khach_san", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    ten = Column(String(255), nullable=False)
    gia_tri_chon = Column(String(255), nullable=True)  # Thêm trường Giá trị chọn theo sơ đồ mới
    mo_ta = Column(Text, nullable=True)

    # Quan hệ ngược lại với bảng khach_san
    khach_san = relationship("KhachSanModel", back_populates="quy_tac")
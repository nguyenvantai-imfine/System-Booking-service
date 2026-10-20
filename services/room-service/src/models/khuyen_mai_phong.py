from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class KhuyenMaiPhongModel(Base):
    __tablename__ = "khuyen_mai_phong"

    id_khuyen_mai = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_loai_phong = Column(
        Integer,
        ForeignKey("loai_phong.id_loai_phong", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ma_khuyen_mai = Column(String(50), nullable=False)
    ngay_bat_dau = Column(Date, nullable=False)
    ngay_ket_thuc = Column(Date, nullable=False)
    phan_tram_giam = Column(Float, nullable=False)  # ví dụ 15.0 nghĩa là giảm 15%
    mo_ta = Column(String(255), nullable=True)

    loai_phong = relationship("LoaiPhongModel", back_populates="khuyen_mai")

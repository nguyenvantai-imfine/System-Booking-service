from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class TienIchPhongModel(Base):
    __tablename__ = "tien_ich_phong"

    id_tien_ich = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_loai_phong = Column(
        Integer,
        ForeignKey("loai_phong.id_loai_phong", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ten_tien_ich = Column(String(100), nullable=False)
    bieu_tuong = Column(String(100), nullable=True)  # wifi, bath, air-vent, tv, coffee...

    loai_phong = relationship("LoaiPhongModel", back_populates="tien_ich")

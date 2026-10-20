from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class QuyTacPhongModel(Base):
    __tablename__ = "quy_tac_phong"

    id_quy_tac = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_loai_phong = Column(
        Integer,
        ForeignKey("loai_phong.id_loai_phong", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tieu_de = Column(String(150), nullable=False)  # Hút thuốc, Thú cưng, Giờ yên lặng...
    cho_phep = Column(Boolean, default=False, nullable=False)
    ghi_chu = Column(String(255), nullable=True)

    loai_phong = relationship("LoaiPhongModel", back_populates="quy_tac")

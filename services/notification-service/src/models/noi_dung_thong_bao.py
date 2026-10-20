from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class NoiDungThongBaoModel(Base):
    __tablename__ = "noi_dung_thong_bao"

    id_noi_dung = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_thong_bao = Column(Integer, ForeignKey("thong_bao.id_thong_bao", ondelete="CASCADE"), nullable=False, unique=True)
    tieu_de = Column(String(255), nullable=False)
    noi_dung_html = Column(Text, nullable=False)
    noi_dung_text = Column(Text, nullable=True)
    du_lieu_dinh_kem = Column(Text, nullable=True) # JSON raw data

    thong_bao = relationship("ThongBaoModel", back_populates="noi_dung")

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class ThongTinKhachOModel(Base):
    __tablename__ = "thong_tin_khach_o"

    id_khach_o = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_dat_phong = Column(
        Integer,
        ForeignKey("dat_phong.id_dat_phong", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    ho_ten = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    sdt = Column(String(20), nullable=False)
    ghi_chu_dac_biet = Column(Text, nullable=True)

    dat_phong = relationship("DatPhongModel", back_populates="khach_o")

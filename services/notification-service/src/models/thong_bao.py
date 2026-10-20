from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class ThongBaoModel(Base):
    __tablename__ = "thong_bao"

    id_thong_bao = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_tai_khoan = Column(Integer, nullable=True)
    loai_thong_bao = Column(String(50), nullable=False, index=True) # BOOKING_CONFIRMED, PAYMENT_SUCCESS, BOOKING_CANCELLED, SYSTEM
    kenh_gui = Column(String(20), nullable=False, default="EMAIL") # EMAIL, SMS, IN_APP
    nguoi_nhan = Column(String(150), nullable=False, index=True) # Email or Phone
    trang_thai = Column(String(30), nullable=False, default="PENDING", index=True) # SENT, FAILED, PENDING
    ma_booking = Column(String(50), nullable=True, index=True)
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_gui = Column(DateTime, nullable=True)
    ghi_chu_loi = Column(Text, nullable=True)

    noi_dung = relationship("NoiDungThongBaoModel", back_populates="thong_bao", uselist=False, cascade="all, delete-orphan")

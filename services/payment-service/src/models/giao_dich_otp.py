from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.core.database import Base

class GiaoDichOtpModel(Base):
    __tablename__ = "giao_dich_otp"

    id_otp = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_giao_dich_gateway = Column(
        String(100),
        ForeignKey("thanh_toan.ma_giao_dich_gateway", ondelete="CASCADE"),
        nullable=False,
    )
    email = Column(String(150), nullable=False)
    otp_code = Column(String(6), nullable=False)
    thoi_gian_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    thoi_gian_het_han = Column(DateTime, nullable=False)
    da_su_dung = Column(Boolean, default=False, nullable=False)
    so_lan_thu = Column(Integer, default=0, nullable=False)

    thanh_toan = relationship("ThanhToanModel", back_populates="giao_dich_otp")

    __table_args__ = (
        Index("idx_otp_txn", "ma_giao_dich_gateway"),
    )

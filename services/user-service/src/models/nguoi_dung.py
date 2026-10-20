from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class NguoiDungModel(Base):
    __tablename__ = "nguoi_dung"

    id_nguoi_dung = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_tai_khoan = Column(
        Integer,
        ForeignKey("tai_khoan.id_tai_khoan", ondelete="CASCADE", onupdate="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    ho = Column(String(50), nullable=True)
    ten = Column(String(50), nullable=True)
    ngay_sinh = Column(Date, nullable=True)
    gioi_tinh = Column(String(10), nullable=True) # Nam, Nữ, Khác
    dia_chi = Column(String(255), nullable=True)
    avatar = Column(String(500), nullable=True)
    cccd = Column(String(20), nullable=True)

    ngay_cap_nhat = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Quan hệ ngược về Tài khoản
    tai_khoan = relationship("TaiKhoanModel", back_populates="nguoi_dung")

    @property
    def ho_va_ten(self) -> str:
        parts = [self.ho, self.ten]
        return " ".join([p for p in parts if p]) or "Chưa đặt tên"

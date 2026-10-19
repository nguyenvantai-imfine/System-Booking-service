from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.core.database import Base

class KhachSanModel(Base):
    __tablename__ = "khach_san"

    id_khach_san = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_tai_khoan = Column(Integer, nullable=False)  # Liên kết với user-service (id tài khoản của partner)
    ten_khach_san = Column(String(255), nullable=False)
    email_khach_san = Column(String(100), nullable=True)
    sdt_khach_san = Column(String(20), nullable=True)
    trang_thai = Column(String(50), nullable=True)
    dia_chi = Column(String(255), nullable=True)
    thanh_pho = Column(String(100), nullable=True)
    tinh = Column(String(100), nullable=True)

    # Thiết lập quan hệ 1:N với các bảng liên quan (giúp truy vấn dữ liệu dễ dàng hơn sau này)
    thong_tin = relationship("ThongTinKhachSanModel", back_populates="khach_san", cascade="all, delete-orphan")
    quy_tac = relationship("QuyTacKhachSanModel", back_populates="khach_san", cascade="all, delete-orphan")
    danh_muc_tien_ich = relationship("DanhMucTienIchModel", back_populates="khach_san", cascade="all, delete-orphan")
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from src.core.database import Base

class TrangThaiKhachSan(str, enum.Enum):
    HOAT_DONG = "HOAT_DONG"          # Đang mở cửa đón khách bình thường
    TAM_DUNG = "TAM_DUNG"            # Tạm ngừng kinh doanh (sửa chữa, dịch bệnh...)
    CHO_DUYET = "CHO_DUYET"          # Đăng ký mới, đang chờ Admin phê duyệt
    DA_XOA = "DA_XOA"                # Đã bị xóa (Soft Deleted)

class KhachSanModel(Base):
    __tablename__ = "khach_san"

    id_khach_san = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_tai_khoan = Column(Integer, nullable=False, index=True)  # ID Partner từ user-service
    ten_khach_san = Column(String(255), nullable=False, index=True)
    email_khach_san = Column(String(100), nullable=True)
    sdt_khach_san = Column(String(20), nullable=True)
    
    # Trạng thái kinh doanh chuẩn hóa qua Enum
    trang_thai = Column(
        Enum(TrangThaiKhachSan, name="trang_thai_khach_san_enum", native_enum=False),
        nullable=False,
        default=TrangThaiKhachSan.HOAT_DONG,
        index=True
    )
    
    # Quản lý địa chỉ chi tiết và tọa độ địa lý
    dia_chi = Column(String(255), nullable=True)
    phuong_xa = Column(String(100), nullable=True)
    quan_huyen = Column(String(100), nullable=True, index=True)
    thanh_pho = Column(String(100), nullable=True, index=True)
    tinh = Column(String(100), nullable=True, index=True)
    quoc_gia = Column(String(100), nullable=True, default="Việt Nam")
    kinh_do = Column(Float, nullable=True)   # Longitude
    vi_do = Column(Float, nullable=True)     # Latitude
    ma_buu_chinh = Column(String(20), nullable=True)

    # Thông tin người quản lý / liên hệ đại diện của khách sạn
    ten_nguoi_lien_he = Column(String(100), nullable=True)
    sdt_nguoi_lien_he = Column(String(20), nullable=True)

    # Quản lý mốc thời gian (Audit timestamps)
    ngay_tao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ngay_cap_nhat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft Delete Pattern
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Thiết lập quan hệ 1:N với các bảng liên quan
    hinh_anh = relationship("HinhAnhKhachSanModel", back_populates="khach_san", cascade="all, delete-orphan", order_by="HinhAnhKhachSanModel.thu_tu")
    thong_tin = relationship("ThongTinKhachSanModel", back_populates="khach_san", cascade="all, delete-orphan")
    quy_tac = relationship("QuyTacKhachSanModel", back_populates="khach_san", cascade="all, delete-orphan")
    danh_muc_tien_ich = relationship("DanhMucTienIchModel", back_populates="khach_san", cascade="all, delete-orphan")
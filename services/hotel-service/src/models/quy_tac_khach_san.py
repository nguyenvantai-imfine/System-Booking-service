import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.core.database import Base

class LoaiChinhSach(str, enum.Enum):
    CHECK_IN_OUT = "CHECK_IN_OUT"        # Giờ nhận phòng, giờ trả phòng
    HUY_PHONG = "HUY_PHONG"              # Chính sách hủy đặt phòng và hoàn tiền
    TRE_EM = "TRE_EM"                    # Chính sách trẻ em, độ tuổi và giường phụ
    DAT_COC = "DAT_COC"                  # Quy định thanh toán / đặt cọc trước
    QUY_DINH_CHUNG = "QUY_DINH_CHUNG"    # Thú cưng, hút thuốc, tổ chức tiệc tùng

class QuyTacKhachSanModel(Base):
    __tablename__ = "quy_tac_khach_san"

    id_quy_tac = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_khach_san = Column(Integer, ForeignKey("khach_san.id_khach_san", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # Phân loại chính sách qua Enum
    loai_chinh_sach = Column(
        Enum(LoaiChinhSach, name="loai_chinh_sach_enum", native_enum=False),
        nullable=False,
        default=LoaiChinhSach.QUY_DINH_CHUNG,
        index=True
    )
    ten = Column(String(255), nullable=False)
    gia_tri_chon = Column(String(255), nullable=True)  # Ví dụ: '14:00', '12:00', 'Không cho phép'
    mo_ta = Column(Text, nullable=True)

    # Quan hệ ngược lại với bảng khach_san
    khach_san = relationship("KhachSanModel", back_populates="quy_tac")
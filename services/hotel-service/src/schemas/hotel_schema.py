import re
from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from src.models.khach_san import TrangThaiKhachSan
from src.models.quy_tac_khach_san import LoaiChinhSach

T = TypeVar("T")

# ==============================================================================
# 0. SCHEMA PHÂN TRANG CHUẨN (GENERIC PAGINATED RESPONSE)
# ==============================================================================
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="Danh sách các phần tử của trang hiện tại")
    total: int = Field(..., ge=0, description="Tổng số bản ghi tìm thấy trong hệ thống")
    page: int = Field(..., ge=1, description="Trang hiện tại (bắt đầu từ 1)")
    page_size: int = Field(..., ge=1, description="Số lượng bản ghi trên một trang")
    total_pages: int = Field(..., ge=0, description="Tổng số trang")


# ==============================================================================
# 1. SCHEMAS CHO HÌNH ẢNH KHÁCH SẠN (hinh_anh_khach_san)
# ==============================================================================
class HinhAnhBase(BaseModel):
    duong_dan_anh: str = Field(..., max_length=500, description="URL hoặc đường dẫn ảnh")
    loai_anh: Optional[str] = Field("chung", max_length=50, description="Phân loại: ngoai_canh, sanh, phong_ngu, tien_ich, chung")
    la_anh_chinh: bool = Field(False, description="True nếu là ảnh đại diện hiển thị danh sách")
    thu_tu: int = Field(0, ge=0, description="Thứ tự ưu tiên hiển thị (0 là đầu tiên)")

class HinhAnhCreate(HinhAnhBase):
    pass

class HinhAnhUpdate(BaseModel):
    duong_dan_anh: Optional[str] = Field(None, max_length=500)
    loai_anh: Optional[str] = Field(None, max_length=50)
    la_anh_chinh: Optional[bool] = None
    thu_tu: Optional[int] = Field(None, ge=0)

class HinhAnhResponse(HinhAnhBase):
    id_hinh_anh: int
    id_khach_san: int
    ngay_tao: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. SCHEMAS CHO CHI TIẾT CÁC TIỆN NGHI (chi_tiet_tien_nghi)
# ==============================================================================
class ChiTietTienNghiBase(BaseModel):
    ten_tien_ich: str = Field(..., min_length=1, max_length=255, description="Tên tiện ích cụ thể (ví dụ: Wifi miễn phí, Bể bơi vô cực)")

class ChiTietTienNghiCreate(ChiTietTienNghiBase):
    pass

class ChiTietTienNghiUpdate(BaseModel):
    ten_tien_ich: Optional[str] = Field(None, min_length=1, max_length=255)

class ChiTietTienNghiResponse(ChiTietTienNghiBase):
    id_tien_nghi: int
    id_danh_muc: int

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. SCHEMAS CHO DANH MỤC TIỆN ÍCH (danh_muc_tien_ich)
# ==============================================================================
class DanhMucTienIchBase(BaseModel):
    ten_danh_muc: str = Field(..., min_length=1, max_length=255, description="Tên nhóm danh mục (ví dụ: Tiện nghi phòng, Giải trí & Thể thao)")
    icon_danh_muc: Optional[str] = Field(None, max_length=255, description="Icon class hoặc URL icon")

class DanhMucTienIchCreate(DanhMucTienIchBase):
    chi_tiet_tien_nghi: Optional[List[ChiTietTienNghiCreate]] = []

class DanhMucTienIchUpdate(BaseModel):
    ten_danh_muc: Optional[str] = Field(None, min_length=1, max_length=255)
    icon_danh_muc: Optional[str] = Field(None, max_length=255)

class DanhMucTienIchResponse(DanhMucTienIchBase):
    id_danh_muc: int
    id_khach_san: int
    chi_tiet_tien_nghi: List[ChiTietTienNghiResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 4. SCHEMAS CHO THÔNG TIN KHÁCH SẠN (thong_tin_khach_san)
# ==============================================================================
class ThongTinKhachSanBase(BaseModel):
    loai_thong_tin: str = Field(..., min_length=1, max_length=255, description="Loại thông tin (ví dụ: Giới thiệu chung, Hướng dẫn nhận phòng)")
    noi_dung: Optional[str] = Field(None, description="Nội dung chi tiết")

class ThongTinKhachSanCreate(ThongTinKhachSanBase):
    pass

class ThongTinKhachSanUpdate(BaseModel):
    loai_thong_tin: Optional[str] = Field(None, min_length=1, max_length=255)
    noi_dung: Optional[str] = None

class ThongTinKhachSanResponse(ThongTinKhachSanBase):
    id_thong_tin: int
    id_khach_san: int

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 5. SCHEMAS CHO QUY TẮC & CHÍNH SÁCH KHÁCH SẠN (quy_tac_khach_san)
# ==============================================================================
class QuyTacKhachSanBase(BaseModel):
    loai_chinh_sach: LoaiChinhSach = Field(
        default=LoaiChinhSach.QUY_DINH_CHUNG,
        description="Phân loại: CHECK_IN_OUT, HUY_PHONG, TRE_EM, DAT_COC, QUY_DINH_CHUNG"
    )
    ten: str = Field(..., min_length=1, max_length=255, description="Tên chính sách (ví dụ: Giờ nhận phòng, Quy định thú cưng)")
    gia_tri_chon: Optional[str] = Field(None, max_length=255, description="Giá trị ngắn gọn (ví dụ: 14:00, Cho phép, Không hoàn tiền)")
    mo_ta: Optional[str] = Field(None, description="Mô tả chi tiết nội dung chính sách")

class QuyTacKhachSanCreate(QuyTacKhachSanBase):
    pass

class QuyTacKhachSanUpdate(BaseModel):
    loai_chinh_sach: Optional[LoaiChinhSach] = None
    ten: Optional[str] = Field(None, min_length=1, max_length=255)
    gia_tri_chon: Optional[str] = Field(None, max_length=255)
    mo_ta: Optional[str] = None

class QuyTacKhachSanResponse(QuyTacKhachSanBase):
    id_quy_tac: int
    id_khach_san: int

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 6. SCHEMAS CHÍNH CHO KHÁCH SẠN (khach_san)
# ==============================================================================
class KhachSanStatusUpdate(BaseModel):
    """Schema dùng riêng cho PATCH /{id}/status"""
    trang_thai: TrangThaiKhachSan = Field(
        ...,
        description="Trạng thái mới: HOAT_DONG | TAM_DUNG | CHO_DUYET (không cho phép DA_XOA)",
    )


class KhachSanBase(BaseModel):
    id_tai_khoan: int = Field(..., description="ID tài khoản Partner sở hữu khách sạn")
    ten_khach_san: str = Field(..., min_length=2, max_length=255, description="Tên khách sạn")
    email_khach_san: Optional[EmailStr] = Field(None, description="Email liên hệ khách sạn")
    sdt_khach_san: Optional[str] = Field(None, max_length=20, description="SĐT bàn hoặc hotline")
    trang_thai: TrangThaiKhachSan = Field(default=TrangThaiKhachSan.HOAT_DONG, description="Trạng thái kinh doanh")

    # Quản lý địa chỉ chi tiết & Tọa độ bản đồ
    dia_chi: Optional[str] = Field(None, max_length=255, description="Số nhà, tên đường")
    phuong_xa: Optional[str] = Field(None, max_length=100, description="Phường / Xã")
    quan_huyen: Optional[str] = Field(None, max_length=100, description="Quận / Huyện")
    thanh_pho: Optional[str] = Field(None, max_length=100, description="Thành phố")
    tinh: Optional[str] = Field(None, max_length=100, description="Tỉnh")
    quoc_gia: Optional[str] = Field("Việt Nam", max_length=100, description="Quốc gia")
    kinh_do: Optional[float] = Field(None, description="Kinh độ (Longitude)")
    vi_do: Optional[float] = Field(None, description="Vĩ độ (Latitude)")
    ma_buu_chinh: Optional[str] = Field(None, max_length=20, description="Mã bưu chính / Postal Code")

    # Thông tin người liên hệ đại diện của khách sạn
    ten_nguoi_lien_he: Optional[str] = Field(None, max_length=100, description="Họ tên người quản lý/đại diện")
    sdt_nguoi_lien_he: Optional[str] = Field(None, max_length=20, description="SĐT di động người quản lý")

    @field_validator("sdt_khach_san", "sdt_nguoi_lien_he", mode="before")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_clean = str(v).strip().replace(" ", "").replace(".", "").replace("-", "")
        # Cho phép định dạng điện thoại VN: 10 chữ số (bắt đầu bằng 0) hoặc đầu số quốc tế +84
        if not re.match(r"^(0|\+84)[0-9]{9}$", v_clean):
            raise ValueError("Số điện thoại không hợp lệ (yêu cầu 10 chữ số, ví dụ: 0912345678 hoặc +84912345678)")
        return v_clean


class KhachSanCreate(KhachSanBase):
    # Cho phép gửi kèm các dữ liệu con để tạo khách sạn hoàn chỉnh trong 1 request
    hinh_anh: Optional[List[HinhAnhCreate]] = Field(default=[], description="Danh sách hình ảnh kèm theo")
    thong_tin: Optional[List[ThongTinKhachSanCreate]] = Field(default=[], description="Danh sách thông tin phụ")
    quy_tac: Optional[List[QuyTacKhachSanCreate]] = Field(default=[], description="Danh sách quy tắc / chính sách")
    danh_muc_tien_ich: Optional[List[DanhMucTienIchCreate]] = Field(default=[], description="Danh sách tiện nghi")


class KhachSanUpdate(BaseModel):
    id_tai_khoan: Optional[int] = None
    ten_khach_san: Optional[str] = Field(None, min_length=2, max_length=255)
    email_khach_san: Optional[EmailStr] = None
    sdt_khach_san: Optional[str] = Field(None, max_length=20)
    trang_thai: Optional[TrangThaiKhachSan] = None
    
    dia_chi: Optional[str] = Field(None, max_length=255)
    phuong_xa: Optional[str] = Field(None, max_length=100)
    quan_huyen: Optional[str] = Field(None, max_length=100)
    thanh_pho: Optional[str] = Field(None, max_length=100)
    tinh: Optional[str] = Field(None, max_length=100)
    quoc_gia: Optional[str] = Field(None, max_length=100)
    kinh_do: Optional[float] = None
    vi_do: Optional[float] = None
    ma_buu_chinh: Optional[str] = Field(None, max_length=20)

    ten_nguoi_lien_he: Optional[str] = Field(None, max_length=100)
    sdt_nguoi_lien_he: Optional[str] = Field(None, max_length=20)

    @field_validator("sdt_khach_san", "sdt_nguoi_lien_he", mode="before")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_clean = str(v).strip().replace(" ", "").replace(".", "").replace("-", "")
        if not re.match(r"^(0|\+84)[0-9]{9}$", v_clean):
            raise ValueError("Số điện thoại không hợp lệ (yêu cầu 10 chữ số, ví dụ: 0912345678 hoặc +84912345678)")
        return v_clean


# ------------------------------------------------------------------------------
# 6.1 RESPONSE GỌN NHẸ (BRIEF): Dùng cho Xem danh sách & Tìm kiếm (Tối ưu tốc độ & Payload)
# ------------------------------------------------------------------------------
class KhachSanBriefResponse(BaseModel):
    id_khach_san: int
    id_tai_khoan: int
    ten_khach_san: str
    email_khach_san: Optional[str] = None
    sdt_khach_san: Optional[str] = None
    trang_thai: TrangThaiKhachSan
    dia_chi: Optional[str] = None
    phuong_xa: Optional[str] = None
    quan_huyen: Optional[str] = None
    thanh_pho: Optional[str] = None
    tinh: Optional[str] = None
    quoc_gia: Optional[str] = None
    kinh_do: Optional[float] = None
    vi_do: Optional[float] = None
    
    # Ảnh đại diện chính trích xuất nhanh
    anh_dai_dien: Optional[str] = Field(None, description="URL ảnh chính của khách sạn")
    
    is_deleted: bool = False
    ngay_tao: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# 6.2 RESPONSE ĐẦY ĐỦ (DETAIL): Dùng cho Trang Chi Tiết Khách Sạn (Nạp sâu quan hệ)
# ------------------------------------------------------------------------------
class KhachSanDetailResponse(KhachSanBase):
    id_khach_san: int
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    ngay_tao: datetime
    ngay_cap_nhat: datetime

    hinh_anh: List[HinhAnhResponse] = []
    thong_tin: List[ThongTinKhachSanResponse] = []
    quy_tac: List[QuyTacKhachSanResponse] = []
    danh_muc_tien_ich: List[DanhMucTienIchResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Alias backward compatibility cho code cũ
KhachSanResponse = KhachSanDetailResponse

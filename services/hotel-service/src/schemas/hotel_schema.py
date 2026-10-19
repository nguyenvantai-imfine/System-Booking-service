from typing import List, Optional
from pydantic import BaseModel, EmailStr

# 1. SCHEMAS CHO CHI TIẾT CÁC TIỆN NGHI (chi_tiet_tien_nghi)
class ChiTietTienNghiBase(BaseModel):
    ten_tien_ich: str

class ChiTietTienNghiCreate(ChiTietTienNghiBase):
    pass

class ChiTietTienNghiUpdate(BaseModel):
    ten_tien_ich: Optional[str] = None

class ChiTietTienNghiResponse(ChiTietTienNghiBase):
    id_tien_nghi: int
    id_danh_muc: int

    class Config:
        from_attributes = True


# 2. SCHEMAS CHO DANH MỤC TIỆN ÍCH (danh_muc_tien_ich)
class DanhMucTienIchBase(BaseModel):
    ten_danh_muc: str
    icon_danh_muc: Optional[str] = None

class DanhMucTienIchCreate(DanhMucTienIchBase):
    # Cho phép truyền danh sách chi tiết tiện nghi khi tạo danh mục
    chi_tiet_tien_nghi: Optional[List[ChiTietTienNghiCreate]] = []

class DanhMucTienIchUpdate(BaseModel):
    ten_danh_muc: Optional[str] = None
    icon_danh_muc: Optional[str] = None

class DanhMucTienIchResponse(DanhMucTienIchBase):
    id_danh_muc: int
    id_khach_san: int
    chi_tiet_tien_nghi: List[ChiTietTienNghiResponse] = []

    class Config:
        from_attributes = True


# 3. SCHEMAS CHO THÔNG TIN KHÁCH SẠN (thong_tin_khach_san)
class ThongTinKhachSanBase(BaseModel):
    loai_thong_tin: str
    noi_dung: Optional[str] = None

class ThongTinKhachSanCreate(ThongTinKhachSanBase):
    pass

class ThongTinKhachSanUpdate(BaseModel):
    loai_thong_tin: Optional[str] = None
    noi_dung: Optional[str] = None

class ThongTinKhachSanResponse(ThongTinKhachSanBase):
    id_thong_tin: int
    id_khach_san: int

    class Config:
        from_attributes = True


# 4. SCHEMAS CHO QUY TẮC KHÁCH SẠN (quy_tac_khach_san)
class QuyTacKhachSanBase(BaseModel):
    ten: str
    gia_tri_chon: Optional[str] = None
    mo_ta: Optional[str] = None

class QuyTacKhachSanCreate(QuyTacKhachSanBase):
    pass

class QuyTacKhachSanUpdate(BaseModel):
    ten: Optional[str] = None
    gia_tri_chon: Optional[str] = None
    mo_ta: Optional[str] = None

class QuyTacKhachSanResponse(QuyTacKhachSanBase):
    id_quy_tac: int
    id_khach_san: int

    class Config:
        from_attributes = True


# 5. SCHEMAS CHÍNH CHO KHÁCH SẠN (khach_san)
class KhachSanBase(BaseModel):
    id_tai_khoan: int
    ten_khach_san: str
    email_khach_san: Optional[EmailStr] = None
    sdt_khach_san: Optional[str] = None
    trang_thai: Optional[str] = "Hoạt động"
    dia_chi: Optional[str] = None
    thanh_pho: Optional[str] = None
    tinh: Optional[str] = None

class KhachSanCreate(KhachSanBase):
    # Cho phép gửi kèm các thông tin con khi khởi tạo một khách sạn mới
    thong_tin: Optional[List[ThongTinKhachSanCreate]] = []
    quy_tac: Optional[List[QuyTacKhachSanCreate]] = []
    danh_muc_tien_ich: Optional[List[DanhMucTienIchCreate]] = []

class KhachSanUpdate(BaseModel):
    id_tai_khoan: Optional[int] = None
    ten_khach_san: Optional[str] = None
    email_khach_san: Optional[EmailStr] = None
    sdt_khach_san: Optional[str] = None
    trang_thai: Optional[str] = None
    dia_chi: Optional[str] = None
    thanh_pho: Optional[str] = None
    tinh: Optional[str] = None

class KhachSanResponse(KhachSanBase):
    id_khach_san: int
    thong_tin: List[ThongTinKhachSanResponse] = []
    quy_tac: List[QuyTacKhachSanResponse] = []
    danh_muc_tien_ich: List[DanhMucTienIchResponse] = []

    class Config:
        from_attributes = True

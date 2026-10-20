from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Tien Ich
class TienIchBase(BaseModel):
    ten_tien_ich: str = Field(..., min_length=1, max_length=100)
    bieu_tuong: Optional[str] = Field(None, max_length=100)

class TienIchCreate(TienIchBase):
    pass

class TienIchResponse(TienIchBase):
    id_tien_ich: int
    id_loai_phong: int

    model_config = ConfigDict(from_attributes=True)

# Quy Tac
class QuyTacBase(BaseModel):
    tieu_de: str = Field(..., min_length=1, max_length=150)
    cho_phep: bool = False
    ghi_chu: Optional[str] = Field(None, max_length=255)

class QuyTacCreate(QuyTacBase):
    pass

class QuyTacResponse(QuyTacBase):
    id_quy_tac: int
    id_loai_phong: int

    model_config = ConfigDict(from_attributes=True)

# Khuyen Mai
class KhuyenMaiBase(BaseModel):
    ma_khuyen_mai: str = Field(..., min_length=1, max_length=50)
    ngay_bat_dau: date
    ngay_ket_thuc: date
    phan_tram_giam: float = Field(..., ge=0, le=100)
    mo_ta: Optional[str] = Field(None, max_length=255)

class KhuyenMaiCreate(KhuyenMaiBase):
    pass

class KhuyenMaiResponse(KhuyenMaiBase):
    id_khuyen_mai: int
    id_loai_phong: int

    model_config = ConfigDict(from_attributes=True)

# Loai Phong
class LoaiPhongBase(BaseModel):
    ten_loai_phong: str = Field(..., min_length=2, max_length=100)
    mo_ta: Optional[str] = None
    suc_chua_nguoi_lon: int = Field(2, ge=1)
    suc_chua_tre_em: int = Field(1, ge=0)
    gia_co_ban_mot_dem: float = Field(..., gt=0)
    dien_tich_m2: Optional[float] = Field(None, gt=0)

class LoaiPhongCreate(LoaiPhongBase):
    tien_ich: Optional[List[TienIchCreate]] = []
    quy_tac: Optional[List[QuyTacCreate]] = []
    khuyen_mai: Optional[List[KhuyenMaiCreate]] = []

class LoaiPhongUpdate(BaseModel):
    ten_loai_phong: Optional[str] = Field(None, min_length=2, max_length=100)
    mo_ta: Optional[str] = None
    suc_chua_nguoi_lon: Optional[int] = Field(None, ge=1)
    suc_chua_tre_em: Optional[int] = Field(None, ge=0)
    gia_co_ban_mot_dem: Optional[float] = Field(None, gt=0)
    dien_tich_m2: Optional[float] = Field(None, gt=0)

class LoaiPhongBriefResponse(LoaiPhongBase):
    id_loai_phong: int
    id_khach_san: int
    so_luong_phong: int

    model_config = ConfigDict(from_attributes=True)

class LoaiPhongResponse(LoaiPhongBase):
    id_loai_phong: int
    id_khach_san: int
    so_luong_phong: int
    ngay_tao: datetime
    ngay_cap_nhat: datetime
    tien_ich: List[TienIchResponse] = []
    quy_tac: List[QuyTacResponse] = []
    khuyen_mai: List[KhuyenMaiResponse] = []

    model_config = ConfigDict(from_attributes=True)

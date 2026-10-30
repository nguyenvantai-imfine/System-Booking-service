
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
)

from src.models.dat_phong import TrangThaiBookingEnum


# =========================================================
# 1. THONG TIN KHACH O
# =========================================================

class ThongTinKhachOBase(BaseModel):

    ho_ten: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    sdt: str = Field(..., min_length=6, max_length=20)
    ghi_chu_dac_biet: Optional[str] = Field(
        None,
        max_length=500,
    )

    @field_validator("ho_ten")
    @classmethod
    def validate_ho_ten(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Ho ten phai co it nhat 2 ky tu."
            )

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("sdt")
    @classmethod
    def validate_sdt(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "So dien thoai khong duoc de trong."
            )

        allowed_chars = set("0123456789+-() ")

        if any(char not in allowed_chars for char in value):
            raise ValueError(
                "So dien thoai chua ky tu khong hop le."
            )

        digit_count = sum(char.isdigit() for char in value)

        if digit_count < 6:
            raise ValueError(
                "So dien thoai phai co it nhat 6 chu so."
            )

        return value

    @field_validator("ghi_chu_dac_biet")
    @classmethod
    def normalize_note(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class ThongTinKhachOCreate(ThongTinKhachOBase):
    pass


class ThongTinKhachOResponse(ThongTinKhachOBase):

    id_khach_o: int
    id_dat_phong: int

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 2. CHI TIET PHONG DAT
# =========================================================

class ChiTietDatPhongCreate(BaseModel):

    id_phong: int = Field(..., ge=1)
    id_loai_phong: int = Field(..., ge=1)

    so_phong: Optional[str] = Field(
        None,
        max_length=50,
    )

    ten_loai_phong: Optional[str] = Field(
        None,
        max_length=100,
    )

    gia: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=2,
        description="Gia mot dem tai thoi diem dat",
    )

    @field_validator("gia")
    @classmethod
    def validate_gia(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value <= 0:
            raise ValueError(
                "Gia phong phai la so duong hop le."
            )

        return value

    @field_validator("so_phong", "ten_loai_phong")
    @classmethod
    def normalize_room_text(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class ChiTietDatPhongResponse(BaseModel):

    id_chi_tiet: int
    id_dat_phong: int
    id_phong: int
    id_loai_phong: int

    so_phong: Optional[str] = None
    ten_loai_phong: Optional[str] = None

    gia_tai_thoi_diem_dat: Decimal

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 3. NHAT KY BOOKING
# =========================================================

class NhatKyBookingResponse(BaseModel):

    id_nhat_ky: int
    trang_thai_cu: Optional[str] = None
    trang_thai_moi: str
    ly_do: Optional[str] = None
    thoi_gian: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 4. YEU CAU TAO BOOKING
# =========================================================

class BookingCreateRequest(BaseModel):

    id_khach_san: int = Field(..., ge=1)

    ngay_nhan_phong: date
    ngay_tra_phong: date

    rooms: List[ChiTietDatPhongCreate] = Field(
        ...,
        min_length=1,
    )

    khach_o: ThongTinKhachOCreate

    id_tai_khoan: Optional[int] = Field(
        None,
        ge=1,
        description="Chi ADMIN moi duoc chi dinh tai khoan khac",
    )

    @model_validator(mode="after")
    def validate_booking_data(self):

        if self.ngay_nhan_phong < date.today():
            raise ValueError(
                "Ngay nhan phong khong duoc nam trong qua khu."
            )

        if self.ngay_nhan_phong >= self.ngay_tra_phong:
            raise ValueError(
                "Ngay nhan phong phai truoc ngay tra phong."
            )

        if not self.rooms:
            raise ValueError(
                "Don dat phong phai co it nhat mot phong."
            )

        room_ids = [
            room.id_phong
            for room in self.rooms
        ]

        if len(room_ids) != len(set(room_ids)):
            raise ValueError(
                "Mot phong khong the xuat hien nhieu lan "
                "trong cung yeu cau dat phong."
            )

        return self


# =========================================================
# 5. PHAN HOI BOOKING
# =========================================================

class BookingResponse(BaseModel):

    id_dat_phong: int
    ma_booking: str
    id_tai_khoan: int
    id_khach_san: int

    ngay_nhan_phong: date
    ngay_tra_phong: date

    tien_phong: Optional[Decimal] = Field(
        None,
        description="Tong tien phong truoc thue va phi",
    )

    thue_phi: Decimal = Field(
        Decimal("0.00"),
        description="Thue va phi VAT 10%",
    )

    tong_tien: Decimal

    trang_thai: TrangThaiBookingEnum

    han_giu_cho: Optional[datetime] = None
    ngay_tao: datetime
    ngay_cap_nhat: datetime

    chi_tiet: List[ChiTietDatPhongResponse] = Field(
        default_factory=list,
    )

    khach_o: Optional[ThongTinKhachOResponse] = None

    nhat_ky: List[NhatKyBookingResponse] = Field(
        default_factory=list,
    )

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def ensure_tax_and_room_amount(self):

        if self.tien_phong is None:
            self.tien_phong = (
                self.tong_tien - self.thue_phi
            ).quantize(Decimal("0.01"))

        return self


# =========================================================
# 6. DANH SACH BOOKING PHAN TRANG
# =========================================================

class BookingPaginatedResponse(BaseModel):

    items: List[BookingResponse] = Field(
        default_factory=list,
    )

    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=1)


# =========================================================
# 7. CAP NHAT TRANG THAI BOOKING
# =========================================================

class BookingStatusUpdate(BaseModel):

    trang_thai: TrangThaiBookingEnum

    ly_do: Optional[str] = Field(
        None,
        max_length=255,
    )

    @field_validator("ly_do")
    @classmethod
    def normalize_reason(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value

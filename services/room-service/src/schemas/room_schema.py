from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.models.phong import TrangThaiPhongEnum
from src.schemas.room_type_schema import LoaiPhongBriefResponse

class PhongBase(BaseModel):
    so_phong: str = Field(..., min_length=1, max_length=50)
    tang: Optional[int] = Field(1, ge=0)
    trang_thai: TrangThaiPhongEnum = TrangThaiPhongEnum.AVAILABLE
    ghi_chu: Optional[str] = Field(None, max_length=255)

class PhongCreate(PhongBase):
    pass

class BatchCreateRoomsRequest(BaseModel):
    prefix: Optional[str] = Field("P.", max_length=10)
    tang: Optional[int] = Field(1, ge=0)
    from_number: Optional[int] = Field(None, ge=1)
    to_number: Optional[int] = Field(None, ge=1)
    room_numbers: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Danh sách các số phòng cụ thể",
    )

    @field_validator("room_numbers")
    @classmethod
    def normalize_room_numbers(cls, values: Optional[List[str]]) -> Optional[List[str]]:
        if values is None:
            return None
        normalized = [value.strip() for value in values]
        if any(not value or len(value) > 50 for value in normalized):
            raise ValueError("Mỗi số phòng phải có từ 1 đến 50 ký tự.")
        return normalized

class PhongStatusUpdate(BaseModel):
    trang_thai: TrangThaiPhongEnum
    ghi_chu: Optional[str] = Field(None, max_length=255)

class PhongResponse(PhongBase):
    id_phong: int
    id_loai_phong: int
    id_khach_san: int
    ngay_tao: datetime
    ngay_cap_nhat: datetime
    loai_phong: Optional[LoaiPhongBriefResponse] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedRoomsResponse(BaseModel):
    items: List[PhongResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class AvailableRoomQuery(BaseModel):
    hotel_id: int
    check_in: date
    check_out: date
    num_guests: Optional[int] = 1

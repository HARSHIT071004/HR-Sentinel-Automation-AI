from datetime import datetime, date
from pydantic import BaseModel, field_serializer
import uuid


class AttendanceBase(BaseModel):
    employee_id: str
    name: str
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    late_flag: bool = False
    missing_punch: bool = False
    raw_punch_count: int = 0


class AttendanceResponse(AttendanceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceUploadResponse(BaseModel):
    upload_id: str
    file_name: str
    status: str
    records_created: int
    records_updated: int
    warnings_detected: int


class UploadLogResponse(BaseModel):
    id: str
    file_name: str
    status: str
    row_count: int
    records_created: int
    uploaded_at: datetime

    @field_serializer('id')
    def serialize_id(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True

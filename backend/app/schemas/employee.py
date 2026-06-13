import uuid
from datetime import datetime, date
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    employee_id: str
    designation: str | None = None
    date_of_joining: date | None = None
    employment_type: str = "full_time"
    department_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    designation: str | None = None
    date_of_joining: date | None = None
    employment_type: str | None = None
    department_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class EmployeeResponse(EmployeeBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeDetailResponse(EmployeeResponse):
    department_name: str | None = None
    user_email: str | None = None
    user_name: str | None = None

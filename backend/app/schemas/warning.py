from datetime import datetime
from pydantic import BaseModel


class WarningLogResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    month_year: str
    strike_level: int
    warning_type: str
    message: str
    delivery_status: str
    sent_at: datetime

    class Config:
        from_attributes = True

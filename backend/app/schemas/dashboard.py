from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_employees: int
    present_today: int
    late_today: int
    missing_punches: int
    total_warnings: int
    strike_1_count: int
    strike_2_count: int
    strike_3_count: int


class DashboardFeedItem(BaseModel):
    employee_id: str
    name: str
    check_in: str | None = None
    check_out: str | None = None
    status: str
    strikes: int
    department: str | None = None


class DashboardAlert(BaseModel):
    employee_id: str
    name: str
    alert_type: str
    message: str
    strike_level: int
    date: str

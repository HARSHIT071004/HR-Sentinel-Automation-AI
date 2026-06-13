from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.employee_repo import EmployeeRepository
from app.models.attendance import DailyRecord, MonthlySummary, WarningLog
from datetime import date


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.employee_repo = EmployeeRepository(db)

    async def get_stats(self) -> dict:
        total_employees = await self.employee_repo.count_employees()
        today_records = await self.attendance_repo.get_today_records()
        present_today = len(today_records)
        late_today = sum(1 for r in today_records if r.late_flag)
        missing_punches = sum(1 for r in today_records if r.missing_punch)
        strike_dist = await self.attendance_repo.get_strike_distribution()

        total_warnings_result = await self.db.execute(select(func.count(WarningLog.id)))
        total_warnings = total_warnings_result.scalar()

        return {
            "total_employees": total_employees,
            "present_today": present_today,
            "late_today": late_today,
            "missing_punches": missing_punches,
            "total_warnings": total_warnings,
            "strike_1_count": strike_dist.get("strike_1", 0),
            "strike_2_count": strike_dist.get("strike_2", 0),
            "strike_3_count": strike_dist.get("strike_3", 0),
        }

    async def get_feed(self) -> list[dict]:
        today_records = await self.attendance_repo.get_today_records()
        current_month = date.today().strftime("%Y-%m")

        feed = []
        for record in today_records:
            summary_result = await self.db.execute(
                select(MonthlySummary).where(
                    and_(
                        MonthlySummary.employee_id == record.employee_id,
                        MonthlySummary.month_year == current_month,
                    )
                )
            )
            summary = summary_result.scalar_one_or_none()
            strikes = summary.late_count if summary else 0

            if record.late_flag:
                status = "Late"
            elif record.missing_punch:
                status = "Missing Punch"
            else:
                status = "Present"

            feed.append({
                "employee_id": record.employee_id,
                "name": record.name,
                "check_in": record.check_in.strftime("%I:%M %p") if record.check_in else None,
                "check_out": record.check_out.strftime("%I:%M %p") if record.check_out else None,
                "status": status,
                "strikes": strikes,
            })

        return sorted(feed, key=lambda x: x["strikes"], reverse=True)

    async def get_alerts(self) -> list[dict]:
        warnings = await self.attendance_repo.get_recent_warnings(limit=10)
        alerts = []
        for w in warnings:
            alert_type = {1: "warning", 2: "warning", 3: "critical"}.get(w.strike_level, "warning")
            alerts.append({
                "employee_id": w.employee_id,
                "name": w.name,
                "alert_type": alert_type,
                "message": w.message[:100] + "..." if len(w.message) > 100 else w.message,
                "strike_level": w.strike_level,
                "date": w.sent_at.strftime("%Y-%m-%d %H:%M"),
            })
        return alerts

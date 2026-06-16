import uuid
from datetime import date, datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attendance import DailyRecord, MonthlySummary, UploadLog, WarningLog
from app.models.employee import EmployeeProfile


class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, record_id: int) -> DailyRecord | None:
        return await self.db.get(DailyRecord, record_id)

    async def upsert_daily_record(self, record: dict) -> DailyRecord:
        data = dict(record)
        data.pop("month_year", None)
        if isinstance(data.get("date"), str):
            data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").date()

        existing = await self.db.execute(
            select(DailyRecord).where(
                and_(
                    DailyRecord.employee_id == data["employee_id"],
                    DailyRecord.date == data["date"],
                )
            )
        )
        existing_record = existing.scalar_one_or_none()
        for key in ("check_in", "check_out"):
            val = data.get(key)
            if isinstance(val, str) and val:
                try:
                    data[key] = datetime.fromisoformat(val)
                except ValueError:
                    data[key] = None

        if existing_record:
            existing_record.check_in = data.get("check_in")
            existing_record.check_out = data.get("check_out")
            existing_record.late_flag = data.get("late_flag", False)
            existing_record.missing_punch = data.get("missing_punch", False)
            existing_record.raw_punch_count = data.get("raw_punch_count", 0)
            existing_record.upload_id = data.get("upload_id")
            await self.db.flush()
            return existing_record
        else:
            new_record = DailyRecord(**data)
            self.db.add(new_record)
            await self.db.flush()
            return new_record

    async def upsert_monthly_summary(self, employee_id: str, name: str, month_year: str, is_late: bool) -> MonthlySummary:
        existing = await self.db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.employee_id == employee_id,
                    MonthlySummary.month_year == month_year,
                )
            )
        )
        summary = existing.scalar_one_or_none()

        if summary:
            if is_late:
                summary.late_count += 1
                summary.last_late_date = date.today()
            await self.db.flush()
            return summary
        else:
            summary = MonthlySummary(
                employee_id=employee_id,
                name=name,
                month_year=month_year,
                late_count=1 if is_late else 0,
                last_late_date=date.today() if is_late else None,
            )
            self.db.add(summary)
            await self.db.flush()
            return summary

    async def get_monthly_summary(self, employee_id: str, month_year: str) -> MonthlySummary | None:
        result = await self.db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.employee_id == employee_id,
                    MonthlySummary.month_year == month_year,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_upload_log(self, file_name: str, file_hash: str, uploaded_by: uuid.UUID | None = None) -> UploadLog:
        upload = UploadLog(
            file_name=file_name,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
        )
        self.db.add(upload)
        await self.db.flush()
        return upload

    async def update_upload_log(self, upload: UploadLog, **kwargs) -> UploadLog:
        for key, value in kwargs.items():
            setattr(upload, key, value)
        await self.db.flush()
        return upload

    async def get_upload_by_hash(self, file_hash: str) -> UploadLog | None:
        result = await self.db.execute(select(UploadLog).where(UploadLog.file_hash == file_hash))
        return result.scalar_one_or_none()

    async def create_warning(self, employee_id: str, name: str, month_year: str, strike_level: int, warning_type: str, message: str) -> WarningLog:
        warning = WarningLog(
            employee_id=employee_id,
            name=name,
            month_year=month_year,
            strike_level=strike_level,
            warning_type=warning_type,
            message=message,
        )
        self.db.add(warning)
        await self.db.flush()
        return warning

    async def get_today_records(self, target_date: date | None = None) -> list[DailyRecord]:
        if target_date is None:
            target_date = date.today()
        result = await self.db.execute(
            select(DailyRecord).where(DailyRecord.date == target_date)
        )
        return list(result.scalars().all())

    async def get_employee_records(self, employee_id: str, skip: int = 0, limit: int = 30) -> list[DailyRecord]:
        result = await self.db.execute(
            select(DailyRecord)
            .where(DailyRecord.employee_id == employee_id)
            .order_by(DailyRecord.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_today_late(self) -> int:
        result = await self.db.execute(
            select(func.count(DailyRecord.id)).where(
                and_(DailyRecord.date == date.today(), DailyRecord.late_flag == True)
            )
        )
        return result.scalar()

    async def count_today_missing(self) -> int:
        result = await self.db.execute(
            select(func.count(DailyRecord.id)).where(
                and_(DailyRecord.date == date.today(), DailyRecord.missing_punch == True)
            )
        )
        return result.scalar()

    async def get_strike_distribution(self) -> dict:
        current_month = date.today().strftime("%Y-%m")
        result = await self.db.execute(
            select(MonthlySummary).where(MonthlySummary.month_year == current_month)
        )
        summaries = list(result.scalars().all())
        return {
            "strike_1": sum(1 for s in summaries if s.late_count == 1),
            "strike_2": sum(1 for s in summaries if s.late_count == 2),
            "strike_3": sum(1 for s in summaries if s.late_count >= 3),
        }

    async def get_recent_warnings(self, limit: int = 10) -> list[WarningLog]:
        result = await self.db.execute(
            select(WarningLog).order_by(WarningLog.sent_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_upload_by_id(self, upload_id: uuid.UUID) -> UploadLog | None:
        return await self.db.get(UploadLog, upload_id)

    async def delete_records_by_upload_id(self, upload_id: uuid.UUID) -> list[str]:
        """Delete all daily records for an upload and return affected (employee_id, month_year) pairs."""
        result = await self.db.execute(
            select(DailyRecord).where(DailyRecord.upload_id == upload_id)
        )
        records = list(result.scalars().all())
        affected = list(set((r.employee_id, r.date.strftime("%Y-%m")) for r in records))
        for r in records:
            await self.db.delete(r)
        await self.db.flush()
        return affected

    async def delete_upload_log(self, upload_log: UploadLog) -> None:
        await self.db.delete(upload_log)
        await self.db.flush()

    async def recalculate_monthly_summary(self, employee_id: str, month_year: str) -> None:
        """Recalculate late_count and warning_level for an employee's month."""
        year = int(month_year[:4])
        month = int(month_year[5:])
        import calendar
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])

        late_count_result = await self.db.execute(
            select(func.count(DailyRecord.id)).where(
                and_(
                    DailyRecord.employee_id == employee_id,
                    DailyRecord.date >= start_date,
                    DailyRecord.date <= end_date,
                    DailyRecord.late_flag == True,
                )
            )
        )
        new_late_count = late_count_result.scalar() or 0

        summary_result = await self.db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.employee_id == employee_id,
                    MonthlySummary.month_year == month_year,
                )
            )
        )
        summary = summary_result.scalar_one_or_none()
        if summary:
            if new_late_count == 0:
                await self.db.delete(summary)
            else:
                summary.late_count = new_late_count
                summary.warning_level = min(new_late_count, 3)
            await self.db.flush()

    async def delete_employees_without_records(self, employee_ids: list[str]) -> list[str]:
        """Delete EmployeeProfile records that have zero DailyRecords. Returns deleted employee_ids."""
        deleted = []
        for emp_id in employee_ids:
            count_result = await self.db.execute(
                select(func.count(DailyRecord.id)).where(DailyRecord.employee_id == emp_id)
            )
            if count_result.scalar() == 0:
                emp_result = await self.db.execute(
                    select(EmployeeProfile).where(EmployeeProfile.employee_id == emp_id)
                )
                emp = emp_result.scalar_one_or_none()
                if emp:
                    await self.db.delete(emp)
                    deleted.append(emp_id)
        if deleted:
            await self.db.flush()
        return deleted

    async def delete_employee_ai_data(self, employee_ids: list[str]) -> None:
        """Delete RiskScore, AIWarning, WarningLog records for given employees."""
        from app.models.ai import RiskScore, AIWarning
        for emp_id in employee_ids:
            for model_cls in (RiskScore, AIWarning, WarningLog):
                result = await self.db.execute(
                    select(model_cls).where(model_cls.employee_id == emp_id)
                )
                for row in result.scalars().all():
                    await self.db.delete(row)
        await self.db.flush()

    async def get_or_create_employee(self, employee_id: str, name: str) -> EmployeeProfile:
        result = await self.db.execute(
            select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id)
        )
        emp = result.scalar_one_or_none()
        if emp:
            return emp
        emp = EmployeeProfile(employee_id=employee_id, name=name, email=f"{employee_id.lower()}@company.com")
        self.db.add(emp)
        await self.db.flush()
        return emp

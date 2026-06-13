import uuid
import hashlib
import json
from datetime import datetime, time, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.attendance_repo import AttendanceRepository
from app.core.exceptions import ConflictError, BadRequestError
from app.services.attendance_ingestion import ingest_attendance_records, delete_attendance_embeddings


LATE_THRESHOLD_HOUR = 11
LATE_THRESHOLD_MIN = 0
TIMEZONE_OFFSET = "+05:30"


def generate_file_hash(items: list) -> str:
    sorted_data = sorted(items, key=lambda r: f"{r.get('employee_id', '')}_{r.get('date', '')}_{r.get('time', '')}")
    raw = json.dumps(sorted_data, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_time(time_str: str) -> time | None:
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def normalize_date(date_str) -> str | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str)).date().isoformat()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").date().isoformat()
        except ValueError:
            return None


def to_timestamp(date_str: str, time_obj: time | None) -> str | None:
    if not date_str or not time_obj:
        return None
    return f"{date_str}T{time_obj.isoformat()}{TIMEZONE_OFFSET}"


def _normalize_key(key: str) -> str:
    """Normalize column header keys to handle various naming conventions."""
    mapping = {
        "employee id": "employee_id", "emp id": "employee_id", "emp_id": "employee_id",
        "employee_code": "employee_id", "employeecode": "employee_id", "emp_code": "employee_id",
        "employee name": "name", "emp name": "name", "emp_name": "name",
        "employee_name": "name", "full name": "name", "full_name": "name",
    }
    normalized = key.strip().lower().replace("  ", " ")
    return mapping.get(normalized, normalized)


def consolidate_attendance(items: list) -> tuple[list, str]:
    file_hash = generate_file_hash(items)
    grouped = {}
    warnings = []

    for item in items:
        normalized = {}
        for k, v in item.items():
            normalized[_normalize_key(k)] = v
        item = normalized

        employee_id = str(item.get("employee_id") or "").strip()
        name = str(item.get("name") or "").strip()
        date_str = normalize_date(item.get("date"))
        raw_time = item.get("time")
        status = str(item.get("status") or "").strip().upper()

        if not employee_id or not date_str:
            warnings.append(f"Skipped: missing employee_id or date")
            continue
        if status not in ("IN", "OUT"):
            warnings.append(f"Skipped: invalid status '{status}' for {employee_id}")
            continue

        key = f"{employee_id}__{date_str}"
        if key not in grouped:
            grouped[key] = {
                "employee_id": employee_id,
                "name": name,
                "date": date_str,
                "in_times": [],
                "out_times": [],
                "total_punches": 0,
            }

        grouped[key]["total_punches"] += 1
        parsed_t = parse_time(raw_time)
        if parsed_t:
            if status == "IN":
                grouped[key]["in_times"].append(parsed_t)
            else:
                grouped[key]["out_times"].append(parsed_t)
        else:
            warnings.append(f"Invalid time '{raw_time}' for {employee_id}")

    results = []
    for group in grouped.values():
        group["in_times"].sort()
        group["out_times"].sort()

        check_in = group["in_times"][0] if group["in_times"] else None
        check_out = group["out_times"][-1] if group["out_times"] else None

        late_flag = False
        if check_in:
            threshold = time(LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MIN)
            late_flag = check_in > threshold

        missing_punch = not check_in or not check_out

        results.append({
            "employee_id": group["employee_id"],
            "name": group["name"],
            "date": group["date"],
            "check_in": to_timestamp(group["date"], check_in),
            "check_out": to_timestamp(group["date"], check_out),
            "late_flag": late_flag,
            "missing_punch": missing_punch,
            "raw_punch_count": group["total_punches"],
            "month_year": group["date"][:7],
        })

    return results, file_hash


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)

    async def process_upload(self, filename: str, items: list, uploaded_by: uuid.UUID | None = None) -> dict:
        records, file_hash = consolidate_attendance(items)

        existing_upload = await self.attendance_repo.get_upload_by_hash(file_hash)
        if existing_upload:
            raise ConflictError("This file has already been uploaded")

        upload_log = await self.attendance_repo.create_upload_log(
            file_name=filename,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
        )

        created = 0
        updated = 0
        warnings_detected = 0

        # Auto-create employee profiles from uploaded data
        seen_ids = set()
        for record in records:
            if record["employee_id"] not in seen_ids:
                seen_ids.add(record["employee_id"])
                await self.attendance_repo.get_or_create_employee(
                    record["employee_id"], record["name"]
                )

        for record in records:
            record["upload_id"] = upload_log.id

            await self.attendance_repo.upsert_daily_record(record)
            created += 1

            if record["late_flag"]:
                warnings_detected += 1
                await self.attendance_repo.upsert_monthly_summary(
                    employee_id=record["employee_id"],
                    name=record["name"],
                    month_year=record["month_year"],
                    is_late=True,
                )
            else:
                await self.attendance_repo.upsert_monthly_summary(
                    employee_id=record["employee_id"],
                    name=record["name"],
                    month_year=record["month_year"],
                    is_late=False,
                )

        await self.attendance_repo.update_upload_log(
            upload_log,
            row_count=len(items),
            records_created=created,
            records_updated=updated,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )

        await self._process_escalations(records)

        await ingest_attendance_records(records, upload_id=upload_log.id)

        return {
            "upload_id": str(upload_log.id),
            "file_name": filename,
            "status": "completed",
            "records_created": created,
            "records_updated": updated,
            "warnings_detected": warnings_detected,
        }

    async def delete_upload(self, file_id: uuid.UUID) -> bool:
        upload_log = await self.attendance_repo.get_upload_by_id(file_id)
        if not upload_log:
            return False

        affected = await self.attendance_repo.delete_records_by_upload_id(file_id)
        employee_ids = list(set(emp_id for emp_id, _ in affected))

        for emp_id, month_yr in affected:
            await self.attendance_repo.recalculate_monthly_summary(emp_id, month_yr)

        await self.attendance_repo.delete_employee_ai_data(employee_ids)
        orphans = await self.attendance_repo.delete_employees_without_records(employee_ids)

        await delete_attendance_embeddings(file_id)

        await self.attendance_repo.delete_upload_log(upload_log)
        return True

    async def _process_escalations(self, records: list):
        for record in records:
            if not record["late_flag"]:
                continue

            summary = await self.attendance_repo.get_monthly_summary(
                employee_id=record["employee_id"],
                month_year=record["month_year"],
            )
            if not summary:
                continue

            strike_level = min(summary.late_count, 3)
            if strike_level >= 1 and summary.warning_level < strike_level:
                warning_type = {1: "friendly", 2: "formal", 3: "final"}.get(strike_level, "friendly")
                message = self._generate_warning_message(record["name"], strike_level, warning_type, record["date"])

                await self.attendance_repo.create_warning(
                    employee_id=record["employee_id"],
                    name=record["name"],
                    month_year=record["month_year"],
                    strike_level=strike_level,
                    warning_type=warning_type,
                    message=message,
                )

                summary.warning_level = strike_level
                summary.last_warning_date = date.today()
                await self.db.flush()

    def _generate_warning_message(self, name: str, strike_level: int, warning_type: str, late_date: str) -> str:
        messages = {
            1: f"Hi {name}, this is a friendly reminder that you arrived late on {late_date}. Please ensure timely check-ins.",
            2: f"Hi {name}, this is a formal warning. You have been late twice this month. A third late arrival will result in a mandatory HR meeting.",
            3: f"Hi {name}, this is a final warning. You have reached 3 late arrivals this month. A mandatory HR meeting has been scheduled.",
        }
        return messages.get(strike_level, messages[1])

    async def get_today_records(self):
        return await self.attendance_repo.get_today_records()

    async def get_employee_records(self, employee_id: str, skip: int = 0, limit: int = 30):
        return await self.attendance_repo.get_employee_records(employee_id, skip=skip, limit=limit)

    async def get_upload_logs(self, skip: int = 0, limit: int = 20):
        from sqlalchemy import select
        from app.models.attendance import UploadLog
        result = await self.db.execute(
            select(UploadLog).order_by(UploadLog.uploaded_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

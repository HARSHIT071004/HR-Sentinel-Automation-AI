import uuid
import json
import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.attendance import AttendanceUploadResponse, UploadLogResponse
from app.services.attendance_service import AttendanceService
from app.core.deps import require_role, get_current_user
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _parse_excel(file) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(file, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise BadRequestError("Excel file is empty or has no data rows")
    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    items = []
    for row in rows[1:]:
        record = {}
        for i, header in enumerate(headers):
            if header and i < len(row):
                record[header] = row[i]
        if record:
            items.append(record)
    wb.close()
    return items


def _parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise BadRequestError("CSV file is empty or has no headers")
    items = []
    for row in reader:
        normalized = {}
        for k, v in row.items():
            if k:
                normalized[k.strip().lower()] = v
        if normalized:
            items.append(normalized)
    return items


@router.post("/upload", response_model=AttendanceUploadResponse)
async def upload_attendance(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    if not file.filename:
        raise BadRequestError("No file provided")

    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise BadRequestError("Only .xlsx, .xls, and .csv files are accepted")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise BadRequestError(f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    try:
        if file.filename.endswith(".csv"):
            items = _parse_csv(content)
        else:
            items = _parse_excel(file.file)
    except BadRequestError:
        raise
    except Exception as e:
        raise BadRequestError(f"Failed to parse file: {str(e)}")

    if len(items) < 1:
        raise BadRequestError("No valid data rows found in file")

    service = AttendanceService(db)
    result = await service.process_upload(
        filename=file.filename,
        items=items,
        uploaded_by=current_user.id,
    )

    return AttendanceUploadResponse(**result)


@router.get("", response_model=list[dict])
async def list_attendance(
    employee_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AttendanceService(db)
    if employee_id:
        records = await service.get_employee_records(employee_id, skip=skip, limit=limit)
    else:
        records = await service.get_today_records()

    return [
        {
            "id": r.id,
            "employee_id": r.employee_id,
            "name": r.name,
            "date": str(r.date),
            "check_in": r.check_in.isoformat() if r.check_in else None,
            "check_out": r.check_out.isoformat() if r.check_out else None,
            "late_flag": r.late_flag,
            "missing_punch": r.missing_punch,
        }
        for r in records
    ]


@router.get("/files")
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AttendanceService(db)
    files = await service.get_upload_logs(skip=skip, limit=limit)
    return [
        {
            "id": str(f.id),
            "file_name": f.file_name,
            "status": f.status,
            "row_count": f.row_count,
            "records_created": f.records_created,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
        }
        for f in files
    ]


@router.delete("/files/{file_id}")
async def delete_upload_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AttendanceService(db)
    result = await service.delete_upload(file_id)
    if not result:
        raise NotFoundError("Upload file not found")
    return {"message": "File deleted successfully", "success": True}

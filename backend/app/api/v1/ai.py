import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.ai import (
    RiskScoreResponse, BehaviorAnalysisResponse, AIWarningResponse,
    ExecutiveReportResponse, ReportGenerateRequest, AIUsageSummary,
)
from app.services.ai_service import AIService
from app.core.deps import require_role, get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


@router.get("/risk/{employee_id}", response_model=RiskScoreResponse)
async def get_risk_score(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)
    result = await service.score_risk(employee_id)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/behavior/{employee_id}", response_model=BehaviorAnalysisResponse)
async def get_behavior_analysis(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)
    result = await service.analyze_behavior(employee_id)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/warning/{employee_id}", response_model=AIWarningResponse)
async def generate_warning(
    employee_id: str,
    strike_level: int = Query(ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)

    # Get employee context
    from sqlalchemy import select
    from app.models.employee import EmployeeProfile
    result = await db.execute(select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Employee not found")

    from datetime import date
    context = {
        "name": employee.employee_id,
        "date": str(date.today()),
        "check_in": "11:15 AM",
        "late_count": strike_level,
    }

    warning = await service.generate_warning(employee_id, strike_level, context)
    return warning


@router.post("/reports/generate", response_model=ExecutiveReportResponse)
async def generate_report(
    data: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)
    result = await service.generate_executive_report(
        report_type=data.report_type,
        generated_by=current_user.full_name,
    )
    return result


@router.get("/reports", response_model=list[dict])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)
    return await service.get_reports(skip=skip, limit=limit)


@router.get("/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = AIService(db)
    result = await service.get_report(report_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/usage", response_model=AIUsageSummary)
async def get_usage(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = AIService(db)
    return await service.get_usage_summary(days=days)

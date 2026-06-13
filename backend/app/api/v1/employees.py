import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeDetailResponse
from app.services.employee_service import EmployeeService
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.department import Department

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeDetailResponse])
async def list_employees(
    department_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EmployeeService(db)
    employees = await service.list_employees(department_id=department_id, search=search, skip=skip, limit=limit)

    # Get department names
    dept_map = {}
    if employees:
        dept_ids = set(e.department_id for e in employees if e.department_id)
        for dept_id in dept_ids:
            dept = await db.get(Department, dept_id)
            if dept:
                dept_map[dept_id] = dept.name

    result = []
    for emp in employees:
        result.append(EmployeeDetailResponse(
            id=emp.id,
            employee_id=emp.employee_id,
            designation=emp.designation,
            date_of_joining=emp.date_of_joining,
            employment_type=emp.employment_type,
            department_id=emp.department_id,
            user_id=emp.user_id,
            created_at=emp.created_at,
            department_name=dept_map.get(emp.department_id),
            user_email=emp.email,
            user_name=emp.name,
        ))
    return result


@router.post("", response_model=EmployeeResponse)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = EmployeeService(db)
    employee = await service.create_employee(
        employee_id=data.employee_id,
        name=data.employee_id,
        designation=data.designation,
        date_of_joining=data.date_of_joining,
        employment_type=data.employment_type,
        department_id=data.department_id,
        user_id=data.user_id,
    )
    return employee


@router.get("/{emp_id}", response_model=EmployeeDetailResponse)
async def get_employee(
    emp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EmployeeService(db)
    employee = await service.get_employee(emp_id)

    dept_name = None
    if employee.department_id:
        dept = await db.get(Department, employee.department_id)
        if dept:
            dept_name = dept.name

    return EmployeeDetailResponse(
        id=employee.id,
        employee_id=employee.employee_id,
        designation=employee.designation,
        date_of_joining=employee.date_of_joining,
        employment_type=employee.employment_type,
        department_id=employee.department_id,
        user_id=employee.user_id,
        created_at=employee.created_at,
        department_name=dept_name,
        user_email=employee.email,
        user_name=employee.name,
    )


@router.put("/{emp_id}", response_model=EmployeeResponse)
async def update_employee(
    emp_id: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = EmployeeService(db)
    employee = await service.update_employee(
        emp_id,
        designation=data.designation,
        date_of_joining=data.date_of_joining,
        employment_type=data.employment_type,
        department_id=data.department_id,
        user_id=data.user_id,
    )
    return employee


@router.delete("/{emp_id}")
async def delete_employee(
    emp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = EmployeeService(db)
    await service.delete_employee(emp_id)
    return {"message": "Employee deleted successfully", "success": True}

import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.employee import EmployeeProfile


class EmployeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, emp_id: uuid.UUID) -> EmployeeProfile | None:
        return await self.db.get(EmployeeProfile, emp_id)

    async def get_by_employee_id(self, employee_id: str) -> EmployeeProfile | None:
        result = await self.db.execute(
            select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> EmployeeProfile:
        employee = EmployeeProfile(**kwargs)
        self.db.add(employee)
        await self.db.flush()
        return employee

    async def update(self, employee: EmployeeProfile, **kwargs) -> EmployeeProfile:
        for key, value in kwargs.items():
            if value is not None:
                setattr(employee, key, value)
        await self.db.flush()
        return employee

    async def delete(self, employee: EmployeeProfile) -> None:
        await self.db.delete(employee)
        await self.db.flush()

    async def list_employees(
        self,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EmployeeProfile]:
        query = select(EmployeeProfile)

        if department_id:
            query = query.where(EmployeeProfile.department_id == department_id)
        if search:
            query = query.where(EmployeeProfile.employee_id.ilike(f"%{search}%"))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_employees(self, department_id: uuid.UUID | None = None) -> int:
        query = select(func.count(EmployeeProfile.id))
        if department_id:
            query = query.where(EmployeeProfile.department_id == department_id)
        result = await self.db.execute(query)
        return result.scalar()

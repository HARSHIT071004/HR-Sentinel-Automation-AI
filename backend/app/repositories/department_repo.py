import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, dept_id: uuid.UUID) -> Department | None:
        return await self.db.get(Department, dept_id)

    async def get_by_name(self, name: str) -> Department | None:
        result = await self.db.execute(select(Department).where(Department.name == name))
        return result.scalar_one_or_none()

    async def create(self, name: str) -> Department:
        department = Department(name=name)
        self.db.add(department)
        await self.db.flush()
        return department

    async def update(self, department: Department, name: str | None = None) -> Department:
        if name is not None:
            department.name = name
        await self.db.flush()
        return department

    async def list_departments(self, skip: int = 0, limit: int = 100) -> list[Department]:
        result = await self.db.execute(select(Department).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count_departments(self) -> int:
        result = await self.db.execute(select(func.count(Department.id)))
        return result.scalar()

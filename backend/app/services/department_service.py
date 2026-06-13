import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.department_repo import DepartmentRepository
from app.core.exceptions import NotFoundError, ConflictError


class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dept_repo = DepartmentRepository(db)

    async def create_department(self, name: str):
        existing = await self.dept_repo.get_by_name(name)
        if existing:
            raise ConflictError(f"Department '{name}' already exists")
        return await self.dept_repo.create(name=name)

    async def get_department(self, dept_id: uuid.UUID):
        dept = await self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise NotFoundError("Department")
        return dept

    async def update_department(self, dept_id: uuid.UUID, name: str | None = None):
        dept = await self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise NotFoundError("Department")
        if name:
            existing = await self.dept_repo.get_by_name(name)
            if existing and existing.id != dept_id:
                raise ConflictError(f"Department '{name}' already exists")
        return await self.dept_repo.update(dept, name=name)

    async def list_departments(self, skip: int = 0, limit: int = 100):
        return await self.dept_repo.list_departments(skip=skip, limit=limit)

    async def count_departments(self):
        return await self.dept_repo.count_departments()

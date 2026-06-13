import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.employee_repo import EmployeeRepository
from app.core.exceptions import NotFoundError, ConflictError


class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.employee_repo = EmployeeRepository(db)

    async def create_employee(self, employee_id: str, **kwargs):
        existing = await self.employee_repo.get_by_employee_id(employee_id)
        if existing:
            raise ConflictError(f"Employee '{employee_id}' already exists")
        return await self.employee_repo.create(employee_id=employee_id, **kwargs)

    async def get_employee(self, emp_id: uuid.UUID):
        employee = await self.employee_repo.get_by_id(emp_id)
        if not employee:
            raise NotFoundError("Employee")
        return employee

    async def update_employee(self, emp_id: uuid.UUID, **kwargs):
        employee = await self.employee_repo.get_by_id(emp_id)
        if not employee:
            raise NotFoundError("Employee")
        return await self.employee_repo.update(employee, **kwargs)

    async def delete_employee(self, emp_id: uuid.UUID):
        employee = await self.employee_repo.get_by_id(emp_id)
        if not employee:
            raise NotFoundError("Employee")
        await self.employee_repo.delete(employee)

    async def list_employees(self, department_id: uuid.UUID | None = None, search: str | None = None, skip: int = 0, limit: int = 100):
        return await self.employee_repo.list_employees(department_id=department_id, search=search, skip=skip, limit=limit)

    async def count_employees(self, department_id: uuid.UUID | None = None):
        return await self.employee_repo.count_employees(department_id=department_id)

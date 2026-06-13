from fastapi import APIRouter
from app.api.v1 import auth, employees, departments, attendance, dashboard, health, ai, copilot

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(departments.router)
api_router.include_router(attendance.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(copilot.router)
api_router.include_router(health.router)

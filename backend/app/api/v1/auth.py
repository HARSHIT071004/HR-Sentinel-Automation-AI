from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import UserCreate, UserResponse, LoginRequest, TokenResponse, RefreshRequest, MessageResponse
from app.services.auth_service import AuthService
from app.core.deps import get_current_user, require_role
from app.core.exceptions import AppException
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    service = AuthService(db)
    user = await service.register(email=data.email, password=data.password, full_name=data.full_name, role=data.role)
    return user


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        service = AuthService(db)
        result = await service.login(email=data.email, password=data.password)
        return result
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_token(refresh_token=data.refresh_token)
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

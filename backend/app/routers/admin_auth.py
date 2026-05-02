from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.admin import Admin
from app.utils.security import hash_password, verify_password, create_access_token
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    email: str
    token_type: str = "bearer"


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.email == data.email.lower()))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is deactivated")

    token = create_access_token(str(admin.id))
    return AdminLoginResponse(access_token=token, email=admin.email)

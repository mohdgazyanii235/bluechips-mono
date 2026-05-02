from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.escort import Escort
from app.models.admin import Admin

bearer_scheme = HTTPBearer()


async def get_current_escort(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Escort:
    token = credentials.credentials
    escort_id = decode_access_token(token)
    if not escort_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(Escort).where(Escort.id == escort_id))
    escort = result.scalar_one_or_none()
    if not escort or not escort.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found or deactivated")
    return escort


async def get_current_verified_escort(escort: Escort = Depends(get_current_escort)) -> Escort:
    if not escort.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email first")
    return escort


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    token = credentials.credentials
    admin_id = decode_access_token(token)
    if not admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account not found or deactivated")
    return admin

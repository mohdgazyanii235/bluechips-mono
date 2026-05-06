from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.escort import Escort, EscortPhoto
from app.services.storage_service import upload_image, delete_file
from app.services.email_service import send_profile_reactivated
from app.routers.deps import get_current_verified_escort
from app.schemas.common import MessageResponse
from app.config import settings
import uuid

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Magic byte signatures for supported image types
_JPEG_SIG = b'\xff\xd8\xff'
_PNG_SIG = b'\x89PNG\r\n\x1a\n'


def _valid_image_magic(data: bytes) -> bool:
    if data[:3] == _JPEG_SIG:
        return True
    if data[:8] == _PNG_SIG:
        return True
    # WebP: starts with RIFF....WEBP
    if len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return True
    return False


@router.post("/photo", status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG and WebP images are accepted")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"Image must be under {settings.MAX_UPLOAD_SIZE_MB}MB")

    if not _valid_image_magic(contents):
        raise HTTPException(status_code=400, detail="File content does not match a supported image format")

    result = await db.execute(select(EscortPhoto).where(EscortPhoto.escort_id == escort.id))
    existing_photos = result.scalars().all()

    if len(existing_photos) >= escort.photo_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Your plan allows up to {escort.photo_limit} photos. Upgrade to add more."
        )

    url, thumb_url = await upload_image(contents, file.filename or "photo.jpg", subfolder="photos")

    is_primary = len(existing_photos) == 0
    photo = EscortPhoto(
        escort_id=escort.id,
        url=url,
        thumbnail_url=thumb_url,
        is_primary=is_primary,
        sort_order=len(existing_photos),
    )
    db.add(photo)
    await db.flush()

    return {"id": str(photo.id), "url": url, "thumbnail_url": thumb_url, "is_primary": is_primary}


@router.delete("/photo/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    photo_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EscortPhoto).where(EscortPhoto.id == photo_id, EscortPhoto.escort_id == escort.id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    await delete_file(photo.url)
    if photo.thumbnail_url:
        await delete_file(photo.thumbnail_url)
    await db.delete(photo)

    # Reassign primary if needed
    remaining_result = await db.execute(
        select(EscortPhoto).where(EscortPhoto.escort_id == escort.id).order_by(EscortPhoto.sort_order)
    )
    remaining = remaining_result.scalars().all()
    if remaining and not any(p.is_primary for p in remaining):
        remaining[0].is_primary = True

    # Auto-reactivate profile if it was paused due to photo limit and is now within limit
    if not escort.is_approved and len(remaining) <= escort.photo_limit:
        escort.is_approved = True
        background_tasks.add_task(
            send_profile_reactivated,
            escort_email=escort.email,
            stage_name=escort.stage_name,
        )

    return MessageResponse(message="Photo deleted")


@router.patch("/photo/{photo_id}/set-primary", response_model=MessageResponse)
async def set_primary_photo(
    photo_id: uuid.UUID,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    all_photos_result = await db.execute(
        select(EscortPhoto).where(EscortPhoto.escort_id == escort.id)
    )
    all_photos = all_photos_result.scalars().all()
    for p in all_photos:
        p.is_primary = str(p.id) == str(photo_id)

    return MessageResponse(message="Primary photo updated")

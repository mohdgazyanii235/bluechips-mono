"""Shared image-upload validation used by photo uploads and verification submissions."""
from fastapi import HTTPException, UploadFile
from app.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Magic byte signatures
_JPEG_SIG = b"\xff\xd8\xff"
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def is_valid_image_magic(data: bytes) -> bool:
    if data[:3] == _JPEG_SIG:
        return True
    if data[:8] == _PNG_SIG:
        return True
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


def validate_image_upload(file: UploadFile, contents: bytes, *, field_name: str = "file") -> None:
    """Run the standard image validation pipeline. Raises HTTPException on failure.

    Checks content-type header, file size, and magic bytes. Header alone is trivially
    spoofable so the magic-byte check is the real defence — combined they reject
    almost all non-image uploads.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: only JPEG, PNG, and WebP images are accepted",
        )
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: file must be under {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    if not is_valid_image_magic(contents):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: file content does not match a supported image format",
        )

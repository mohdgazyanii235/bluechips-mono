"""
Unified storage service.
Uses local filesystem in development; AWS S3 in production when credentials are set.
"""
import os
import time
import hmac
import hashlib
import uuid
import aiofiles
from pathlib import Path
from PIL import Image
import io
from app.config import settings

if settings.use_s3:
    import boto3
    _boto_kwargs = dict(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    if settings.S3_ENDPOINT_URL:
        _boto_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    s3_client = boto3.client("s3", **_boto_kwargs)


def _local_upload_path(subfolder: str = "photos") -> Path:
    path = Path(settings.LOCAL_UPLOADS_DIR) / subfolder
    path.mkdir(parents=True, exist_ok=True)
    return path


def _public_url(key: str) -> str:
    base = settings.public_media_url
    if base:
        return f"{base.rstrip('/')}/{key}"
    return f"{settings.BACKEND_URL}/uploads/{key}"


async def upload_image(file_bytes: bytes, filename: str, subfolder: str = "photos") -> tuple[str, str]:
    """Upload original + generate thumbnail. Returns (url, thumbnail_url)."""
    ext = Path(filename).suffix.lower() or ".jpg"
    key = f"{subfolder}/{uuid.uuid4().hex}{ext}"
    thumb_key = f"{subfolder}/thumbs/{uuid.uuid4().hex}{ext}"

    # Process with Pillow
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Original — cap at 1200px wide
    orig = img.copy()
    orig.thumbnail((1200, 1600), Image.LANCZOS)
    orig_bytes = io.BytesIO()
    orig.save(orig_bytes, format="JPEG", quality=85, optimize=True)
    orig_bytes.seek(0)

    # Thumbnail — 400x500 crop
    thumb = img.copy()
    thumb.thumbnail((400, 500), Image.LANCZOS)
    thumb_bytes = io.BytesIO()
    thumb.save(thumb_bytes, format="JPEG", quality=75, optimize=True)
    thumb_bytes.seek(0)

    if settings.use_s3:
        s3_client.put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=orig_bytes.read(), ContentType="image/jpeg")
        s3_client.put_object(Bucket=settings.S3_BUCKET_NAME, Key=thumb_key, Body=thumb_bytes.read(), ContentType="image/jpeg")
    else:
        local_path = _local_upload_path(subfolder)
        thumb_path = _local_upload_path(f"{subfolder}/thumbs")
        async with aiofiles.open(local_path / Path(key).name, "wb") as f:
            await f.write(orig_bytes.read())
        async with aiofiles.open(thumb_path / Path(thumb_key).name, "wb") as f:
            await f.write(thumb_bytes.read())

    return _public_url(key), _public_url(thumb_key)


async def upload_document(file_bytes: bytes, filename: str) -> str:
    """Upload a verification document. Not publicly accessible."""
    ext = Path(filename).suffix.lower() or ".jpg"
    key = f"documents/{uuid.uuid4().hex}{ext}"

    if settings.use_s3:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType="image/jpeg",
            ACL="private",
        )
    else:
        path = _local_upload_path("documents")
        async with aiofiles.open(path / Path(key).name, "wb") as f:
            await f.write(file_bytes)

    return key  # Return key, not public URL — documents are private


async def delete_file(key_or_url: str) -> None:
    """Delete a file by its key or URL."""
    if settings.use_s3 and not key_or_url.startswith("http"):
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key_or_url)
    else:
        # Local: extract filename from URL
        filename = key_or_url.split("/")[-1]
        for subdir in ["photos", "photos/thumbs", "documents"]:
            p = Path(settings.LOCAL_UPLOADS_DIR) / subdir / filename
            if p.exists():
                p.unlink()
                break


def _make_local_signed_url(key: str, expires_in: int = 3600) -> str:
    """Build an HMAC-signed URL for short-lived access to a local private file.

    The signature binds (key, expiry) to the server's SECRET_KEY so the URL
    can't be tampered with or replayed past its expiry. The /private/ route in
    main.py validates the signature and serves the file from disk.
    """
    expiry = int(time.time()) + expires_in
    sig_data = f"{key}|{expiry}".encode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), sig_data, hashlib.sha256).hexdigest()
    return f"{settings.BACKEND_URL}/private/{key}?exp={expiry}&sig={sig}"


def verify_local_signed_url(key: str, exp: int, sig: str) -> bool:
    """Constant-time verification of a /private/ URL signature."""
    if exp < int(time.time()):
        return False
    sig_data = f"{key}|{exp}".encode("utf-8")
    expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), sig_data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


async def get_signed_url(key: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for accessing a private document.

    For S3: presigned URL valid for `expires_in` seconds.
    For local: HMAC-signed URL handled by the /private/ route in main.py.
    """
    if not key:
        return None

    if settings.use_s3:
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            print(f"[SIGNED URL ERROR] {e}")
            return key
    else:
        return _make_local_signed_url(key, expires_in)

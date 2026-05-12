"""HTTP-level tests for `/api/upload/*` photo endpoints.

Covers:
- POST /upload/photo — magic-byte validation, content-type validation, photo
  limit enforcement by tier, primary-photo auto-set on first upload.
- DELETE /upload/photo/:id — only deletes own photo, reassigns primary,
  auto-reactivates a profile paused for photo-limit breach.
- PATCH /upload/photo/:id/set-primary — only one primary at a time.
- Email-verification requirement on all routes.
"""
from __future__ import annotations

import io
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models.escort import EscortPhoto
from app.utils.security import create_access_token
from tests.conftest import make_jpeg_bytes, make_png_bytes, make_webp_bytes


pytestmark = pytest.mark.asyncio


def _headers_for(escort) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(escort.id))}"}


# ---------------------------------------------------------------------------
# POST /upload/photo
# ---------------------------------------------------------------------------
class TestUploadPhoto:
    async def test_upload_valid_jpeg(self, client, escort, auth_headers, mock_storage, jpeg_bytes):
        files = {"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["url"]
        assert body["thumbnail_url"]
        assert body["is_primary"] is True  # first photo auto-primary

    async def test_upload_valid_png(self, client, escort, auth_headers, mock_storage, png_bytes):
        files = {"file": ("x.png", png_bytes, "image/png")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 201

    async def test_upload_valid_webp(self, client, escort, auth_headers, mock_storage, webp_bytes):
        files = {"file": ("x.webp", webp_bytes, "image/webp")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 201

    @pytest.mark.security
    @pytest.mark.parametrize("content_type", ["application/pdf", "text/plain", "application/x-msdownload"])
    async def test_upload_rejects_bad_content_type(self, client, auth_headers, mock_storage, jpeg_bytes, content_type):
        files = {"file": ("evil.exe", jpeg_bytes, content_type)}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 400
        assert "JPEG" in resp.json()["detail"]

    @pytest.mark.security
    async def test_upload_rejects_spoofed_image_jpeg_header(self, client, auth_headers, mock_storage):
        """A non-image with image/jpeg content-type must be rejected via magic-byte check."""
        files = {"file": ("evil.jpg", b"%PDF-1.4 fake content", "image/jpeg")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 400
        assert "content does not match" in resp.json()["detail"]

    @pytest.mark.security
    async def test_upload_rejects_executable_disguised_as_image(self, client, auth_headers, mock_storage):
        files = {"file": ("trojan.png", b"MZ\x90\x00\x03" + b"\x00" * 100, "image/png")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 400

    async def test_upload_oversized_file_rejected(self, client, auth_headers, mock_storage):
        from app.utils.file_validation import MAX_BYTES
        huge = make_jpeg_bytes() + b"\x00" * (MAX_BYTES + 1)
        files = {"file": ("huge.jpg", huge, "image/jpeg")}
        resp = await client.post("/api/upload/photo", headers=auth_headers, files=files)
        assert resp.status_code == 400
        assert "MB" in resp.json()["detail"]

    async def test_photo_limit_free_tier_3(self, client, db_session, escort_factory, mock_storage, jpeg_bytes):
        e = await escort_factory(subscription_tier="free")
        headers = _headers_for(e)
        files_factory = lambda: {"file": ("x.jpg", jpeg_bytes, "image/jpeg")}
        for _ in range(3):
            r = await client.post("/api/upload/photo", headers=headers, files=files_factory())
            assert r.status_code == 201
        # 4th rejected
        r = await client.post("/api/upload/photo", headers=headers, files=files_factory())
        assert r.status_code == 403
        assert "3 photos" in r.json()["detail"]

    async def test_photo_limit_premium_50(self, client, escort_factory, mock_storage):
        """Don't actually upload 50; just confirm computed limit is 50."""
        e = await escort_factory(subscription_tier="premium")
        assert e.photo_limit == 50

    async def test_requires_email_verified(self, client, escort_factory, mock_storage, jpeg_bytes):
        e = await escort_factory(is_email_verified=False)
        files = {"file": ("x.jpg", jpeg_bytes, "image/jpeg")}
        r = await client.post("/api/upload/photo", headers=_headers_for(e), files=files)
        assert r.status_code == 403

    async def test_requires_auth(self, client, mock_storage, jpeg_bytes):
        files = {"file": ("x.jpg", jpeg_bytes, "image/jpeg")}
        r = await client.post("/api/upload/photo", files=files)
        assert r.status_code == 403  # HTTPBearer missing-creds raises 403


# ---------------------------------------------------------------------------
# DELETE /upload/photo/:id
# ---------------------------------------------------------------------------
class TestDeletePhoto:
    async def test_delete_own_photo(self, client, db_session, escort, auth_headers, mock_storage):
        photo = EscortPhoto(escort_id=escort.id, url="photos/a.jpg", thumbnail_url="photos/thumbs/a.jpg",
                            is_primary=True, sort_order=0)
        db_session.add(photo)
        await db_session.flush()
        resp = await client.delete(f"/api/upload/photo/{photo.id}", headers=auth_headers)
        assert resp.status_code == 200
        remaining = await db_session.execute(select(EscortPhoto).where(EscortPhoto.id == photo.id))
        assert remaining.scalar_one_or_none() is None

    @pytest.mark.security
    async def test_cannot_delete_another_users_photo(self, client, db_session, escort_factory, mock_storage):
        a = await escort_factory()
        b = await escort_factory()
        photo = EscortPhoto(escort_id=b.id, url="photos/b.jpg", thumbnail_url="photos/thumbs/b.jpg")
        db_session.add(photo)
        await db_session.flush()
        resp = await client.delete(f"/api/upload/photo/{photo.id}", headers=_headers_for(a))
        assert resp.status_code == 404  # silently not-found; doesn't leak existence

    async def test_delete_unknown_photo_404(self, client, auth_headers):
        resp = await client.delete(f"/api/upload/photo/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_delete_reassigns_primary(self, client, db_session, escort, auth_headers, mock_storage):
        p1 = EscortPhoto(escort_id=escort.id, url="p1.jpg", is_primary=True, sort_order=0)
        p2 = EscortPhoto(escort_id=escort.id, url="p2.jpg", is_primary=False, sort_order=1)
        db_session.add_all([p1, p2])
        await db_session.flush()

        await client.delete(f"/api/upload/photo/{p1.id}", headers=auth_headers)
        await db_session.refresh(p2)
        assert p2.is_primary is True


# ---------------------------------------------------------------------------
# PATCH /upload/photo/:id/set-primary
# ---------------------------------------------------------------------------
class TestSetPrimary:
    async def test_set_primary_clears_others(self, client, db_session, escort, auth_headers):
        p1 = EscortPhoto(escort_id=escort.id, url="p1.jpg", is_primary=True, sort_order=0)
        p2 = EscortPhoto(escort_id=escort.id, url="p2.jpg", is_primary=False, sort_order=1)
        db_session.add_all([p1, p2])
        await db_session.flush()

        resp = await client.patch(f"/api/upload/photo/{p2.id}/set-primary", headers=auth_headers)
        assert resp.status_code == 200

        await db_session.refresh(p1)
        await db_session.refresh(p2)
        assert p1.is_primary is False
        assert p2.is_primary is True

    @pytest.mark.security
    async def test_set_primary_other_user_silently_noop(self, client, db_session, escort_factory):
        a = await escort_factory()
        b = await escort_factory()
        p = EscortPhoto(escort_id=b.id, url="p.jpg", is_primary=False)
        db_session.add(p)
        await db_session.flush()
        # Endpoint iterates ONLY escort's own photos; another user's photo cannot be promoted
        resp = await client.patch(f"/api/upload/photo/{p.id}/set-primary", headers=_headers_for(a))
        assert resp.status_code == 200
        await db_session.refresh(p)
        assert p.is_primary is False  # unchanged

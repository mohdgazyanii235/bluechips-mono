"""Unit tests for image upload validation.

Magic byte checks are the real defence (content-type headers are trivially
forgeable). These tests cover all three accepted formats plus several rejection
paths.
"""
from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.utils.file_validation import (
    is_valid_image_magic,
    validate_image_upload,
    MAX_BYTES,
)
from tests.conftest import make_jpeg_bytes, make_png_bytes, make_webp_bytes


def _upload(content_type: str, filename: str = "x.jpg") -> UploadFile:
    """Build a minimal UploadFile-like object for validation tests."""
    f = MagicMock(spec=UploadFile)
    f.content_type = content_type
    f.filename = filename
    return f


class TestMagicByteRecognition:
    def test_jpeg_recognised(self):
        assert is_valid_image_magic(make_jpeg_bytes()) is True

    def test_png_recognised(self):
        assert is_valid_image_magic(make_png_bytes()) is True

    def test_webp_recognised(self):
        assert is_valid_image_magic(make_webp_bytes()) is True

    def test_text_rejected(self):
        assert is_valid_image_magic(b"hello, this is not an image") is False

    def test_empty_rejected(self):
        assert is_valid_image_magic(b"") is False

    def test_pdf_rejected(self):
        """PDFs start with %PDF - must NOT match an image signature."""
        assert is_valid_image_magic(b"%PDF-1.4\n...") is False

    def test_executable_rejected(self):
        """Windows PE 'MZ' header must not match."""
        assert is_valid_image_magic(b"MZ\x90\x00\x03") is False
        # ELF
        assert is_valid_image_magic(b"\x7fELF\x02\x01\x01") is False


class TestValidateImageUpload:
    def test_valid_jpeg_passes(self):
        validate_image_upload(_upload("image/jpeg"), make_jpeg_bytes())

    def test_valid_png_passes(self):
        validate_image_upload(_upload("image/png", "x.png"), make_png_bytes())

    def test_valid_webp_passes(self):
        validate_image_upload(_upload("image/webp", "x.webp"), make_webp_bytes())

    def test_wrong_content_type_rejected(self):
        with pytest.raises(HTTPException) as exc:
            validate_image_upload(_upload("application/pdf"), make_jpeg_bytes())
        assert exc.value.status_code == 400
        assert "JPEG" in exc.value.detail

    def test_spoofed_content_type_caught_by_magic_bytes(self):
        """A non-image file uploaded with image/jpeg header should be rejected."""
        with pytest.raises(HTTPException) as exc:
            validate_image_upload(_upload("image/jpeg"), b"not an image at all")
        assert exc.value.status_code == 400
        assert "content does not match" in exc.value.detail

    def test_oversized_file_rejected(self):
        big = make_jpeg_bytes() + b"\x00" * (MAX_BYTES + 1)
        with pytest.raises(HTTPException) as exc:
            validate_image_upload(_upload("image/jpeg"), big)
        assert exc.value.status_code == 400
        assert "MB" in exc.value.detail

    def test_field_name_appears_in_error(self):
        with pytest.raises(HTTPException) as exc:
            validate_image_upload(_upload("application/pdf"), make_jpeg_bytes(), field_name="ID document")
        assert "ID document" in exc.value.detail

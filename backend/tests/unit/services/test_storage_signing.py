"""Unit tests for the local HMAC signed URL helpers in storage_service.

Production runs on S3 (boto3 presigned URLs); local development uses the
HMAC-signed `/private/{key}` route served by main.py. The signature binds
(key, expiry) to SECRET_KEY so it can't be tampered or replayed past expiry.
"""
from __future__ import annotations

import time
import urllib.parse as up

import pytest

from app.services.storage_service import (
    _make_local_signed_url,
    verify_local_signed_url,
)


class TestLocalSignedURL:
    def test_signed_url_round_trip(self):
        url = _make_local_signed_url("documents/abc.jpg", expires_in=60)
        parsed = up.urlparse(url)
        qs = up.parse_qs(parsed.query)
        assert verify_local_signed_url("documents/abc.jpg", int(qs["exp"][0]), qs["sig"][0]) is True

    def test_expired_signature_rejected(self):
        url = _make_local_signed_url("documents/abc.jpg", expires_in=-1)
        parsed = up.urlparse(url)
        qs = up.parse_qs(parsed.query)
        assert verify_local_signed_url("documents/abc.jpg", int(qs["exp"][0]), qs["sig"][0]) is False

    def test_tampered_signature_rejected(self):
        url = _make_local_signed_url("documents/abc.jpg", expires_in=60)
        parsed = up.urlparse(url)
        qs = up.parse_qs(parsed.query)
        bad = "0" * len(qs["sig"][0])
        assert verify_local_signed_url("documents/abc.jpg", int(qs["exp"][0]), bad) is False

    def test_tampered_key_rejected(self):
        url = _make_local_signed_url("documents/abc.jpg", expires_in=60)
        parsed = up.urlparse(url)
        qs = up.parse_qs(parsed.query)
        # Verify against a different key — signature is bound to the original key.
        assert verify_local_signed_url("documents/EVIL.jpg", int(qs["exp"][0]), qs["sig"][0]) is False

    def test_constant_time_compare_used(self):
        """Smoke check: the helper uses hmac.compare_digest, not '==' on the digest."""
        import inspect
        from app.services import storage_service
        src = inspect.getsource(storage_service.verify_local_signed_url)
        assert "compare_digest" in src

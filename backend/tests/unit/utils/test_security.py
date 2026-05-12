"""Unit tests for app.utils.security: bcrypt + JWT helpers.

Covers:
- Password hashing (deterministic verify, non-deterministic hash, wrong-password rejection).
- JWT creation/decoding round-trip with explicit `sub` payload.
- Expired tokens decode to None (no exception leak).
- Tokens signed with a different secret are rejected.
- Algorithm confusion: a token signed with HS256 cannot be replayed under "none".
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

import pytest
from jose import jwt

from app.config import settings
from app.utils.security import (
    create_access_token,
    decode_access_token,
    generate_verification_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_non_deterministic(self):
        """Same plaintext should produce different bcrypt hashes (salt randomness)."""
        h1 = hash_password("S3cret!23")
        h2 = hash_password("S3cret!23")
        assert h1 != h2

    def test_verify_correct_password(self):
        h = hash_password("CorrectHorseBatteryStaple")
        assert verify_password("CorrectHorseBatteryStaple", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("CorrectHorseBatteryStaple")
        assert verify_password("wrong", h) is False

    def test_verify_handles_unicode(self):
        h = hash_password("p@sswörd-🔥")
        assert verify_password("p@sswörd-🔥", h) is True

    def test_verify_empty_password(self):
        """Empty string is technically valid input for bcrypt - just confirm verify path doesn't crash."""
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("x", h) is False

    def test_hash_returns_str_not_bytes(self):
        h = hash_password("abc")
        assert isinstance(h, str)


class TestJWT:
    def test_round_trip(self):
        token = create_access_token("user-123")
        assert decode_access_token(token) == "user-123"

    def test_decode_returns_none_on_garbage(self):
        assert decode_access_token("not.a.jwt") is None
        assert decode_access_token("") is None

    def test_decode_returns_none_on_wrong_secret(self):
        """A token signed with a different secret must not be accepted."""
        bad = jwt.encode({"sub": "user-1", "exp": datetime.utcnow() + timedelta(minutes=10)},
                         "different-secret", algorithm=settings.ALGORITHM)
        assert decode_access_token(bad) is None

    def test_expired_token_returns_none(self):
        token = create_access_token("user-1", expires_delta=timedelta(seconds=-1))
        assert decode_access_token(token) is None

    def test_short_expiry_just_in_future(self):
        token = create_access_token("user-1", expires_delta=timedelta(seconds=5))
        assert decode_access_token(token) == "user-1"

    def test_none_algorithm_attack_rejected(self):
        """A token with alg=none must NOT be accepted (classic JWT vuln check)."""
        # python-jose refuses to encode with 'none' unless explicitly opted in;
        # we craft a token manually to simulate the attack.
        import base64, json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "attacker", "exp": 9999999999}).encode()).rstrip(b"=").decode()
        crafted = f"{header}.{payload}."
        assert decode_access_token(crafted) is None

    def test_subject_preserved_as_string(self):
        token = create_access_token("12345")
        assert decode_access_token(token) == "12345"


class TestVerificationToken:
    def test_token_is_url_safe(self):
        t = generate_verification_token()
        assert isinstance(t, str)
        # secrets.token_urlsafe(32) is at least 43 chars
        assert len(t) >= 32
        # URL-safe alphabet only
        import string
        assert set(t).issubset(set(string.ascii_letters + string.digits + "-_"))

    def test_tokens_are_unique(self):
        tokens = {generate_verification_token() for _ in range(100)}
        assert len(tokens) == 100

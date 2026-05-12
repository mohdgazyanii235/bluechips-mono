"""HTTP-level tests for `/api/auth/*` endpoints.

Covers:
- Registration: valid inputs, duplicate emails, weak passwords, malformed
  payloads, rate limiting (5/hour/IP).
- Login: success, wrong password, deactivated account, non-existent user,
  rate limiting (10/10min/IP+email).
- Email verification: valid token, expired token (>24h), already-used token,
  unknown token.
- Change password: success, wrong current password, weak new password,
  auth required.

All tests run against the rolled-back DB session fixture so they're fully
isolated. The autouse `_reset_rate_limiter` fixture in conftest clears the
in-memory limiter store between tests.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.escort import Escort
from app.utils.security import create_access_token


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegister:
    async def test_register_valid_returns_201(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "newperson@test.local",
            "password": "Password123!",
            "stage_name": "Lily",
        })
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "check your email" in body["message"].lower()

    async def test_register_persists_escort_unverified(self, client, db_session):
        await client.post("/api/auth/register", json={
            "email": "Unverified@TEST.local",  # mixed case to test lower-casing
            "password": "Password123!",
            "stage_name": "Mia",
        })
        # Email must be lower-cased on write
        result = await db_session.execute(select(Escort).where(Escort.email == "unverified@test.local"))
        escort = result.scalar_one_or_none()
        assert escort is not None
        assert escort.is_email_verified is False
        assert escort.verification_level == 0
        assert escort.email_verification_token is not None
        assert escort.email_verification_token_expires_at is not None
        # Token must expire within the next 24h, +/- 60s for clock drift
        delta = escort.email_verification_token_expires_at - datetime.utcnow()
        assert timedelta(hours=23, minutes=58) <= delta <= timedelta(hours=24, minutes=2)

    async def test_register_duplicate_email_rejected(self, client, escort_factory):
        await escort_factory(email="dupe@test.local")
        resp = await client.post("/api/auth/register", json={
            "email": "dupe@test.local",
            "password": "Password123!",
            "stage_name": "Anyone",
        })
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_duplicate_email_case_insensitive(self, client, escort_factory):
        await escort_factory(email="caser@test.local")
        resp = await client.post("/api/auth/register", json={
            "email": "CASER@test.local",
            "password": "Password123!",
            "stage_name": "Anyone",
        })
        assert resp.status_code == 400

    @pytest.mark.parametrize("password", ["", "short", "1234567"])
    async def test_register_rejects_short_password(self, client, password):
        resp = await client.post("/api/auth/register", json={
            "email": "tooshort@test.local",
            "password": password,
            "stage_name": "Mia",
        })
        assert resp.status_code == 422

    @pytest.mark.parametrize("name", ["", " ", "x", "  a  "])
    async def test_register_rejects_short_stage_name(self, client, name):
        resp = await client.post("/api/auth/register", json={
            "email": "short@test.local",
            "password": "Password123!",
            "stage_name": name,
        })
        assert resp.status_code == 422

    async def test_register_rejects_oversized_stage_name(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "long@test.local",
            "password": "Password123!",
            "stage_name": "x" * 51,
        })
        assert resp.status_code == 422

    @pytest.mark.parametrize("bad_email", ["not-an-email", "@", "a@", "@b.com", ""])
    async def test_register_rejects_invalid_email(self, client, bad_email):
        resp = await client.post("/api/auth/register", json={
            "email": bad_email,
            "password": "Password123!",
            "stage_name": "Mia",
        })
        assert resp.status_code == 422

    async def test_register_missing_fields(self, client):
        resp = await client.post("/api/auth/register", json={"email": "x@y.com"})
        assert resp.status_code == 422

    async def test_register_generates_unique_slug(self, client, db_session, escort_factory):
        await escort_factory(stage_name="Lily")
        await client.post("/api/auth/register", json={
            "email": "lily2@test.local",
            "password": "Password123!",
            "stage_name": "Lily",
        })
        result = await db_session.execute(select(Escort).where(Escort.email == "lily2@test.local"))
        new_escort = result.scalar_one()
        # Counter or randomised suffix to avoid the existing 'lily' slug
        assert new_escort.slug != ""
        # No slug collisions
        all_slugs = (await db_session.execute(select(Escort.slug))).scalars().all()
        assert len(all_slugs) == len(set(all_slugs))

    @pytest.mark.security
    async def test_register_rate_limited_after_five_per_hour(self, client):
        """6th registration from same IP within an hour is rejected with 429."""
        for i in range(5):
            r = await client.post("/api/auth/register", json={
                "email": f"rl{i}@test.local",
                "password": "Password123!",
                "stage_name": f"User{i}",
            })
            assert r.status_code == 201, f"Attempt {i+1} should succeed, got {r.status_code} {r.text}"

        r = await client.post("/api/auth/register", json={
            "email": "rl-blocked@test.local",
            "password": "Password123!",
            "stage_name": "Blocked",
        })
        assert r.status_code == 429
        assert "too many" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class TestLogin:
    async def test_login_success_returns_token(self, client, escort_factory):
        await escort_factory(email="login@test.local", password="MyP@ss123")
        resp = await client.post("/api/auth/login", json={
            "email": "login@test.local",
            "password": "MyP@ss123",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        assert body["stage_name"]
        assert body["escort_id"]

    async def test_login_wrong_password_returns_401(self, client, escort_factory):
        await escort_factory(email="wp@test.local", password="Correct123!")
        resp = await client.post("/api/auth/login", json={
            "email": "wp@test.local",
            "password": "Wrong123!",
        })
        assert resp.status_code == 401
        assert "incorrect" in resp.json()["detail"].lower()

    async def test_login_nonexistent_user_returns_401_same_message(self, client):
        """Login error should not leak whether the email exists."""
        resp = await client.post("/api/auth/login", json={
            "email": "ghost@test.local",
            "password": "Whatever123!",
        })
        assert resp.status_code == 401
        # Same generic message
        assert "incorrect" in resp.json()["detail"].lower()

    async def test_login_deactivated_account_returns_403(self, client, escort_factory):
        await escort_factory(email="dead@test.local", password="Pass1234!", is_active=False)
        resp = await client.post("/api/auth/login", json={
            "email": "dead@test.local",
            "password": "Pass1234!",
        })
        assert resp.status_code == 403
        assert "deactivated" in resp.json()["detail"].lower()

    async def test_login_email_case_insensitive(self, client, escort_factory):
        await escort_factory(email="case@test.local", password="Pass1234!")
        resp = await client.post("/api/auth/login", json={
            "email": "CASE@test.local",
            "password": "Pass1234!",
        })
        assert resp.status_code == 200

    @pytest.mark.security
    async def test_login_rate_limited_after_ten_per_ten_minutes(self, client, escort_factory):
        await escort_factory(email="rl-login@test.local", password="Correct1!")
        for _ in range(10):
            await client.post("/api/auth/login", json={
                "email": "rl-login@test.local",
                "password": "Wrong!",
            })
        resp = await client.post("/api/auth/login", json={
            "email": "rl-login@test.local",
            "password": "Correct1!",
        })
        assert resp.status_code == 429
        assert "10 minutes" in resp.json()["detail"]

    @pytest.mark.security
    async def test_login_rate_limit_per_email_isolated(self, client, escort_factory):
        """One email being rate-limited must not block another email from same IP."""
        await escort_factory(email="rl-A@test.local", password="A1!aaaaaa")
        await escort_factory(email="rl-B@test.local", password="B1!bbbbbb")
        for _ in range(10):
            await client.post("/api/auth/login", json={"email": "rl-A@test.local", "password": "x"})
        # User A is limited
        a = await client.post("/api/auth/login", json={"email": "rl-A@test.local", "password": "A1!aaaaaa"})
        assert a.status_code == 429
        # User B is unaffected — rate key includes the email
        b = await client.post("/api/auth/login", json={"email": "rl-B@test.local", "password": "B1!bbbbbb"})
        assert b.status_code == 200


# ---------------------------------------------------------------------------
# Verify email
# ---------------------------------------------------------------------------
class TestVerifyEmail:
    async def test_verify_valid_token(self, client, db_session, escort_factory):
        e = await escort_factory(
            is_email_verified=False,
            verification_level=0,
            email_verification_token="valid-tok-123",
            email_verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
        )
        resp = await client.post("/api/auth/verify-email?token=valid-tok-123")
        assert resp.status_code == 200
        assert "verified" in resp.json()["message"].lower()

        await db_session.refresh(e)
        assert e.is_email_verified is True
        assert e.verification_level == 1
        # Token cleared after use
        assert e.email_verification_token is None

    async def test_verify_unknown_token_400(self, client):
        resp = await client.post("/api/auth/verify-email?token=does-not-exist")
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()

    @pytest.mark.security
    async def test_verify_expired_token_400(self, client, escort_factory):
        await escort_factory(
            is_email_verified=False,
            email_verification_token="old-tok",
            email_verification_token_expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        resp = await client.post("/api/auth/verify-email?token=old-tok")
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    async def test_verify_already_verified_idempotent(self, client, escort_factory):
        await escort_factory(
            is_email_verified=True,
            email_verification_token="reused-tok",
            email_verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
        )
        resp = await client.post("/api/auth/verify-email?token=reused-tok")
        assert resp.status_code == 200
        assert "already verified" in resp.json()["message"].lower()

    @pytest.mark.security
    async def test_verify_token_single_use(self, client, escort_factory):
        """After first successful verify, the token must no longer match."""
        await escort_factory(
            is_email_verified=False,
            email_verification_token="single-use",
            email_verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
        )
        first = await client.post("/api/auth/verify-email?token=single-use")
        assert first.status_code == 200

        # Token cleared → second attempt with same token finds no escort
        second = await client.post("/api/auth/verify-email?token=single-use")
        assert second.status_code == 400

    @pytest.mark.security
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "x'; DROP TABLE escorts;--",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
        "%00",
        "a" * 1000,  # oversize
    ])
    async def test_verify_malicious_tokens_rejected(self, client, payload):
        """Tokens with SQLi/XSS/path payloads must just 400 — never error."""
        resp = await client.post(f"/api/auth/verify-email", params={"token": payload})
        # 400 (no match) or 422 (validation) are both acceptable; never 500
        assert resp.status_code in (400, 422), resp.text


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------
class TestChangePassword:
    async def test_change_password_success(self, client, escort_factory):
        e = await escort_factory(email="pw@test.local", password="OldPass1!")
        token = create_access_token(str(e.id))
        resp = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "OldPass1!", "new_password": "NewPass2!"},
        )
        assert resp.status_code == 200

        # New password works on login
        login = await client.post("/api/auth/login", json={
            "email": "pw@test.local", "password": "NewPass2!",
        })
        assert login.status_code == 200

    async def test_change_password_wrong_current_400(self, client, auth_headers):
        resp = await client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={"current_password": "wrong", "new_password": "NewPass2!"},
        )
        assert resp.status_code == 400
        assert "current password is incorrect" in resp.json()["detail"].lower()

    async def test_change_password_weak_new_password_422(self, client, auth_headers):
        resp = await client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={"current_password": "Password123!", "new_password": "short"},
        )
        assert resp.status_code == 422

    async def test_change_password_requires_auth(self, client):
        resp = await client.post("/api/auth/change-password", json={
            "current_password": "x", "new_password": "yyyyyyyy",
        })
        assert resp.status_code == 403  # HTTPBearer raises 403 when missing

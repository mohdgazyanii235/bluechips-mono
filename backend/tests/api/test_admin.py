"""HTTP-level tests for `/api/admin/*` non-verification endpoints.

Covers:
- POST /admin/login — rate-limited (5/15min/IP), wrong credentials, deactivated
  admin, generic error message (no email enumeration).
- GET /admin/stats — counts and totals.
- GET /admin/escorts — paginated escort listing.
- PATCH /admin/escorts/:id/toggle-active — flips is_active.
- Discount code management endpoints.
- Pricing management.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.discount import DiscountCode
from app.models.escort import Escort
from app.utils.security import create_access_token


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# POST /admin/login
# ---------------------------------------------------------------------------
class TestAdminLogin:
    async def test_login_success(self, client, admin):
        resp = await client.post("/api/admin/login", json={
            "email": admin.email, "password": "AdminPass123!",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["email"] == admin.email

    async def test_login_wrong_password_401(self, client, admin):
        resp = await client.post("/api/admin/login", json={
            "email": admin.email, "password": "wrong",
        })
        assert resp.status_code == 401
        assert "invalid credentials" in resp.json()["detail"].lower()

    async def test_login_unknown_email_401(self, client):
        resp = await client.post("/api/admin/login", json={
            "email": "no-such-admin@x.com", "password": "anything",
        })
        assert resp.status_code == 401
        # Same generic message — no enumeration
        assert "invalid credentials" in resp.json()["detail"].lower()

    async def test_login_deactivated_admin_403(self, client, admin_factory):
        a = await admin_factory(email="off@test.local")
        a.is_active = False
        resp = await client.post("/api/admin/login", json={
            "email": "off@test.local", "password": "AdminPass123!",
        })
        assert resp.status_code == 403

    @pytest.mark.security
    async def test_admin_login_rate_limited_5_per_15min(self, client, admin):
        for _ in range(5):
            await client.post("/api/admin/login", json={
                "email": admin.email, "password": "wrong",
            })
        # 6th attempt rate-limited regardless of correctness
        resp = await client.post("/api/admin/login", json={
            "email": admin.email, "password": "AdminPass123!",
        })
        assert resp.status_code == 429
        assert "15 minutes" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /admin/stats
# ---------------------------------------------------------------------------
class TestAdminStats:
    async def test_stats_returns_counts(self, client, db_session, escort_factory, admin_headers):
        await escort_factory(subscription_tier="free")
        await escort_factory(subscription_tier="premium")
        await escort_factory(subscription_tier="elite")
        body = (await client.get("/api/admin/stats", headers=admin_headers)).json()
        assert body["total_escorts"] == 3
        assert body["paid_escorts"] == 2
        assert body["pending_verifications"] == 0


# ---------------------------------------------------------------------------
# GET /admin/escorts
# ---------------------------------------------------------------------------
class TestListEscorts:
    async def test_lists_all_escorts_including_inactive(self, client, escort_factory, admin_headers):
        await escort_factory(stage_name="Active")
        await escort_factory(stage_name="Inactive", is_active=False)
        await escort_factory(stage_name="Unverified", is_email_verified=False, verification_level=0)
        body = (await client.get("/api/admin/escorts", headers=admin_headers)).json()
        names = {e["stage_name"] for e in body}
        # Admin sees all three (the public list excludes some, but admin sees everyone)
        assert names >= {"Active", "Inactive", "Unverified"}

    async def test_requires_admin_auth(self, client, auth_headers):
        # Escort JWT to admin route → admin lookup fails
        resp = await client.get("/api/admin/escorts", headers=auth_headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /admin/escorts/:id/toggle-active
# ---------------------------------------------------------------------------
class TestToggleActive:
    async def test_toggle_flips_state(self, client, db_session, escort, admin_headers):
        was = escort.is_active
        resp = await client.patch(f"/api/admin/escorts/{escort.id}/toggle-active", headers=admin_headers)
        assert resp.status_code == 200
        await db_session.refresh(escort)
        assert escort.is_active != was

    async def test_unknown_escort_404(self, client, admin_headers):
        import uuid
        resp = await client.patch(f"/api/admin/escorts/{uuid.uuid4()}/toggle-active", headers=admin_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Discount codes
# ---------------------------------------------------------------------------
class TestDiscountCodes:
    async def test_create_valid_code(self, client, db_session, admin_headers):
        resp = await client.post("/api/admin/discounts", headers=admin_headers, json={
            "code": "summer25",
            "name": "Summer 25% off",
            "percent_off": 25,
            "applicable_tiers": ["essential"],
            "duration_months": 3,
        })
        assert resp.status_code == 200
        result = await db_session.execute(select(DiscountCode).where(DiscountCode.code == "SUMMER25"))
        dc = result.scalar_one()
        assert dc.percent_off == 25
        assert dc.applicable_tiers == ["essential"]

    async def test_duplicate_code_400(self, client, db_session, admin_headers):
        db_session.add(DiscountCode(code="DUPE", name="x", percent_off=10, applicable_tiers=[], duration_months=1))
        await db_session.flush()
        resp = await client.post("/api/admin/discounts", headers=admin_headers, json={
            "code": "DUPE", "name": "y", "percent_off": 10, "duration_months": 1,
        })
        assert resp.status_code == 400

    @pytest.mark.parametrize("percent", [0, 101, -1, 200])
    async def test_invalid_percent_400(self, client, admin_headers, percent):
        resp = await client.post("/api/admin/discounts", headers=admin_headers, json={
            "code": "X", "name": "x", "percent_off": percent, "duration_months": 1,
        })
        assert resp.status_code == 400

    async def test_invalid_tiers_400(self, client, admin_headers):
        resp = await client.post("/api/admin/discounts", headers=admin_headers, json={
            "code": "X", "name": "x", "percent_off": 10, "duration_months": 1,
            "applicable_tiers": ["BOGUS_TIER"],
        })
        assert resp.status_code == 400

    async def test_deactivate_code(self, client, db_session, admin_headers):
        dc = DiscountCode(code="OFF", name="x", percent_off=10, applicable_tiers=[], duration_months=1)
        db_session.add(dc)
        await db_session.flush()
        resp = await client.patch(f"/api/admin/discounts/{dc.id}/deactivate", headers=admin_headers)
        assert resp.status_code == 200
        await db_session.refresh(dc)
        assert dc.is_active is False

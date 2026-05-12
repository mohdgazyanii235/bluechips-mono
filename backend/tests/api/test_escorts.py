"""HTTP-level tests for `/api/escorts/*` endpoints.

Covers:
- GET /escorts list with every filter
- Sort ordering (elite > premium > essential > free; verif desc; available_now desc)
- Pagination
- Visibility rules (is_active AND is_approved AND is_email_verified)
- GET /escorts/me (dashboard with private fields)
- PUT /escorts/me (profile update with phone/age validators)
- PATCH /escorts/me/available-now toggle
- GET /escorts/:slug (public profile, increments view count)
- POST /escorts/:slug/contact-click
- Couple profile_type filter
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.escort import Escort, EscortService


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# GET /escorts (public list)
# ---------------------------------------------------------------------------
class TestListEscorts:
    async def test_empty_list(self, client):
        resp = await client.get("/api/escorts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["page"] == 1

    async def test_lists_visible_escort(self, client, escort_factory):
        await escort_factory(stage_name="Visible")
        resp = await client.get("/api/escorts")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["stage_name"] == "Visible"

    async def test_visibility_rules_exclude_unverified(self, client, escort_factory):
        await escort_factory(stage_name="Visible")
        await escort_factory(stage_name="Inactive", is_active=False)
        await escort_factory(stage_name="NotApproved", is_approved=False)
        await escort_factory(stage_name="NotEmail", is_email_verified=False, verification_level=0)
        resp = await client.get("/api/escorts")
        names = {e["stage_name"] for e in resp.json()["items"]}
        assert names == {"Visible"}

    async def test_sort_order_tier_priority(self, client, escort_factory):
        """elite > premium > essential > free, then verification_level desc."""
        await escort_factory(stage_name="FreeOne", subscription_tier="free")
        await escort_factory(stage_name="EliteOne", subscription_tier="elite", verification_level=3)
        await escort_factory(stage_name="PremiumOne", subscription_tier="premium", verification_level=2)
        await escort_factory(stage_name="EssentialOne", subscription_tier="essential", verification_level=1)
        resp = await client.get("/api/escorts")
        names = [e["stage_name"] for e in resp.json()["items"]]
        assert names == ["EliteOne", "PremiumOne", "EssentialOne", "FreeOne"]

    async def test_sort_within_same_tier_by_verification(self, client, escort_factory):
        await escort_factory(stage_name="P_low",  subscription_tier="premium", verification_level=1)
        await escort_factory(stage_name="P_high", subscription_tier="premium", verification_level=3)
        await escort_factory(stage_name="P_mid",  subscription_tier="premium", verification_level=2)
        resp = await client.get("/api/escorts")
        names = [e["stage_name"] for e in resp.json()["items"]]
        assert names == ["P_high", "P_mid", "P_low"]

    async def test_sort_within_same_tier_and_verif_available_now_first(self, client, escort_factory):
        await escort_factory(stage_name="P_off", subscription_tier="premium", verification_level=2, available_now=False)
        await escort_factory(stage_name="P_on",  subscription_tier="premium", verification_level=2, available_now=True)
        resp = await client.get("/api/escorts")
        names = [e["stage_name"] for e in resp.json()["items"]]
        assert names == ["P_on", "P_off"]

    @pytest.mark.parametrize("filter_kwargs,db_kwargs,expect_in_results", [
        ({"ethnicity": "European"}, {"ethnicity": "European"}, True),
        ({"ethnicity": "European"}, {"ethnicity": "Asian"}, False),
        ({"availability_type": "incall"}, {"availability_type": "incall"}, True),
        ({"availability_type": "incall"}, {"availability_type": "outcall"}, False),
        ({"min_age": 25}, {"age": 30}, True),
        ({"min_age": 25}, {"age": 22}, False),
        ({"max_age": 30}, {"age": 22}, True),
        ({"max_age": 30}, {"age": 40}, False),
        ({"min_rate": 100}, {"rate_1hour": 150}, True),
        ({"min_rate": 100}, {"rate_1hour": 80}, False),
        ({"max_rate": 200}, {"rate_1hour": 150}, True),
        ({"max_rate": 200}, {"rate_1hour": 300}, False),
        ({"std_tested": "true"}, {"std_tested": True}, True),
        ({"std_tested": "false"}, {"std_tested": True}, False),
        ({"available_now": "true"}, {"available_now": True}, True),
        ({"available_now": "true"}, {"available_now": False}, False),
        ({"blue_tick_only": "true"}, {"verification_level": 3}, True),
        ({"blue_tick_only": "true"}, {"verification_level": 2}, False),
        ({"profile_type": "couple"}, {"profile_type": "couple"}, True),
        ({"profile_type": "couple"}, {"profile_type": "individual"}, False),
        ({"profile_type": "individual"}, {"profile_type": "individual"}, True),
    ])
    async def test_filters(self, client, escort_factory, filter_kwargs, db_kwargs, expect_in_results):
        await escort_factory(stage_name="Target", **db_kwargs)
        resp = await client.get("/api/escorts", params=filter_kwargs)
        names = [e["stage_name"] for e in resp.json()["items"]]
        if expect_in_results:
            assert "Target" in names
        else:
            assert "Target" not in names

    async def test_filter_by_borough_slug(self, client, escort_factory, borough_factory):
        b1 = await borough_factory("Mayfair", "mayfair")
        b2 = await borough_factory("Soho", "soho")
        await escort_factory(stage_name="InMayfair", borough_id=b1.id)
        await escort_factory(stage_name="InSoho", borough_id=b2.id)
        resp = await client.get("/api/escorts", params={"borough_slug": "mayfair"})
        names = [e["stage_name"] for e in resp.json()["items"]]
        assert names == ["InMayfair"]

    async def test_filter_by_borough_slug_unknown_returns_all(self, client, escort_factory):
        """Unknown borough slug silently no-ops; doesn't filter."""
        await escort_factory(stage_name="One")
        resp = await client.get("/api/escorts", params={"borough_slug": "nowhere"})
        # The router only applies the borough filter if the borough lookup succeeds
        assert resp.json()["total"] == 1

    async def test_filter_by_service_tag(self, client, db_session, escort_factory):
        e_gfe = await escort_factory(stage_name="HasGFE")
        e_other = await escort_factory(stage_name="HasOther")
        db_session.add(EscortService(escort_id=e_gfe.id, tag="GFE"))
        db_session.add(EscortService(escort_id=e_other.id, tag="Massage"))
        await db_session.flush()

        resp = await client.get("/api/escorts", params={"service_tag": "GFE"})
        names = [e["stage_name"] for e in resp.json()["items"]]
        assert names == ["HasGFE"]

    async def test_pagination_basic(self, client, escort_factory):
        for i in range(5):
            await escort_factory(stage_name=f"User{i:02d}")
        resp = await client.get("/api/escorts", params={"page": 1, "per_page": 2})
        body = resp.json()
        assert body["total"] == 5
        assert body["pages"] == 3
        assert len(body["items"]) == 2

    async def test_pagination_invalid_params(self, client):
        # page < 1 → 422
        r = await client.get("/api/escorts", params={"page": 0})
        assert r.status_code == 422
        # per_page > 48 → 422
        r = await client.get("/api/escorts", params={"per_page": 100})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /escorts/me
# ---------------------------------------------------------------------------
class TestMyProfile:
    async def test_requires_auth(self, client):
        resp = await client.get("/api/escorts/me")
        assert resp.status_code == 403  # HTTPBearer raises 403 on missing creds

    async def test_returns_private_fields(self, client, escort, auth_headers):
        resp = await client.get("/api/escorts/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == escort.email
        assert "photo_limit" in body
        # Default tier 'free' allows 3 photos
        assert body["photo_limit"] == 3
        assert "blue_tick_stripe_subscription_id" in body
        assert "stripe_subscription_id" in body
        assert "referral_code" in body

    async def test_photo_limit_changes_with_tier(self, client, escort_factory):
        from app.utils.security import create_access_token
        e = await escort_factory(subscription_tier="premium")
        headers = {"Authorization": f"Bearer {create_access_token(str(e.id))}"}
        resp = await client.get("/api/escorts/me", headers=headers)
        assert resp.json()["photo_limit"] == 50

    async def test_invalid_token_returns_401(self, client):
        resp = await client.get("/api/escorts/me", headers={"Authorization": "Bearer not-a-token"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /escorts/me
# ---------------------------------------------------------------------------
class TestUpdateMyProfile:
    async def test_update_basic_fields(self, client, db_session, escort, auth_headers, borough):
        resp = await client.put("/api/escorts/me", headers=auth_headers, json={
            "age": 28,
            "ethnicity": "European",
            "about_me": "Hello world",
            "availability_type": "both",
            "borough_id": str(borough.id),
        })
        assert resp.status_code == 200, resp.text
        await db_session.refresh(escort)
        assert escort.age == 28
        assert escort.ethnicity == "European"
        assert escort.about_me == "Hello world"
        assert escort.profile_complete is True  # All 4 required set

    async def test_partial_update_does_not_overwrite_unset_fields(self, client, db_session, escort_factory):
        from app.utils.security import create_access_token
        e = await escort_factory(age=30, ethnicity="Asian")
        headers = {"Authorization": f"Bearer {create_access_token(str(e.id))}"}
        await client.put("/api/escorts/me", headers=headers, json={"age": 31})
        await db_session.refresh(e)
        assert e.age == 31
        assert e.ethnicity == "Asian"  # unchanged

    @pytest.mark.parametrize("age", [17, 0, -1, 100, 999])
    async def test_invalid_age_rejected(self, client, auth_headers, age):
        resp = await client.put("/api/escorts/me", headers=auth_headers, json={"age": age})
        assert resp.status_code == 422

    @pytest.mark.parametrize("phone", ["+44 7700 900000", "+447700900000", "07700900000"])
    async def test_valid_phone_accepted(self, client, auth_headers, phone):
        resp = await client.put("/api/escorts/me", headers=auth_headers, json={"phone_number": phone})
        assert resp.status_code == 200

    @pytest.mark.parametrize("phone", ["abc123", "<script>", "phone!!", "x" * 30])
    async def test_invalid_phone_rejected(self, client, auth_headers, phone):
        resp = await client.put("/api/escorts/me", headers=auth_headers, json={"phone_number": phone})
        assert resp.status_code == 422

    async def test_about_me_truncated_to_600(self, client, db_session, escort, auth_headers):
        long = "x" * 1000
        await client.put("/api/escorts/me", headers=auth_headers, json={"about_me": long})
        await db_session.refresh(escort)
        assert len(escort.about_me) == 600

    async def test_service_tags_replaced_not_appended(self, client, db_session, escort, auth_headers):
        await client.put("/api/escorts/me", headers=auth_headers, json={"service_tags": ["GFE", "Massage"]})
        await client.put("/api/escorts/me", headers=auth_headers, json={"service_tags": ["Massage"]})
        result = await db_session.execute(select(EscortService.tag).where(EscortService.escort_id == escort.id))
        tags = [r[0] for r in result.fetchall()]
        assert tags == ["Massage"]

    async def test_unknown_service_tags_dropped(self, client, db_session, escort, auth_headers):
        await client.put("/api/escorts/me", headers=auth_headers, json={
            "service_tags": ["GFE", "BOGUS_NOT_IN_LIST", "Massage"],
        })
        result = await db_session.execute(select(EscortService.tag).where(EscortService.escort_id == escort.id))
        tags = {r[0] for r in result.fetchall()}
        assert tags == {"GFE", "Massage"}


# ---------------------------------------------------------------------------
# PATCH /escorts/me/available-now
# ---------------------------------------------------------------------------
class TestAvailableNowToggle:
    async def test_toggle_on(self, client, db_session, escort, auth_headers):
        resp = await client.patch("/api/escorts/me/available-now", headers=auth_headers, params={"available": "true"})
        assert resp.status_code == 200
        assert "Available Now" in resp.json()["message"]
        await db_session.refresh(escort)
        assert escort.available_now is True

    async def test_toggle_off(self, client, db_session, escort_factory):
        from app.utils.security import create_access_token
        e = await escort_factory(available_now=True)
        headers = {"Authorization": f"Bearer {create_access_token(str(e.id))}"}
        resp = await client.patch("/api/escorts/me/available-now", headers=headers, params={"available": "false"})
        assert resp.status_code == 200
        assert "Offline" in resp.json()["message"]
        await db_session.refresh(e)
        assert e.available_now is False


# ---------------------------------------------------------------------------
# GET /escorts/:slug (public)
# ---------------------------------------------------------------------------
class TestPublicProfile:
    async def test_returns_full_profile(self, client, escort_factory, borough):
        e = await escort_factory(
            stage_name="Sasha", age=25, about_me="Hello", borough_id=borough.id,
            whatsapp_number="+447700900000", phone_number="+447700900001",
        )
        resp = await client.get(f"/api/escorts/{e.slug}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["stage_name"] == "Sasha"
        assert body["about_me"] == "Hello"
        # Contact fields must appear (these were the bug in the FIXED list)
        assert body["whatsapp_number"] == "+447700900000"
        assert body["phone_number"] == "+447700900001"

    async def test_404_for_unknown_slug(self, client):
        resp = await client.get("/api/escorts/does-not-exist")
        assert resp.status_code == 404

    async def test_404_for_deactivated_escort(self, client, escort_factory):
        e = await escort_factory(is_active=False)
        resp = await client.get(f"/api/escorts/{e.slug}")
        assert resp.status_code == 404

    async def test_404_for_unapproved_escort(self, client, escort_factory):
        e = await escort_factory(is_approved=False)
        resp = await client.get(f"/api/escorts/{e.slug}")
        assert resp.status_code == 404

    async def test_view_count_incremented(self, client, db_session, escort):
        before = escort.profile_views
        await client.get(f"/api/escorts/{escort.slug}")
        await db_session.refresh(escort)
        assert escort.profile_views == before + 1

    async def test_std_tested_hidden_for_free_tier(self, client, escort_factory):
        """STD-tested badge is a premium/elite feature only."""
        e = await escort_factory(std_tested=True, std_tested_date="Jan 2026", subscription_tier="essential")
        body = (await client.get(f"/api/escorts/{e.slug}")).json()
        assert body["std_tested"] is False
        assert body["std_tested_date"] is None

    async def test_std_tested_visible_for_premium(self, client, escort_factory):
        e = await escort_factory(std_tested=True, std_tested_date="Jan 2026", subscription_tier="premium")
        body = (await client.get(f"/api/escorts/{e.slug}")).json()
        assert body["std_tested"] is True
        assert body["std_tested_date"] == "Jan 2026"


# ---------------------------------------------------------------------------
# POST /escorts/:slug/contact-click
# ---------------------------------------------------------------------------
class TestContactClick:
    async def test_increments_count(self, client, db_session, escort):
        before = escort.contact_clicks
        resp = await client.post(f"/api/escorts/{escort.slug}/contact-click")
        assert resp.status_code == 200
        await db_session.refresh(escort)
        assert escort.contact_clicks == before + 1

    async def test_unknown_slug_returns_ok_silently(self, client):
        """Tracking endpoint shouldn't reveal whether the slug exists."""
        resp = await client.post("/api/escorts/nobody/contact-click")
        assert resp.status_code == 200

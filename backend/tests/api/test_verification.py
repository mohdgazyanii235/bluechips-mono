"""HTTP-level tests for `/api/verification/*` and admin verification flow.

The verification module has a strict state machine:
- Identity (level 2) requires an active paid sub.
- Blue Tick (level 3) requires identity-verified AND an active blue_tick sub.
- Each level may have at most one pending submission at a time.
- Admin approval promotes verification_level; admin rejection cancels the
  responsible Stripe subscription and refunds the most recent invoice.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.verification import Verification
from app.utils.security import create_access_token
from tests.conftest import make_jpeg_bytes


pytestmark = pytest.mark.asyncio


def _headers_for(escort) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(escort.id))}"}


def _file_part(name: str = "id.jpg") -> tuple:
    return (name, make_jpeg_bytes(), "image/jpeg")


# ---------------------------------------------------------------------------
# POST /verification/submit-identity-documents
# ---------------------------------------------------------------------------
class TestSubmitIdentity:
    async def test_paid_subscriber_can_submit(self, client, db_session, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential", verification_level=1)
        files = {"id_document": _file_part("id.jpg"), "selfie": _file_part("self.jpg")}
        resp = await client.post("/api/verification/submit-identity-documents",
                                 headers=_headers_for(e), files=files)
        assert resp.status_code == 201, resp.text
        result = await db_session.execute(select(Verification).where(Verification.escort_id == e.id))
        v = result.scalar_one()
        assert v.level == 2
        assert v.status == "pending"
        assert v.id_document_url is not None
        assert v.selfie_url is not None

    async def test_free_tier_rejected(self, client, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="free", verification_level=1)
        files = {"id_document": _file_part(), "selfie": _file_part()}
        resp = await client.post("/api/verification/submit-identity-documents",
                                 headers=_headers_for(e), files=files)
        assert resp.status_code == 400
        assert "paid subscribers" in resp.json()["detail"].lower()

    async def test_already_verified_rejected(self, client, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="premium", verification_level=2)
        files = {"id_document": _file_part(), "selfie": _file_part()}
        resp = await client.post("/api/verification/submit-identity-documents",
                                 headers=_headers_for(e), files=files)
        assert resp.status_code == 400

    async def test_duplicate_pending_rejected(self, client, db_session, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential", verification_level=1)
        db_session.add(Verification(escort_id=e.id, level=2, status="pending"))
        await db_session.flush()
        files = {"id_document": _file_part(), "selfie": _file_part()}
        resp = await client.post("/api/verification/submit-identity-documents",
                                 headers=_headers_for(e), files=files)
        assert resp.status_code == 400
        assert "pending" in resp.json()["detail"].lower()

    @pytest.mark.security
    async def test_id_document_must_pass_magic_byte_check(self, client, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential")
        files = {
            "id_document": ("evil.pdf", b"%PDF-1.4 fake", "image/jpeg"),
            "selfie": _file_part(),
        }
        resp = await client.post("/api/verification/submit-identity-documents",
                                 headers=_headers_for(e), files=files)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /verification/submit-blue-tick-documents
# ---------------------------------------------------------------------------
class TestSubmitBlueTick:
    async def test_requires_blue_tick_subscription(self, client, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential", verification_level=2,
                                 blue_tick_stripe_subscription_id=None)
        resp = await client.post("/api/verification/submit-blue-tick-documents",
                                 headers=_headers_for(e),
                                 files={"match_selfie": _file_part()})
        assert resp.status_code == 400
        assert "blue tick" in resp.json()["detail"].lower()

    async def test_requires_identity_first(self, client, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential", verification_level=1,
                                 blue_tick_stripe_subscription_id="sub_bt")
        resp = await client.post("/api/verification/submit-blue-tick-documents",
                                 headers=_headers_for(e),
                                 files={"match_selfie": _file_part()})
        assert resp.status_code == 400
        assert "identity verification" in resp.json()["detail"].lower()

    async def test_success_creates_verification(self, client, db_session, escort_factory, mock_storage):
        e = await escort_factory(subscription_tier="essential", verification_level=2,
                                 blue_tick_stripe_subscription_id="sub_bt")
        resp = await client.post("/api/verification/submit-blue-tick-documents",
                                 headers=_headers_for(e),
                                 files={"match_selfie": _file_part()})
        assert resp.status_code == 201
        v = (await db_session.execute(select(Verification).where(Verification.escort_id == e.id))).scalar_one()
        assert v.level == 3
        assert v.status == "pending"
        assert v.match_selfie_url is not None


# ---------------------------------------------------------------------------
# GET /verification/status
# ---------------------------------------------------------------------------
class TestVerificationStatus:
    async def test_status_with_pending_submission(self, client, db_session, escort, auth_headers):
        db_session.add(Verification(escort_id=escort.id, level=2, status="pending"))
        await db_session.flush()
        body = (await client.get("/api/verification/status", headers=auth_headers)).json()
        assert body["pending_submission"] is not None
        assert body["pending_submission"]["level"] == 2

    async def test_status_lists_all_submissions(self, client, db_session, escort, auth_headers):
        db_session.add_all([
            Verification(escort_id=escort.id, level=2, status="approved"),
            Verification(escort_id=escort.id, level=3, status="pending"),
        ])
        await db_session.flush()
        body = (await client.get("/api/verification/status", headers=auth_headers)).json()
        assert len(body["submissions"]) == 2


# ---------------------------------------------------------------------------
# Admin approve / reject (verification flow)
# ---------------------------------------------------------------------------
class TestAdminVerificationFlow:
    async def test_pending_list_visible_to_admin(self, client, db_session, escort, admin_headers):
        db_session.add(Verification(escort_id=escort.id, level=2, status="pending"))
        await db_session.flush()
        body = (await client.get("/api/admin/verifications/pending", headers=admin_headers)).json()
        assert body["total"] == 1
        assert body["items"][0]["escort"]["email"] == escort.email

    async def test_approve_identity_promotes_level(
        self, client, db_session, escort_factory, admin_headers, mock_stripe,
    ):
        e = await escort_factory(subscription_tier="essential", verification_level=1)
        v = Verification(escort_id=e.id, level=2, status="pending")
        db_session.add(v)
        await db_session.flush()

        resp = await client.post(f"/api/admin/verifications/{v.id}/approve", headers=admin_headers)
        assert resp.status_code == 200, resp.text

        await db_session.refresh(e)
        await db_session.refresh(v)
        assert e.verification_level == 2
        assert v.status == "approved"

    async def test_approve_identity_for_premium_grants_blue_tick(
        self, client, db_session, escort_factory, admin_headers, mock_stripe,
    ):
        """Premium tier: approval of identity automatically grants Blue Tick."""
        e = await escort_factory(subscription_tier="premium", verification_level=1, blue_tick_active=False)
        v = Verification(escort_id=e.id, level=2, status="pending")
        db_session.add(v)
        await db_session.flush()

        await client.post(f"/api/admin/verifications/{v.id}/approve", headers=admin_headers)
        await db_session.refresh(e)
        assert e.blue_tick_active is True

    async def test_approve_already_decided_400(
        self, client, db_session, escort, admin_headers, mock_stripe,
    ):
        v = Verification(escort_id=escort.id, level=2, status="approved")
        db_session.add(v)
        await db_session.flush()
        resp = await client.post(f"/api/admin/verifications/{v.id}/approve", headers=admin_headers)
        assert resp.status_code == 400

    async def test_reject_identity_refunds_and_cancels(
        self, client, db_session, escort_factory, admin_headers, mock_stripe,
    ):
        e = await escort_factory(
            subscription_tier="essential", verification_level=1,
            stripe_customer_id="cus_x", stripe_subscription_id="sub_x",
        )
        v = Verification(escort_id=e.id, level=2, status="pending")
        db_session.add(v)
        await db_session.flush()

        # Stripe invoices.list returns an invoice with a charge
        mock_stripe.inv_list.return_value = {"data": [{"id": "in_1", "charge": "ch_1"}]}

        resp = await client.post(
            f"/api/admin/verifications/{v.id}/reject",
            headers=admin_headers,
            json={"admin_notes": "Document unclear"},
        )
        assert resp.status_code == 200

        # Refund created and subscription cancelled
        mock_stripe.refund_create.assert_called_once()
        mock_stripe.sub_delete.assert_called_once()

        await db_session.refresh(e)
        await db_session.refresh(v)
        assert v.status == "rejected"
        assert v.admin_notes == "Document unclear"
        assert e.subscription_tier == "free"
        assert e.stripe_subscription_id is None

    async def test_reject_blue_tick_only_cancels_blue_tick(
        self, client, db_session, escort_factory, admin_headers, mock_stripe,
    ):
        e = await escort_factory(
            subscription_tier="essential", verification_level=2, blue_tick_active=False,
            stripe_customer_id="cus_x", stripe_subscription_id="sub_main",
            blue_tick_stripe_subscription_id="sub_bt",
        )
        v = Verification(escort_id=e.id, level=3, status="pending")
        db_session.add(v)
        await db_session.flush()
        mock_stripe.inv_list.return_value = {"data": [{"id": "in_1", "charge": "ch_1"}]}

        resp = await client.post(
            f"/api/admin/verifications/{v.id}/reject",
            headers=admin_headers,
            json={"admin_notes": "Mismatch"},
        )
        assert resp.status_code == 200

        await db_session.refresh(e)
        # Main subscription unaffected
        assert e.subscription_tier == "essential"
        assert e.stripe_subscription_id == "sub_main"
        # Blue tick cleared
        assert e.blue_tick_active is False
        assert e.blue_tick_stripe_subscription_id is None

    @pytest.mark.security
    async def test_admin_endpoints_require_admin_jwt(self, client, db_session, escort, auth_headers):
        """An escort's bearer must not authenticate as admin."""
        db_session.add(Verification(escort_id=escort.id, level=2, status="pending"))
        await db_session.flush()
        # Escort token sent to admin route → 401 (admin lookup misses)
        resp = await client.get("/api/admin/verifications/pending", headers=auth_headers)
        assert resp.status_code == 401

    async def test_get_verification_detail_returns_signed_urls(
        self, client, db_session, escort, admin_headers, mock_storage,
    ):
        v = Verification(
            escort_id=escort.id, level=2, status="pending",
            id_document_url="documents/abc.jpg",
            selfie_url="documents/def.jpg",
        )
        db_session.add(v)
        await db_session.flush()
        body = (await client.get(f"/api/admin/verifications/{v.id}", headers=admin_headers)).json()
        # Signed URLs include /private/ for the local-storage path
        assert "/private/" in body["id_document_signed_url"]
        assert "exp=" in body["id_document_signed_url"]
        assert "sig=" in body["id_document_signed_url"]

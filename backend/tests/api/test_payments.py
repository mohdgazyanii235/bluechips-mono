"""HTTP-level tests for `/api/payments/*` and `/api/webhooks/stripe`.

External Stripe calls are mocked via the `mock_stripe` fixture (see conftest)
so no network IO happens. Tests focus on:

- POST /payments/checkout — creates Stripe Checkout session, persists
  stripe_customer_id, blocks if a verification is pending, validates tier/billing.
- POST /payments/upgrade-tier — modifies existing subscription in-place via
  `client.subscriptions.update(...)`, not by creating a new one (that was the
  double-charge bug). Charges pro-rata, updates DB tier.
- POST /payments/blue-tick-checkout — two line_items (setup + monthly), rejects
  if already has Blue Tick or premium/elite tier (Blue Tick is included).
- GET /payments/subscription — joins blue tick and main sub records.
- GET /payments/invoices — calls Stripe invoices.list with the right customer.
- POST /payments/cancel — sets cancel_at_period_end=True, marks DB 'cancelling'.
- POST /payments/cancel-blue-tick — same for Blue Tick.
- POST /webhooks/stripe — signature verified, idempotent via WebhookEvent,
  customer-id cross-check in checkout.session.completed,
  subscription.updated, subscription.deleted.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.subscription import Subscription
from app.models.verification import Verification
from app.models.webhook_event import WebhookEvent
from app.utils.security import create_access_token


pytestmark = pytest.mark.asyncio


def _headers_for(escort) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(escort.id))}"}


# ---------------------------------------------------------------------------
# POST /payments/checkout
# ---------------------------------------------------------------------------
class TestCheckout:
    async def test_returns_checkout_url(self, client, db_session, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1, is_email_verified=True)
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["url"].startswith("https://checkout.stripe.com/")
        mock_stripe.client.checkout.sessions.create.assert_called_once()
        # Customer was created
        mock_stripe.client.customers.create.assert_called_once()
        await db_session.refresh(e)
        assert e.stripe_customer_id == "cus_test_new"

    async def test_reuses_existing_stripe_customer(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_existing")
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 200
        mock_stripe.client.customers.create.assert_not_called()
        # The session params should reference the existing customer
        call_kwargs = mock_stripe.client.checkout.sessions.create.call_args.kwargs
        params = call_kwargs.get("params") or mock_stripe.client.checkout.sessions.create.call_args.args[0]
        assert params["customer"] == "cus_existing"

    @pytest.mark.parametrize("tier", ["bogus", "FREE", "", "VIP"])
    async def test_invalid_tier_400(self, client, escort, platform_config, mock_stripe, tier):
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(escort),
            json={"tier": tier, "billing": "monthly"},
        )
        assert resp.status_code == 400

    async def test_invalid_billing_400(self, client, escort, platform_config, mock_stripe):
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(escort),
            json={"tier": "essential", "billing": "weekly"},
        )
        assert resp.status_code == 400

    async def test_blocked_when_verification_pending(self, client, db_session, escort, platform_config, mock_stripe):
        db_session.add(Verification(escort_id=escort.id, level=2, status="pending"))
        await db_session.flush()
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(escort),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 409

    async def test_unverified_email_403(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(is_email_verified=False)
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 403

    async def test_annual_billing_missing_price_returns_503(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1)
        resp = await client.post(
            "/api/payments/checkout",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "annual"},
        )
        # platform_config fixture only sets monthly stripe ids
        assert resp.status_code == 503
        assert "annual" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /payments/upgrade-tier
# ---------------------------------------------------------------------------
class TestUpgradeTier:
    async def test_upgrade_modifies_existing_subscription_in_place(
        self, client, db_session, escort_factory, platform_config, mock_stripe,
    ):
        """The fix for the double-charge bug: must call subscriptions.update, not create."""
        e = await escort_factory(
            verification_level=2,
            subscription_tier="essential",
            stripe_customer_id="cus_x",
            stripe_subscription_id="sub_x",
        )
        db_session.add(Subscription(
            escort_id=e.id, tier="essential", status="active",
            stripe_subscription_id="sub_x", amount_gbp=1199,
        ))
        await db_session.flush()

        resp = await client.post(
            "/api/payments/upgrade-tier",
            headers=_headers_for(e),
            json={"tier": "premium", "billing": "monthly"},
        )
        assert resp.status_code == 200, resp.text
        # The crucial assertion: subscriptions.update was called (NOT create).
        mock_stripe.client.subscriptions.update.assert_called()
        mock_stripe.client.checkout.sessions.create.assert_not_called()

        await db_session.refresh(e)
        assert e.subscription_tier == "premium"

    async def test_upgrade_no_existing_subscription_400(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1, subscription_tier="free", stripe_subscription_id=None)
        resp = await client.post(
            "/api/payments/upgrade-tier",
            headers=_headers_for(e),
            json={"tier": "premium", "billing": "monthly"},
        )
        assert resp.status_code == 400

    async def test_upgrade_same_plan_400(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=2, subscription_tier="essential", stripe_subscription_id="sub_x")
        # Mock the retrieve to return the SAME price as essential_monthly
        mock_stripe.client.subscriptions.retrieve.return_value = {
            "id": "sub_x",
            "items": {"data": [{
                "id": "si_x",
                "price": {"id": "price_test_essential_m", "recurring": {"interval": "month"}},
            }]},
        }
        resp = await client.post(
            "/api/payments/upgrade-tier",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 400
        assert "already on this plan" in resp.json()["detail"].lower()

    async def test_downgrade_no_immediate_charge(
        self, client, db_session, escort_factory, platform_config, mock_stripe,
    ):
        e = await escort_factory(
            verification_level=2, subscription_tier="premium",
            stripe_customer_id="cus_x", stripe_subscription_id="sub_x",
        )
        db_session.add(Subscription(
            escort_id=e.id, tier="premium", status="active", stripe_subscription_id="sub_x",
        ))
        await db_session.flush()
        mock_stripe.client.subscriptions.retrieve.return_value = {
            "id": "sub_x",
            "items": {"data": [{
                "id": "si_x", "price": {"id": "price_test_premium_m", "recurring": {"interval": "month"}},
            }]},
        }
        resp = await client.post(
            "/api/payments/upgrade-tier",
            headers=_headers_for(e),
            json={"tier": "essential", "billing": "monthly"},
        )
        assert resp.status_code == 200
        # No invoice charge for downgrade
        mock_stripe.client.invoices.create.assert_not_called()
        # Tier remains premium until billing period end (pending_tier set instead)
        await db_session.refresh(e)
        assert e.subscription_tier == "premium"


# ---------------------------------------------------------------------------
# POST /payments/blue-tick-checkout
# ---------------------------------------------------------------------------
class TestBlueTickCheckout:
    async def test_creates_session_with_two_line_items(
        self, client, escort_factory, platform_config, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, subscription_tier="essential")
        resp = await client.post("/api/payments/blue-tick-checkout", headers=_headers_for(e))
        assert resp.status_code == 200
        call = mock_stripe.client.checkout.sessions.create.call_args
        params = call.kwargs.get("params") or call.args[0]
        # Setup price + monthly price both present
        assert len(params["line_items"]) == 2

    async def test_rejected_if_premium_or_elite(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1, subscription_tier="premium")
        resp = await client.post("/api/payments/blue-tick-checkout", headers=_headers_for(e))
        assert resp.status_code == 400
        assert "included free" in resp.json()["detail"].lower()

    async def test_rejected_if_already_subscribed(self, client, escort_factory, platform_config, mock_stripe):
        e = await escort_factory(verification_level=1, blue_tick_stripe_subscription_id="sub_bt")
        resp = await client.post("/api/payments/blue-tick-checkout", headers=_headers_for(e))
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /payments/subscription & /payments/invoices
# ---------------------------------------------------------------------------
class TestSubscriptionInfo:
    async def test_no_subscription_returns_nones(self, client, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, subscription_tier="free")
        resp = await client.get("/api/payments/subscription", headers=_headers_for(e))
        body = resp.json()
        assert body["tier"] == "free"
        assert body["status"] is None
        assert body["stripe_subscription_id"] is None

    async def test_with_active_subscription(self, client, db_session, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, subscription_tier="premium")
        db_session.add(Subscription(
            escort_id=e.id, tier="premium", status="active",
            stripe_subscription_id="sub_active",
            current_period_end=datetime.utcnow() + timedelta(days=20),
        ))
        await db_session.flush()
        body = (await client.get("/api/payments/subscription", headers=_headers_for(e))).json()
        assert body["status"] == "active"
        assert body["stripe_subscription_id"] == "sub_active"

    async def test_invoices_empty_when_no_customer_id(self, client, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_customer_id=None)
        body = (await client.get("/api/payments/invoices", headers=_headers_for(e))).json()
        assert body == {"invoices": []}

    async def test_invoices_calls_stripe_with_customer_id(self, client, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_with_inv")
        await client.get("/api/payments/invoices", headers=_headers_for(e))
        mock_stripe.client.invoices.list.assert_called_once()
        call = mock_stripe.client.invoices.list.call_args
        params = call.kwargs.get("params") or call.args[0]
        assert params["customer"] == "cus_with_inv"


# ---------------------------------------------------------------------------
# POST /payments/cancel & cancel-blue-tick
# ---------------------------------------------------------------------------
class TestCancel:
    async def test_cancel_marks_cancelling(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, subscription_tier="premium", stripe_subscription_id="sub_c")
        db_session.add(Subscription(
            escort_id=e.id, tier="premium", status="active", stripe_subscription_id="sub_c",
        ))
        await db_session.flush()
        resp = await client.post("/api/payments/cancel", headers=_headers_for(e))
        assert resp.status_code == 200
        # Stripe called with cancel_at_period_end=True
        mock_stripe.client.subscriptions.update.assert_called()
        call = mock_stripe.client.subscriptions.update.call_args
        params = call.kwargs.get("params") or call.args[1] if len(call.args) > 1 else call.kwargs.get("params")
        assert params["cancel_at_period_end"] is True
        # DB record flipped
        result = await db_session.execute(select(Subscription).where(Subscription.stripe_subscription_id == "sub_c"))
        sub = result.scalar_one()
        assert sub.status == "cancelling"

    async def test_cancel_no_subscription_400(self, client, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_subscription_id=None)
        resp = await client.post("/api/payments/cancel", headers=_headers_for(e))
        assert resp.status_code == 400

    async def test_cancel_already_cancelling_400(self, client, db_session, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_subscription_id="sub_x")
        db_session.add(Subscription(escort_id=e.id, tier="essential", status="cancelling",
                                    stripe_subscription_id="sub_x"))
        await db_session.flush()
        resp = await client.post("/api/payments/cancel", headers=_headers_for(e))
        assert resp.status_code == 400
        assert "already scheduled" in resp.json()["detail"].lower()

    async def test_cancel_blue_tick(self, client, db_session, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, blue_tick_stripe_subscription_id="sub_bt")
        db_session.add(Subscription(escort_id=e.id, tier="blue_tick", status="active",
                                    stripe_subscription_id="sub_bt"))
        await db_session.flush()
        resp = await client.post("/api/payments/cancel-blue-tick", headers=_headers_for(e))
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Webhook handler
# ---------------------------------------------------------------------------
class TestStripeWebhook:
    async def test_invalid_signature_400(self, client, mock_stripe):
        import stripe
        mock_stripe.construct_event.side_effect = stripe.error.SignatureVerificationError("bad sig", "raw")
        resp = await client.post(
            "/api/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "bogus"},
        )
        assert resp.status_code == 400
        assert "signature" in resp.json()["detail"].lower()

    async def test_checkout_completed_creates_subscription_record(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_match", subscription_tier="free")
        mock_stripe.construct_event.return_value = {
            "id": "evt_chk_1",
            "type": "checkout.session.completed",
            "data": {"object": {
                "metadata": {"escort_id": str(e.id), "tier": "premium", "billing": "monthly"},
                "subscription": "sub_new",
                "customer": "cus_match",
            }},
        }
        resp = await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        assert resp.status_code == 200

        await db_session.refresh(e)
        assert e.subscription_tier == "premium"
        assert e.stripe_subscription_id == "sub_new"

        # WebhookEvent row recorded for idempotency
        wh = await db_session.execute(select(WebhookEvent).where(WebhookEvent.id == "evt_chk_1"))
        assert wh.scalar_one() is not None

        # Subscription record present and active
        sub_row = await db_session.execute(select(Subscription).where(Subscription.stripe_subscription_id == "sub_new"))
        assert sub_row.scalar_one().status == "active"

    @pytest.mark.security
    async def test_checkout_completed_rejects_customer_id_mismatch(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        """Security: stripe_customer_id mismatch must NOT promote the escort.

        This is the regression guard for the forged-metadata attack: an attacker
        controls the metadata.escort_id but cannot control session.customer.
        """
        e = await escort_factory(
            verification_level=1, stripe_customer_id="cus_REAL", subscription_tier="free",
        )
        mock_stripe.construct_event.return_value = {
            "id": "evt_chk_attack",
            "type": "checkout.session.completed",
            "data": {"object": {
                "metadata": {"escort_id": str(e.id), "tier": "elite", "billing": "monthly"},
                "subscription": "sub_attacker",
                "customer": "cus_ATTACKER",
            }},
        }
        resp = await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        assert resp.status_code == 200  # webhook still returns 200 to Stripe

        await db_session.refresh(e)
        assert e.subscription_tier == "free"  # NOT promoted
        assert e.stripe_subscription_id is None

    async def test_webhook_idempotent_on_duplicate_event(self, client, db_session, escort_factory, mock_stripe):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_match")
        event = {
            "id": "evt_dupe_1",
            "type": "checkout.session.completed",
            "data": {"object": {
                "metadata": {"escort_id": str(e.id), "tier": "essential", "billing": "monthly"},
                "subscription": "sub_dupe",
                "customer": "cus_match",
            }},
        }
        mock_stripe.construct_event.return_value = event

        r1 = await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        r2 = await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r2.json().get("duplicate") is True

    async def test_subscription_updated_changes_status(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_match", stripe_subscription_id="sub_u")
        db_session.add(Subscription(
            escort_id=e.id, tier="premium", status="active", stripe_subscription_id="sub_u",
            current_period_start=datetime.utcnow() - timedelta(days=5),
            current_period_end=datetime.utcnow() + timedelta(days=25),
        ))
        await db_session.flush()
        period_end_ts = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        mock_stripe.construct_event.return_value = {
            "id": "evt_upd_1", "type": "customer.subscription.updated",
            "data": {"object": {
                "id": "sub_u", "status": "active",
                "cancel_at_period_end": True,
                "current_period_start": int(datetime.utcnow().timestamp()),
                "current_period_end": period_end_ts,
                "customer": "cus_match",
            }},
        }
        await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        result = await db_session.execute(select(Subscription).where(Subscription.stripe_subscription_id == "sub_u"))
        sub = result.scalar_one()
        assert sub.status == "cancelling"

    @pytest.mark.security
    async def test_subscription_updated_rejects_customer_mismatch(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, stripe_customer_id="cus_REAL", stripe_subscription_id="sub_m")
        db_session.add(Subscription(escort_id=e.id, tier="premium", status="active", stripe_subscription_id="sub_m",
                                    current_period_start=datetime.utcnow()))
        await db_session.flush()
        before_expiry = e.subscription_expires_at
        mock_stripe.construct_event.return_value = {
            "id": "evt_upd_attack", "type": "customer.subscription.updated",
            "data": {"object": {
                "id": "sub_m", "status": "active", "cancel_at_period_end": False,
                "current_period_start": int(datetime.utcnow().timestamp()),
                "current_period_end": int((datetime.utcnow() + timedelta(days=365 * 10)).timestamp()),
                "customer": "cus_ATTACKER",
            }},
        }
        await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        await db_session.refresh(e)
        # subscription_expires_at must NOT have been moved to 10 years out
        assert e.subscription_expires_at == before_expiry

    async def test_subscription_deleted_resets_escort_tier(
        self, client, db_session, escort_factory, mock_stripe,
    ):
        e = await escort_factory(verification_level=1, subscription_tier="premium",
                                 stripe_customer_id="cus_match", stripe_subscription_id="sub_d")
        db_session.add(Subscription(escort_id=e.id, tier="premium", status="active", stripe_subscription_id="sub_d"))
        await db_session.flush()
        mock_stripe.construct_event.return_value = {
            "id": "evt_del_1", "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_d", "customer": "cus_match"}},
        }
        await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        await db_session.refresh(e)
        assert e.subscription_tier == "free"
        assert e.stripe_subscription_id is None

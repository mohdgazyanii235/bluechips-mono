"""End-to-end happy-path: register -> verify email -> login -> checkout -> webhook.

These integration tests intentionally cross multiple routers to catch
contract drift between request/response shapes, JWT handling, and the webhook
data model. External services (Stripe) are still mocked.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.escort import Escort
from app.models.subscription import Subscription


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestSignupVerifyLogin:
    async def test_full_signup_to_login(self, client, db_session):
        # 1. Register
        reg = await client.post("/api/auth/register", json={
            "email": "flow@test.local", "password": "Password123!", "stage_name": "Flowy",
        })
        assert reg.status_code == 201

        # 2. Read token straight from DB (in production it goes via email)
        result = await db_session.execute(select(Escort).where(Escort.email == "flow@test.local"))
        escort = result.scalar_one()
        token = escort.email_verification_token
        assert token

        # 3. Verify email
        ver = await client.post(f"/api/auth/verify-email?token={token}")
        assert ver.status_code == 200

        # 4. Login with the same credentials
        login = await client.post("/api/auth/login", json={
            "email": "flow@test.local", "password": "Password123!",
        })
        assert login.status_code == 200
        token = login.json()["access_token"]

        # 5. Authenticated dashboard call
        me = await client.get("/api/escorts/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "flow@test.local"


class TestCheckoutToWebhookActivation:
    async def test_checkout_then_webhook_promotes_tier(
        self, client, db_session, escort_factory, platform_config, mock_stripe,
    ):
        """Simulate the full purchase pipeline:
        1. Escort hits /payments/checkout — Stripe customer is created.
        2. Stripe fires checkout.session.completed via webhook.
        3. Escort.subscription_tier is now 'essential' and Subscription row exists.
        """
        from app.utils.security import create_access_token
        e = await escort_factory(verification_level=1, subscription_tier="free")
        headers = {"Authorization": f"Bearer {create_access_token(str(e.id))}"}

        # Step 1 — checkout creates the stripe customer
        chk = await client.post("/api/payments/checkout", headers=headers,
                                json={"tier": "essential", "billing": "monthly"})
        assert chk.status_code == 200
        await db_session.refresh(e)
        assert e.stripe_customer_id == "cus_test_new"

        # Step 2 — Stripe POSTs the webhook
        mock_stripe.construct_event.return_value = {
            "id": "evt_int_1", "type": "checkout.session.completed",
            "data": {"object": {
                "metadata": {"escort_id": str(e.id), "tier": "essential", "billing": "monthly"},
                "subscription": "sub_int_1",
                "customer": "cus_test_new",
            }},
        }
        wh = await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})
        assert wh.status_code == 200

        # Step 3 — DB reflects the active subscription
        await db_session.refresh(e)
        assert e.subscription_tier == "essential"
        assert e.stripe_subscription_id == "sub_int_1"
        sub = (await db_session.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == "sub_int_1")
        )).scalar_one()
        assert sub.status == "active"


class TestBlueTickFullFlow:
    async def test_blue_tick_purchase_creates_verification_row(
        self, client, db_session, escort_factory, platform_config, mock_stripe,
    ):
        from app.utils.security import create_access_token
        from app.models.verification import Verification

        e = await escort_factory(
            verification_level=2, subscription_tier="essential", stripe_customer_id="cus_x",
        )
        headers = {"Authorization": f"Bearer {create_access_token(str(e.id))}"}

        chk = await client.post("/api/payments/blue-tick-checkout", headers=headers)
        assert chk.status_code == 200

        # Stripe completes checkout
        mock_stripe.construct_event.return_value = {
            "id": "evt_bt_1", "type": "checkout.session.completed",
            "data": {"object": {
                "metadata": {"escort_id": str(e.id), "tier": "blue_tick"},
                "subscription": "sub_bt_1",
                "customer": "cus_x",
            }},
        }
        await client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "ok"})

        await db_session.refresh(e)
        assert e.blue_tick_stripe_subscription_id == "sub_bt_1"

        # Verification(level=3) row created in pending state
        v_result = await db_session.execute(
            select(Verification).where(Verification.escort_id == e.id, Verification.level == 3)
        )
        v = v_result.scalar_one()
        assert v.status == "pending"

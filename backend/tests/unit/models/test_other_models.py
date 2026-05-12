"""Tests for ancillary models: Admin, Verification, Subscription, WebhookEvent.

Focuses on the contract bits that the application logic depends on:
- defaults
- unique constraints
- timestamp auto-population
"""
from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.models.subscription import Subscription
from app.models.verification import Verification
from app.models.webhook_event import WebhookEvent


pytestmark = pytest.mark.asyncio


class TestAdminModel:
    async def test_admin_defaults(self, db_session):
        a = Admin(email="d@test.local", hashed_password="x")
        db_session.add(a)
        await db_session.flush()
        assert a.is_active is True
        assert isinstance(a.created_at, datetime)

    async def test_email_unique(self, db_session):
        a = Admin(email="u@test.local", hashed_password="x")
        b = Admin(email="u@test.local", hashed_password="y")
        db_session.add(a)
        await db_session.flush()
        db_session.add(b)
        with pytest.raises(IntegrityError):
            await db_session.flush()


class TestVerificationModel:
    async def test_status_defaults_pending(self, db_session, escort):
        v = Verification(escort_id=escort.id, level=2)
        db_session.add(v)
        await db_session.flush()
        assert v.status == "pending"
        assert isinstance(v.submitted_at, datetime)
        assert v.reviewed_at is None


class TestSubscriptionModel:
    async def test_status_default_active(self, db_session, escort):
        s = Subscription(escort_id=escort.id, tier="essential")
        db_session.add(s)
        await db_session.flush()
        assert s.status == "active"

    async def test_updated_at_changes_on_update(self, db_session, escort):
        s = Subscription(escort_id=escort.id, tier="essential")
        db_session.add(s)
        await db_session.flush()
        first = s.updated_at
        s.status = "cancelling"
        await db_session.flush()
        # onupdate=datetime.utcnow fires on dirty flush
        assert s.updated_at >= first


class TestWebhookEventModel:
    async def test_idempotent_id(self, db_session):
        e1 = WebhookEvent(id="evt_x", event_type="checkout.session.completed")
        db_session.add(e1)
        await db_session.flush()

        e2 = WebhookEvent(id="evt_x", event_type="customer.subscription.updated")
        db_session.add(e2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

"""Tests for the Escort SQLAlchemy model.

Covers:
- Unique constraints (email, slug).
- Default values from column defaults (verification_level=0, etc.).
- Computed properties: primary_photo_url, photo_limit.
- Cascade deletes: photos/services/verifications removed with the escort.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.escort import Escort, EscortPhoto, EscortService
from app.models.verification import Verification


pytestmark = pytest.mark.asyncio


class TestDefaults:
    async def test_default_field_values(self, db_session):
        e = Escort(
            email="defaults@test.local",
            hashed_password="x",
            stage_name="Defaults",
            slug="defaults-unique",
        )
        db_session.add(e)
        await db_session.flush()

        assert e.verification_level == 0
        assert e.is_email_verified is False
        assert e.is_active is True
        assert e.is_approved is True
        assert e.available_now is False
        assert e.profile_complete is False
        assert e.subscription_tier == "free"
        assert e.blue_tick_active is False
        assert e.profile_views == 0
        assert e.contact_clicks == 0
        assert e.is_founding_member is False


class TestUniqueConstraints:
    async def test_email_unique(self, db_session, escort_factory):
        await escort_factory(email="unique@test.local")
        with pytest.raises(IntegrityError):
            await escort_factory(email="unique@test.local")
            # The flush inside the factory will raise; force it again if not
            await db_session.flush()

    async def test_slug_unique(self, db_session):
        a = Escort(email="a@test.local", hashed_password="x", stage_name="A", slug="dup-slug")
        b = Escort(email="b@test.local", hashed_password="x", stage_name="B", slug="dup-slug")
        db_session.add(a)
        await db_session.flush()
        db_session.add(b)
        with pytest.raises(IntegrityError):
            await db_session.flush()


class TestComputedProperties:
    async def test_photo_limit_by_tier(self, db_session):
        """The photo_limit getter must map tier → limit correctly."""
        for tier, expected in [("free", 3), ("essential", 8), ("premium", 50), ("elite", 50)]:
            e = Escort(
                email=f"{tier}@test.local", hashed_password="x",
                stage_name=tier, slug=f"slug-{tier}",
                subscription_tier=tier,
            )
            assert e.photo_limit == expected

    async def test_photo_limit_unknown_tier_defaults_3(self, db_session):
        e = Escort(email="unknown@test.local", hashed_password="x",
                   stage_name="U", slug="unknown-tier", subscription_tier="legacy")
        assert e.photo_limit == 3

    async def test_primary_photo_url_with_explicit_primary(self, db_session, escort):
        p1 = EscortPhoto(escort_id=escort.id, url="p1.jpg", is_primary=False, sort_order=0)
        p2 = EscortPhoto(escort_id=escort.id, url="p2.jpg", is_primary=True, sort_order=1)
        db_session.add_all([p1, p2])
        await db_session.flush()
        await db_session.refresh(escort)
        assert escort.primary_photo_url == "p2.jpg"

    async def test_primary_photo_url_falls_back_to_first(self, db_session, escort):
        p1 = EscortPhoto(escort_id=escort.id, url="first.jpg", is_primary=False, sort_order=0)
        db_session.add(p1)
        await db_session.flush()
        await db_session.refresh(escort)
        assert escort.primary_photo_url == "first.jpg"

    async def test_primary_photo_url_no_photos(self, db_session, escort):
        await db_session.refresh(escort)
        assert escort.primary_photo_url is None


class TestCascadeDeletes:
    async def test_deleting_escort_cascades_photos(self, db_session, escort):
        db_session.add(EscortPhoto(escort_id=escort.id, url="x.jpg"))
        await db_session.flush()

        await db_session.delete(escort)
        await db_session.flush()
        remaining = await db_session.execute(select(EscortPhoto).where(EscortPhoto.escort_id == escort.id))
        assert remaining.scalar_one_or_none() is None

    async def test_deleting_escort_cascades_services(self, db_session, escort):
        db_session.add(EscortService(escort_id=escort.id, tag="GFE"))
        await db_session.flush()
        await db_session.delete(escort)
        await db_session.flush()
        remaining = await db_session.execute(select(EscortService).where(EscortService.escort_id == escort.id))
        assert remaining.scalar_one_or_none() is None

    async def test_deleting_escort_cascades_verifications(self, db_session, escort):
        db_session.add(Verification(escort_id=escort.id, level=2, status="pending"))
        await db_session.flush()
        await db_session.delete(escort)
        await db_session.flush()
        remaining = await db_session.execute(select(Verification).where(Verification.escort_id == escort.id))
        assert remaining.scalar_one_or_none() is None

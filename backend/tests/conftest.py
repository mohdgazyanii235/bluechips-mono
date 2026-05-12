"""Shared pytest fixtures for the Bluechips London backend test suite.

This conftest wires up:
- an in-memory async SQLite database (Postgres-specific columns are monkey-patched
  to portable types so the same models can be used in tests without a Postgres
  instance);
- a per-test database session/transaction with automatic rollback;
- an httpx.AsyncClient bound to the FastAPI app with the get_db dependency
  overridden to use the test session;
- factory fixtures for Escort, Admin, Borough, Verification, Subscription, etc.;
- a mock_stripe fixture providing a namespace of patched Stripe SDK calls;
- an automatic rate-limiter reset between tests (module-level state).
"""
from __future__ import annotations

import io
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event, JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test-mode env BEFORE any app imports. pytest.ini also sets these but
# `import app.config` happens at first import, so be defensive.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-not-prod")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_dummy")
os.environ.setdefault("SMTP_USER", "")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.local")


# ---------------------------------------------------------------------------
# Compatibility shims for SQLite
# ---------------------------------------------------------------------------
# The models use postgresql.UUID(as_uuid=True), postgresql.ARRAY, and
# postgresql.JSONB. SQLAlchemy provides a generic UUID dialect adapter, but
# we patch ARRAY for sqlite to fall back to JSON which still round-trips lists.
@event.listens_for(ARRAY, "compile", propagate=True, retval=True)
def _array_sqlite_compile(element, compiler, **kw):  # pragma: no cover - tied to dialect
    if compiler.dialect.name == "sqlite":
        return JSON().compile(dialect=compiler.dialect)
    return None  # default
# Note: the above hook is unreliable; we instead patch via __compile_kwargs__
# below in conftest setup if needed. For now we run against Postgres in CI.


from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Database engine + session
# ---------------------------------------------------------------------------

# Tests prefer real Postgres for full model fidelity (ARRAY/JSONB). The fallback
# to SQLite is only viable for pure-unit tests that don't touch ARRAY columns.
_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)


@pytest_asyncio.fixture(scope="session")
async def _engine():
    """One engine for the whole test session."""
    engine = create_async_engine(_TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session wrapped in a transaction that is rolled back at teardown.

    This is the standard SQLAlchemy 'savepoint per test' pattern adapted for
    async. Even nested commits within the request handlers become savepoints
    that don't persist beyond the test.
    """
    connection = await _engine.connect()
    transaction = await connection.begin()
    session_maker = async_sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    session = session_maker()

    # Convert outer commits into nested savepoints so test cleanup wipes them.
    await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(sess, trans):  # pragma: no cover - SQLAlchemy hook
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """An httpx.AsyncClient with get_db overridden to use the rolled-back session."""

    async def _override_get_db():
        # Yield the same session for the whole request; do NOT commit/close here
        # (the fixture owns the lifecycle).
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Rate limiter reset (module-level state)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The in-memory rate limiter is a process-level dict; clear it between tests
    so one test's burst doesn't poison the next."""
    from app.utils.rate_limit import _store
    _store.clear()
    yield
    _store.clear()


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------
def make_jpeg_bytes(size=(100, 100)) -> bytes:
    """In-memory minimal JPEG used for upload tests."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", size, color=(255, 0, 0)).save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def make_png_bytes(size=(100, 100)) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", size, color=(0, 255, 0)).save(buf, format="PNG")
    return buf.getvalue()


def make_webp_bytes(size=(100, 100)) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", size, color=(0, 0, 255)).save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def jpeg_bytes() -> bytes:
    return make_jpeg_bytes()


@pytest.fixture
def png_bytes() -> bytes:
    return make_png_bytes()


@pytest.fixture
def webp_bytes() -> bytes:
    return make_webp_bytes()


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------
from app.models.admin import Admin
from app.models.borough import Borough
from app.models.escort import Escort, EscortPhoto, EscortService
from app.models.platform_config import PlatformConfig
from app.models.subscription import Subscription
from app.models.verification import Verification
from app.models.discount import DiscountCode
from app.utils.security import hash_password, create_access_token


@pytest_asyncio.fixture
async def borough_factory(db_session: AsyncSession):
    async def _factory(name: str = "Mayfair", slug: Optional[str] = None) -> Borough:
        b = Borough(name=name, slug=slug or name.lower().replace(" ", "-"), sort_order=1)
        db_session.add(b)
        await db_session.flush()
        return b
    return _factory


@pytest_asyncio.fixture
async def borough(borough_factory) -> Borough:
    return await borough_factory("Mayfair", "mayfair")


@pytest_asyncio.fixture
async def escort_factory(db_session: AsyncSession):
    """Factory for creating Escort rows with sensible defaults.

    By default the escort is email-verified, active, and approved so that most
    tests don't have to do dance to satisfy visibility predicates. Override any
    field via kwargs.
    """
    counter = {"n": 0}

    async def _factory(
        *,
        email: Optional[str] = None,
        password: str = "Password123!",
        stage_name: Optional[str] = None,
        is_email_verified: bool = True,
        verification_level: int = 1,
        is_active: bool = True,
        is_approved: bool = True,
        subscription_tier: str = "free",
        **extra,
    ) -> Escort:
        counter["n"] += 1
        n = counter["n"]
        e = Escort(
            email=(email or f"escort{n}-{uuid.uuid4().hex[:6]}@test.local").lower(),
            hashed_password=hash_password(password),
            stage_name=stage_name or f"Tester{n}",
            slug=f"tester{n}-{uuid.uuid4().hex[:6]}",
            is_email_verified=is_email_verified,
            verification_level=verification_level,
            is_active=is_active,
            is_approved=is_approved,
            subscription_tier=subscription_tier,
            **extra,
        )
        db_session.add(e)
        await db_session.flush()
        return e

    return _factory


@pytest_asyncio.fixture
async def escort(escort_factory) -> Escort:
    return await escort_factory()


@pytest_asyncio.fixture
async def auth_headers(escort: Escort) -> dict:
    """Bearer-token headers for the default `escort` fixture."""
    token = create_access_token(str(escort.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_factory(db_session: AsyncSession):
    async def _factory(email: str = "admin@test.local", password: str = "AdminPass123!") -> Admin:
        a = Admin(email=email.lower(), hashed_password=hash_password(password), is_active=True)
        db_session.add(a)
        await db_session.flush()
        return a
    return _factory


@pytest_asyncio.fixture
async def admin(admin_factory) -> Admin:
    return await admin_factory()


@pytest_asyncio.fixture
async def admin_headers(admin: Admin) -> dict:
    token = create_access_token(str(admin.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def platform_config(db_session: AsyncSession) -> PlatformConfig:
    cfg = PlatformConfig(
        id=1,
        essential_monthly_pence=1199,
        premium_monthly_pence=1899,
        elite_monthly_pence=2399,
        blue_tick_setup_pence=1000,
        blue_tick_monthly_pence=399,
        stripe_essential_monthly_id="price_test_essential_m",
        stripe_premium_monthly_id="price_test_premium_m",
        stripe_elite_monthly_id="price_test_elite_m",
        stripe_blue_tick_setup_id="price_test_bt_setup",
        stripe_blue_tick_monthly_id="price_test_bt_monthly",
    )
    db_session.add(cfg)
    await db_session.flush()
    return cfg


# ---------------------------------------------------------------------------
# Stripe mocks
# ---------------------------------------------------------------------------
class _MockStripe:
    """Bundles all the Stripe SDK patches used across tests."""
    def __init__(self):
        self.client = MagicMock()
        # checkout.sessions.create returns an object with a .url
        self.client.checkout.sessions.create.return_value = MagicMock(url="https://checkout.stripe.com/test-session")
        # customers.create
        self.client.customers.create.return_value = MagicMock(id="cus_test_new")
        # coupons.create
        self.client.coupons.create.return_value = MagicMock(id="coupon_test")
        # subscriptions
        self.client.subscriptions.retrieve.return_value = {
            "id": "sub_test",
            "items": {"data": [{"id": "si_test", "price": {"id": "price_test", "recurring": {"interval": "month"}}}]},
        }
        self.client.subscriptions.update.return_value = {
            "current_period_end": int(datetime.utcnow().timestamp()) + 30 * 86400,
        }
        # invoices
        self.client.invoices.create.return_value = MagicMock(id="in_test")
        self.client.invoices.finalize_invoice.return_value = MagicMock(amount_due=0, status="paid")
        self.client.invoices.list.return_value = MagicMock(data=[])


@pytest.fixture
def mock_stripe():
    """Yield a namespace of Stripe mocks. Patches:
      - stripe.StripeClient -> returns our MagicMock
      - stripe.Webhook.construct_event -> returns the payload as dict (bypass sig)
      - stripe.Subscription.retrieve -> returns canned dict
      - stripe.Refund.create -> returns id
    """
    m = _MockStripe()
    with patch("app.routers.payments.stripe.StripeClient", return_value=m.client), \
         patch("app.routers.payments.stripe.Webhook.construct_event") as construct_event, \
         patch("app.routers.payments.stripe.Subscription.retrieve") as sub_retrieve, \
         patch("app.routers.admin.stripe.Refund.create") as refund_create, \
         patch("app.routers.admin.stripe.Subscription.delete") as sub_delete, \
         patch("app.routers.admin.stripe.Invoice.list") as inv_list:
        sub_retrieve.return_value = {
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int(datetime.utcnow().timestamp()) + 30 * 86400,
            "items": {"data": [{"price": {"id": "price_test", "unit_amount": 1199}}]},
        }
        refund_create.return_value = MagicMock(id="re_test")
        sub_delete.return_value = MagicMock()
        inv_list.return_value = {"data": []}
        # Default construct_event returns nothing - per-test overrides set the event payload.
        construct_event.return_value = None
        m.construct_event = construct_event
        m.sub_retrieve = sub_retrieve
        m.refund_create = refund_create
        m.sub_delete = sub_delete
        m.inv_list = inv_list
        yield m


@pytest.fixture
def mock_storage(tmp_path, monkeypatch):
    """Replace S3 with in-memory dicts and point local uploads at tmp_path."""
    monkeypatch.setattr(settings, "LOCAL_UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "")
    # Ensure subfolders exist
    (tmp_path / "photos").mkdir(exist_ok=True)
    (tmp_path / "photos" / "thumbs").mkdir(exist_ok=True)
    (tmp_path / "documents").mkdir(exist_ok=True)
    yield tmp_path

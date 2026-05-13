"""
Unit tests for the Verotel FlexPay provider.

These tests use a mocked Settings object so they don't depend on real
Verotel credentials. They verify:
  - Signature is computed deterministically and is reproducible.
  - Webhook verification rejects unsigned / tampered payloads.
  - Webhook verification accepts valid payloads and produces canonical events.
  - Checkout URL params include all required FlexPay v4 fields.
  - Tier upgrades fail-cleanly because Verotel can't change price in-place.
"""
import json
import hashlib
import pytest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

from app.services.payment_provider.errors import (
    InvalidWebhookSignatureError, ProviderApiError,
)
from app.services.payment_provider.base import (
    CheckoutRequest, WebhookEventType,
)


# ─── Test fixtures ─────────────────────────────────────────────────────────

TEST_SHOP_ID = "shop123"
TEST_SIG_KEY = "sigkey-xyz"


@pytest.fixture
def provider(monkeypatch):
    """Verotel provider instance configured with deterministic test creds."""
    from app.config import settings
    monkeypatch.setattr(settings, "VEROTEL_SHOP_ID", TEST_SHOP_ID)
    monkeypatch.setattr(settings, "VEROTEL_SIGNATURE_KEY", TEST_SIG_KEY)
    monkeypatch.setattr(settings, "VEROTEL_API_USERNAME", "apiuser")
    monkeypatch.setattr(settings, "VEROTEL_API_PASSWORD", "apipass")
    monkeypatch.setattr(settings, "VEROTEL_TEST_MODE", True)
    monkeypatch.setattr(settings, "PAYMENT_PROVIDER", "verotel")
    from app.services.payment_provider.verotel import VerotelFlexPayProvider
    return VerotelFlexPayProvider()


def _expected_signature(params: dict) -> str:
    items = sorted((k, v) for k, v in params.items() if k != "signature")
    canonical = TEST_SIG_KEY + ":" + ":".join(f"{k}={v}" for k, v in items)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().lower()


# ─── Configuration ─────────────────────────────────────────────────────────

def test_provider_name(provider):
    assert provider.name == "verotel"


def test_supports_in_place_upgrade_returns_false(provider):
    """Critical contract — the router branches on this."""
    assert provider.supports_in_place_upgrade() is False


def test_init_raises_when_shop_id_missing(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "VEROTEL_SHOP_ID", "")
    monkeypatch.setattr(settings, "VEROTEL_SIGNATURE_KEY", "anything")
    from app.services.payment_provider.verotel import VerotelFlexPayProvider
    from app.services.payment_provider.errors import ProviderNotConfiguredError
    with pytest.raises(ProviderNotConfiguredError):
        VerotelFlexPayProvider()


def test_init_raises_when_signature_key_missing(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "VEROTEL_SHOP_ID", "shop123")
    monkeypatch.setattr(settings, "VEROTEL_SIGNATURE_KEY", "")
    from app.services.payment_provider.verotel import VerotelFlexPayProvider
    from app.services.payment_provider.errors import ProviderNotConfiguredError
    with pytest.raises(ProviderNotConfiguredError):
        VerotelFlexPayProvider()


# ─── Signature ─────────────────────────────────────────────────────────────

def test_sign_deterministic(provider):
    params = {"a": "1", "b": "2", "c": "3"}
    s1 = provider._sign(params)
    s2 = provider._sign(params)
    assert s1 == s2
    assert s1 == _expected_signature(params)


def test_sign_ignores_signature_field(provider):
    params = {"a": "1", "b": "2"}
    with_sig = {**params, "signature": "bogus"}
    assert provider._sign(params) == provider._sign(with_sig)


def test_sign_is_order_independent(provider):
    """Param dict order must not affect the signature (sorted internally)."""
    a = {"x": "1", "y": "2", "z": "3"}
    b = {"z": "3", "x": "1", "y": "2"}
    assert provider._sign(a) == provider._sign(b)


# ─── Checkout URL ──────────────────────────────────────────────────────────

def _checkout_request(**overrides) -> CheckoutRequest:
    base = dict(
        amount_pence=1899,
        billing="monthly",
        tier="premium",
        customer_email="test@example.com",
        customer_name="Sophia",
        success_url="https://bluechips.live/dashboard/verify?payment=success",
        cancel_url="https://bluechips.live/dashboard/subscription?payment=cancelled",
        metadata={"escort_id": "abc-123", "tier": "premium", "billing": "monthly"},
    )
    base.update(overrides)
    return CheckoutRequest(**base)


def test_checkout_url_has_required_params(provider):
    result = provider.create_subscription_checkout(_checkout_request())
    parsed = urlparse(result.url)
    qs = parse_qs(parsed.query)
    assert qs["version"] == ["4"]
    assert qs["type"] == ["subscription"]
    assert qs["shopID"] == [TEST_SHOP_ID]
    assert qs["priceAmount"] == ["18.99"]
    assert qs["priceCurrency"] == ["GBP"]
    assert qs["period"] == ["P1M"]
    assert qs["email"] == ["test@example.com"]
    assert "signature" in qs


def test_checkout_url_signature_is_valid(provider):
    result = provider.create_subscription_checkout(_checkout_request())
    parsed = urlparse(result.url)
    qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    sig = qs.pop("signature")
    assert sig == _expected_signature(qs)


def test_checkout_url_annual_period(provider):
    result = provider.create_subscription_checkout(_checkout_request(billing="annual"))
    qs = parse_qs(urlparse(result.url).query)
    assert qs["period"] == ["P1Y"]


def test_checkout_metadata_round_trips_via_custom1(provider):
    """The escort_id we put in must come back out from custom1 unchanged."""
    result = provider.create_subscription_checkout(_checkout_request(
        metadata={"escort_id": "abc-123", "tier": "premium", "billing": "monthly"}
    ))
    qs = parse_qs(urlparse(result.url).query)
    custom1 = json.loads(qs["custom1"][0])
    assert custom1["escort_id"] == "abc-123"
    assert custom1["tier"] == "premium"
    assert custom1["billing"] == "monthly"


def test_checkout_discount_reduces_first_amount(provider):
    result = provider.create_subscription_checkout(_checkout_request(
        discount_percent=50, discount_label="FM-ABCDE",
    ))
    qs = parse_qs(urlparse(result.url).query)
    # 50% off £18.99 → £9.50 (rounded)
    assert qs["priceAmount"] == ["9.49"] or qs["priceAmount"] == ["9.50"]
    # Recurring (post-discount) price is the full amount
    assert qs["subscriptionPriceAmount"] == ["18.99"]


def test_checkout_blue_tick_includes_setup_fee(provider):
    result = provider.create_subscription_checkout(_checkout_request(
        tier="blue_tick", amount_pence=399, setup_fee_pence=1000,
    ))
    qs = parse_qs(urlparse(result.url).query)
    # First charge = setup (£10) + monthly (£3.99) = £13.99
    assert qs["priceAmount"] == ["13.99"]
    # Subsequent rebills are just the monthly
    assert qs["subscriptionPriceAmount"] == ["3.99"]


# ─── Webhook verification ──────────────────────────────────────────────────

def _valid_postback_body(provider, **fields):
    """Build a postback body with a valid signature."""
    params = {
        "event": "initial",
        "saleID": "verotel-sub-12345",
        "referenceID": "tx-99999",
        "email": "test@example.com",
        "amount": "18.99",
        "custom1": json.dumps({"escort_id": "abc-123", "tier": "premium", "billing": "monthly"}),
        **fields,
    }
    params["signature"] = provider._sign(params)
    from urllib.parse import urlencode
    return urlencode(params).encode("utf-8"), params


def test_webhook_accepts_valid_payload(provider):
    body, params = _valid_postback_body(provider)
    event = provider.verify_and_parse_webhook(raw_body=body, headers={}, query_params={})
    assert event.type == WebhookEventType.SUBSCRIPTION_CREATED
    assert event.subscription_id == "verotel-sub-12345"
    assert event.transaction_id == "tx-99999"
    assert event.amount_pence == 1899
    assert event.metadata["escort_id"] == "abc-123"


def test_webhook_rejects_missing_signature(provider):
    body, params = _valid_postback_body(provider)
    # Strip signature
    from urllib.parse import urlencode
    no_sig = {k: v for k, v in params.items() if k != "signature"}
    tampered = urlencode(no_sig).encode()
    with pytest.raises(InvalidWebhookSignatureError):
        provider.verify_and_parse_webhook(raw_body=tampered, headers={}, query_params={})


def test_webhook_rejects_tampered_amount(provider):
    body, params = _valid_postback_body(provider)
    params["amount"] = "0.01"   # tampered AFTER signing — signature now invalid
    from urllib.parse import urlencode
    tampered_body = urlencode(params).encode()
    with pytest.raises(InvalidWebhookSignatureError):
        provider.verify_and_parse_webhook(raw_body=tampered_body, headers={}, query_params={})


def test_webhook_rejects_unknown_event_type(provider):
    body, params = _valid_postback_body(provider, event="something_unknown")
    with pytest.raises(ProviderApiError):
        provider.verify_and_parse_webhook(raw_body=body, headers={}, query_params={})


def test_webhook_accepts_via_query_params(provider):
    """Verotel can send postbacks as GET requests with query params."""
    body, params = _valid_postback_body(provider)
    event = provider.verify_and_parse_webhook(raw_body=b"", headers={}, query_params=params)
    assert event.type == WebhookEventType.SUBSCRIPTION_CREATED


@pytest.mark.parametrize("verotel_event,canonical", [
    ("initial",     WebhookEventType.SUBSCRIPTION_CREATED),
    ("rebill",      WebhookEventType.SUBSCRIPTION_RENEWED),
    ("cancel",      WebhookEventType.SUBSCRIPTION_CANCELLED),
    ("uncancel",    WebhookEventType.SUBSCRIPTION_REACTIVATED),
    ("expiry",      WebhookEventType.SUBSCRIPTION_EXPIRED),
    ("credit",      WebhookEventType.REFUND_ISSUED),
    ("chargeback",  WebhookEventType.CHARGEBACK),
])
def test_webhook_event_type_mapping(provider, verotel_event, canonical):
    body, _ = _valid_postback_body(provider, event=verotel_event)
    event = provider.verify_and_parse_webhook(raw_body=body, headers={}, query_params={})
    assert event.type == canonical


def test_webhook_handles_corrupt_custom1_gracefully(provider):
    """If custom1 isn't valid JSON, we should still validate the signature
    and return the event — just with empty metadata."""
    body, _ = _valid_postback_body(provider, custom1="not-valid-json")
    event = provider.verify_and_parse_webhook(raw_body=body, headers={}, query_params={})
    assert event.type == WebhookEventType.SUBSCRIPTION_CREATED
    assert event.metadata == {}


# ─── Reactivation ──────────────────────────────────────────────────────────

def test_reactivate_subscription_raises(provider):
    """Verotel doesn't support programmatic reactivation — must be manual."""
    with pytest.raises(ProviderApiError):
        provider.reactivate_subscription("any-id")

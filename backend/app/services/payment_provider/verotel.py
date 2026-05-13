"""
Verotel FlexPay v4 implementation.

Public reference doc this is built against:
  https://controlcenter.verotel.com/cc/docs/FlexPay_integration.pdf
  (publicly available; the full merchant-only API guide arrives after KYC)

VEROTEL_VERIFY markers below tag spots where exact behaviour should be
sanity-checked against the merchant-only docs once received.
"""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Optional

from app.config import settings
from app.services.payment_provider.base import (
    PaymentProvider, CheckoutRequest, CheckoutResult, WebhookEvent, WebhookEventType, Billing,
)
from app.services.payment_provider.errors import (
    ProviderNotConfiguredError, ProviderApiError, InvalidWebhookSignatureError,
)


# ── Endpoints ────────────────────────────────────────────────────────────────
# VEROTEL_VERIFY: confirm the live hosts after approval. The test/sandbox host
# is typically the same domain with `test-` prefix or a separate one entirely;
# the merchant docs will spell it out.
LIVE_CHECKOUT_BASE = "https://secure.verotel.com/startorder"
TEST_CHECKOUT_BASE = "https://secure.verotel.com/startorder"  # Verotel uses same host, distinguishes via shopID
LIVE_API_BASE = "https://controlcenter.verotel.com/api"
TEST_API_BASE = "https://controlcenter.verotel.com/api"


# Map Verotel postback event names to our canonical types.
# VEROTEL_VERIFY: cross-reference the exact `type` strings against the
# postback section of the merchant doc. These match the public FlexPay v4 spec.
_VEROTEL_EVENT_MAP = {
    "initial":   WebhookEventType.SUBSCRIPTION_CREATED,
    "rebill":    WebhookEventType.SUBSCRIPTION_RENEWED,
    "cancel":    WebhookEventType.SUBSCRIPTION_CANCELLED,
    "uncancel":  WebhookEventType.SUBSCRIPTION_REACTIVATED,
    "expiry":    WebhookEventType.SUBSCRIPTION_EXPIRED,
    "credit":    WebhookEventType.REFUND_ISSUED,
    "chargeback": WebhookEventType.CHARGEBACK,
}


class VerotelFlexPayProvider(PaymentProvider):
    """Concrete Verotel FlexPay implementation."""

    name = "verotel"

    def __init__(self):
        if not settings.VEROTEL_SHOP_ID:
            raise ProviderNotConfiguredError("VEROTEL_SHOP_ID is not set")
        if not settings.VEROTEL_SIGNATURE_KEY:
            raise ProviderNotConfiguredError("VEROTEL_SIGNATURE_KEY is not set")
        self.shop_id = settings.VEROTEL_SHOP_ID
        self.signature_key = settings.VEROTEL_SIGNATURE_KEY
        self.is_test_mode = settings.VEROTEL_TEST_MODE
        self.checkout_base = TEST_CHECKOUT_BASE if self.is_test_mode else LIVE_CHECKOUT_BASE
        self.api_base = TEST_API_BASE if self.is_test_mode else LIVE_API_BASE
        # API credentials for server-to-server calls (cancel, status check).
        # These are separate from the signature key — see Verotel Control Center.
        self.api_user = settings.VEROTEL_API_USERNAME
        self.api_pass = settings.VEROTEL_API_PASSWORD

    # ── Public API ──────────────────────────────────────────────────────────

    def supports_in_place_upgrade(self) -> bool:
        return False

    def create_subscription_checkout(self, req: CheckoutRequest) -> CheckoutResult:
        amount_decimal = f"{req.amount_pence / 100:.2f}"
        period = "P1M" if req.billing == "monthly" else "P1Y"

        # Apply discount to the first charge if requested.
        # FlexPay supports a `priceAmount` (the first-period price) that can
        # differ from `nextChargeOn` amount. For percentage discounts we set
        # priceAmount to the discounted value; subsequent rebills use the
        # advertised price (configured in Control Center per shop).
        # VEROTEL_VERIFY: alternate route is sending a `trialAmount` +
        # `trialPeriod` pair. Confirm which our shop config uses.
        first_amount = req.amount_pence
        if req.discount_percent and 1 <= req.discount_percent <= 100:
            first_amount = max(1, int(req.amount_pence * (100 - req.discount_percent) / 100))
        first_amount_decimal = f"{first_amount / 100:.2f}"

        # Round-trip metadata back to us via the `custom1..3` params (each ≤ 255 chars).
        # We JSON-encode everything into custom1 because the canonical metadata
        # we care about (escort_id, tier, billing, discount_label) easily fits.
        custom1 = json.dumps({
            "escort_id": str(req.metadata.get("escort_id", "")),
            "tier": req.metadata.get("tier", req.tier),
            "billing": req.billing,
            "discount_label": req.discount_label or "",
        }, separators=(",", ":"))
        if len(custom1) > 255:
            # Should never happen — if it does, we lose metadata and the webhook
            # handler will reject the event. Fail loud at checkout instead.
            raise ProviderApiError("metadata too large to round-trip via custom1")

        # FlexPay required params. Names taken from the public v4 spec.
        # VEROTEL_VERIFY: param spellings (camelCase vs lowercase) — public
        # doc shows camelCase; some merchant integrations use lowercase.
        params: dict[str, str] = {
            "version": "4",
            "type": "subscription",
            "shopID": self.shop_id,
            "priceAmount": first_amount_decimal,
            "priceCurrency": "GBP",
            "name": f"Bluechips London — {req.tier.capitalize()}",
            "description": f"{req.tier.capitalize()} ({req.billing.capitalize()}) subscription",
            "period": period,
            "email": req.customer_email,
            "custom1": custom1,
            # success/cancel — Verotel sends the user back to these with a
            # signed query string we can verify on landing.
            "successURL": req.success_url,
            "declineURL": req.cancel_url,
        }

        # If a separate first-period price was used, also tell Verotel what
        # the renewal amount should be (the regular subscription price).
        if first_amount != req.amount_pence:
            params["nextChargeOn"] = period  # rebill cadence
            # VEROTEL_VERIFY: the param to set the recurring (post-discount)
            # amount is documented as `subscriptionPriceAmount` in v4, but some
            # docs reference `recurringPriceAmount`. Adjust here once verified.
            params["subscriptionPriceAmount"] = amount_decimal

        # One-time setup fee (Blue Tick) — Verotel supports a second line item
        # via `oneClickToken` or a "purchase + subscription" combo flow. The
        # cleanest way for v4 is `priceAmount` containing setup+first-month
        # and `subscriptionPriceAmount` containing just the recurring amount.
        if req.setup_fee_pence > 0:
            combined = first_amount + req.setup_fee_pence
            params["priceAmount"] = f"{combined / 100:.2f}"
            params["description"] = (
                f"{req.tier.capitalize()} subscription + £{req.setup_fee_pence/100:.2f} setup"
            )
            params["subscriptionPriceAmount"] = amount_decimal
            params["nextChargeOn"] = period

        params["signature"] = self._sign(params)
        url = f"{self.checkout_base}?{urllib.parse.urlencode(params)}"
        # The checkout URL itself is the reference until the user pays and
        # we receive the saleID via postback.
        return CheckoutResult(url=url, reference=params["signature"][:16])

    def cancel_subscription(self, subscription_id: str) -> None:
        """Call Verotel's Control Center API to mark the subscription as
        cancelled at period end. Verotel calls this 'cancel rebilling'.
        """
        # VEROTEL_VERIFY: exact endpoint path and param names from the API
        # guide. Below mirrors the public spec format.
        if not (self.api_user and self.api_pass):
            raise ProviderNotConfiguredError(
                "VEROTEL_API_USERNAME / VEROTEL_API_PASSWORD must be set "
                "to cancel subscriptions via the API"
            )
        params = {
            "shopID": self.shop_id,
            "saleID": subscription_id,
            "version": "1",
        }
        params["signature"] = self._sign(params)
        url = f"{self.api_base}/cancel-subscription?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, method="POST")
            # HTTP Basic auth for Control Center API
            import base64
            token = base64.b64encode(f"{self.api_user}:{self.api_pass}".encode()).decode()
            req.add_header("Authorization", f"Basic {token}")
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                if resp.status != 200:
                    raise ProviderApiError(
                        f"Verotel cancel returned {resp.status}",
                        status_code=resp.status,
                        raw=body,
                    )
        except urllib.error.HTTPError as e:
            # 404 from Verotel when the sale is already cancelled — treat as success.
            if e.code == 404:
                return
            raise ProviderApiError(f"HTTP {e.code} from Verotel", status_code=e.code, raw=str(e))
        except urllib.error.URLError as e:
            raise ProviderApiError(f"Network error to Verotel: {e}", raw=str(e))

    def reactivate_subscription(self, subscription_id: str) -> None:
        """Verotel does not document a programmatic uncancel — it must be
        done by the merchant in Control Center. Raise so the router can
        surface this clearly to the user.
        """
        raise ProviderApiError(
            "Reactivation must be done manually in the Verotel Control Center. "
            "The customer cannot reactivate themselves through the app."
        )

    def verify_and_parse_webhook(
        self, *, raw_body: bytes, headers: dict, query_params: dict
    ) -> WebhookEvent:
        """Verotel postbacks are typically sent as GET (query params) or
        POST application/x-www-form-urlencoded. Either way we have a flat
        dict of params plus a `signature` field to verify.
        """
        if query_params:
            params = dict(query_params)
        else:
            # Parse the form body
            params = dict(urllib.parse.parse_qsl(raw_body.decode("utf-8", errors="replace")))

        signature = params.pop("signature", None)
        if not signature:
            raise InvalidWebhookSignatureError("Missing signature in postback")
        expected = self._sign(params)
        if not _constant_time_eq(signature.lower(), expected.lower()):
            raise InvalidWebhookSignatureError("Postback signature does not match")

        event_name = (params.get("event") or params.get("type") or "").lower()
        canonical = _VEROTEL_EVENT_MAP.get(event_name)
        if not canonical:
            # Unknown event — return it untagged so the router can log + skip.
            raise ProviderApiError(f"Unknown Verotel event type: {event_name!r}", raw=str(params))

        # Decode the metadata we round-tripped via custom1.
        metadata: dict = {}
        custom1 = params.get("custom1") or ""
        if custom1:
            try:
                metadata = json.loads(custom1)
            except json.JSONDecodeError:
                # Don't fail the webhook — just leave metadata empty and let
                # the router fall back to looking up by subscription_id.
                metadata = {}

        # Amounts in Verotel postbacks are decimal strings like "18.99".
        amount_pence = None
        amount_str = params.get("amount") or params.get("priceAmount")
        if amount_str:
            try:
                amount_pence = int(round(float(amount_str) * 100))
            except ValueError:
                pass

        return WebhookEvent(
            type=canonical,
            subscription_id=params.get("saleID") or params.get("subscriptionID") or "",
            transaction_id=params.get("referenceID") or params.get("transactionID"),
            customer_email=params.get("email"),
            amount_pence=amount_pence,
            metadata=metadata,
            raw=dict(params),
        )

    # ── Internal ────────────────────────────────────────────────────────────

    def _sign(self, params: dict[str, str]) -> str:
        """Verotel FlexPay v4 signature.

        Algorithm (per public spec):
          1. Drop the `signature` field if present.
          2. Sort remaining params alphabetically by key.
          3. Concatenate signature_key + ':' + key1=value1:key2=value2:...
          4. SHA-256 hex digest, lowercase.

        VEROTEL_VERIFY: confirm the separator (':' vs '|') and whether values
        are URL-encoded before signing. Public doc shows ':' with raw values.
        """
        items = sorted((k, v) for k, v in params.items() if k != "signature")
        canonical = self.signature_key + ":" + ":".join(f"{k}={v}" for k, v in items)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest().lower()


def _constant_time_eq(a: str, b: str) -> bool:
    """Avoid timing attacks on signature comparison."""
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0

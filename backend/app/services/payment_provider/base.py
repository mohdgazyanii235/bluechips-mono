"""
Provider-agnostic interface that the rest of the app interacts with.

When adding a new provider:
  1. Implement `PaymentProvider`.
  2. Register it in `payment_provider.__init__.get_provider()`.
  3. Map the provider's webhook event names to the canonical
     `WebhookEventType` enum below.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Optional, Literal


Billing = Literal["monthly", "annual"]


class WebhookEventType(str, Enum):
    """Canonical event types every provider must map their events to."""
    SUBSCRIPTION_CREATED = "subscription_created"      # First successful charge
    SUBSCRIPTION_RENEWED = "subscription_renewed"      # Recurring rebill succeeded
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"  # User or admin cancelled — access until period end
    SUBSCRIPTION_EXPIRED = "subscription_expired"      # Period ended after cancel, access revoked
    SUBSCRIPTION_REACTIVATED = "subscription_reactivated"  # Cancellation reversed before period end
    REFUND_ISSUED = "refund_issued"                    # A previous charge was refunded
    CHARGEBACK = "chargeback"                          # Customer disputed the charge


@dataclass(frozen=True)
class CheckoutRequest:
    """Inputs the router gives the provider to create a checkout session."""
    amount_pence: int                  # primary recurring amount
    billing: Billing
    tier: str                           # essential / premium / elite / blue_tick
    customer_email: str
    customer_name: str
    success_url: str
    cancel_url: str
    # Free-form metadata. The provider MUST round-trip this back via webhook
    # so we can correlate the event to the originating escort / subscription.
    metadata: dict
    # Optional one-time setup fee (Blue Tick uses this for the £10 setup).
    setup_fee_pence: int = 0
    # Optional percent discount, 1..100, applied to the FIRST charge only.
    discount_percent: Optional[int] = None
    discount_label: Optional[str] = None


@dataclass(frozen=True)
class CheckoutResult:
    """What the provider gives back after creating a checkout session."""
    url: str
    # Provider-specific transaction or session reference. Stored locally as
    # `psp_checkout_reference` for audit. NOT the subscription ID — that's
    # only known after the user pays and the postback fires.
    reference: str


@dataclass(frozen=True)
class WebhookEvent:
    """Provider-agnostic representation of a webhook event."""
    type: WebhookEventType
    # The provider's permanent subscription identifier. For Verotel this is
    # the saleID. For Stripe (if we ever return) it was sub_xxx.
    subscription_id: str
    # The transaction that triggered this event (renewals get a new tx ID
    # per charge; subscription_id stays stable).
    transaction_id: Optional[str] = None
    # Customer email as the provider has it on file.
    customer_email: Optional[str] = None
    # Amount of THIS event (pence). For renewals, this is the rebill amount.
    amount_pence: Optional[int] = None
    # The metadata we passed at checkout time — provider round-trips it back.
    # This is how we recover (escort_id, tier, billing).
    metadata: dict = field(default_factory=dict)
    # Raw event for diagnostics + future audit. Don't parse this in routers.
    raw: dict = field(default_factory=dict)


class PaymentProvider(Protocol):
    """The contract every concrete provider implements."""

    name: str

    def create_subscription_checkout(self, req: CheckoutRequest) -> CheckoutResult:
        """Build a hosted-checkout URL the user will be redirected to."""
        ...

    def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel an active subscription at end of current period.

        Implementations should be idempotent — calling on an already-cancelled
        sub should not raise.
        """
        ...

    def reactivate_subscription(self, subscription_id: str) -> None:
        """Reverse a pending cancellation. May not be supported by all providers."""
        ...

    def verify_and_parse_webhook(
        self, *, raw_body: bytes, headers: dict, query_params: dict
    ) -> WebhookEvent:
        """Validate the webhook signature and parse into a canonical event.

        Raises `InvalidWebhookSignatureError` if validation fails.
        Raises `PaymentProviderError` if the payload is malformed.
        """
        ...

    def supports_in_place_upgrade(self) -> bool:
        """True if the provider can change subscription price mid-cycle.

        Stripe = yes. Verotel = no (must cancel + new checkout).
        The router branches on this to decide whether to do an in-place
        update or to start a fresh checkout.
        """
        ...

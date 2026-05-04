import stripe
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.discount import DiscountCode
from app.models.escort import Escort
from app.models.subscription import Subscription
from app.models.verification import Verification
from app.routers.deps import get_current_verified_escort
from app.schemas.common import MessageResponse
from app.services.email_service import send_verification_submitted_to_admin

router = APIRouter(tags=["Payments"])

TIER_PRICE_MAP = {
    "essential": {"monthly": "STRIPE_ESSENTIAL_PRICE_ID", "annual": "STRIPE_ESSENTIAL_ANNUAL_PRICE_ID"},
    "premium":   {"monthly": "STRIPE_PREMIUM_PRICE_ID",   "annual": "STRIPE_PREMIUM_ANNUAL_PRICE_ID"},
    "elite":     {"monthly": "STRIPE_ELITE_PRICE_ID",     "annual": "STRIPE_ELITE_ANNUAL_PRICE_ID"},
}

TIER_ORDER = {"free": 0, "essential": 1, "premium": 2, "elite": 3}

_TIER_ANNUAL_PRICE_PENCE = {"essential": 24990, "premium": 49990, "elite": 89990}
_ANNUAL_AMOUNTS = {24990, 49990, 89990}


def _stripe_client() -> stripe.StripeClient:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payments not configured")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


async def _build_stripe_discount(
    client: stripe.StripeClient,
    db: AsyncSession,
    body: "CheckoutRequest",
    escort: Escort,
) -> Optional[str]:
    """Validate discount/referral code, apply redemption, return a Stripe coupon ID (or None)."""
    percent_off = None
    duration_months = None
    label = None

    if body.discount_code:
        code = body.discount_code.strip().upper()
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.code == code, DiscountCode.is_active == True)
        )
        dc = result.scalar_one_or_none()
        if not dc:
            raise HTTPException(status_code=400, detail="Discount code is invalid or no longer active")
        if dc.max_redemptions is not None and dc.current_redemptions >= dc.max_redemptions:
            raise HTTPException(status_code=400, detail="This code has reached its maximum number of uses")
        if dc.applicable_tiers and body.tier not in dc.applicable_tiers:
            names = ", ".join(t.title() for t in dc.applicable_tiers)
            raise HTTPException(status_code=400, detail=f"This code is only valid for: {names}")
        percent_off = dc.percent_off
        duration_months = dc.duration_months
        label = code
        dc.current_redemptions += 1
        await db.flush()

    elif body.referral_code:
        code = body.referral_code.strip().upper()
        ref_result = await db.execute(select(Escort).where(Escort.referral_code == code))
        referrer = ref_result.scalar_one_or_none()
        if not referrer:
            raise HTTPException(status_code=400, detail="Referral code not found")
        if referrer.id == escort.id:
            raise HTTPException(status_code=400, detail="You cannot use your own referral code")
        percent_off = 50
        duration_months = 3
        label = f"REF-{code}"
        escort.referred_by_code = code
        await db.flush()

    if percent_off is None:
        return None

    if body.billing == "monthly":
        coupon = client.coupons.create(params={
            "percent_off": percent_off,
            "duration": "repeating",
            "duration_in_months": duration_months,
            "currency": "gbp",
            "name": f"{label}: {percent_off}% off × {duration_months}mo",
        })
    else:
        annual_price = _TIER_ANNUAL_PRICE_PENCE.get(body.tier, 0)
        amount_off = max(1, int((annual_price / 12) * (percent_off / 100) * duration_months))
        coupon = client.coupons.create(params={
            "amount_off": amount_off,
            "currency": "gbp",
            "duration": "once",
            "name": f"{label}: pro-rata {percent_off}% off × {duration_months}mo",
        })

    return coupon.id


class CheckoutRequest(BaseModel):
    tier: str
    billing: str = "monthly"
    discount_code: Optional[str] = None
    referral_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    url: str


@router.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if body.tier not in TIER_PRICE_MAP:
        raise HTTPException(status_code=400, detail="Invalid tier. Choose: essential, premium, or elite")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")

    price_key = TIER_PRICE_MAP[body.tier][body.billing]
    price_id = getattr(settings, price_key, "")
    if not price_id:
        if body.billing == "annual":
            raise HTTPException(status_code=503, detail="Annual billing is not yet available. Please select monthly billing.")
        raise HTTPException(status_code=503, detail="Tier price not configured")

    # Check for pending verification
    pending_result = await db.execute(
        select(Verification).where(
            Verification.escort_id == escort.id,
            Verification.status == "pending",
        )
    )
    if pending_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Your current application is being reviewed. Please wait before subscribing to another tier.",
        )

    client = _stripe_client()

    # Create or reuse Stripe customer
    customer_id = escort.stripe_customer_id
    if not customer_id:
        customer = client.customers.create(params={
            "email": escort.email,
            "name": escort.stage_name,
            "metadata": {"escort_id": str(escort.id)},
        })
        customer_id = customer.id
        escort.stripe_customer_id = customer_id
        await db.flush()

    coupon_id = await _build_stripe_discount(client, db, body, escort)

    session_params: dict = {
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{settings.FRONTEND_URL}/dashboard/verify?payment=success",
        "cancel_url": f"{settings.FRONTEND_URL}/dashboard/subscription?payment=cancelled",
        "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
        "subscription_data": {
            "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
        },
    }
    if coupon_id:
        session_params["discounts"] = [{"coupon": coupon_id}]
    else:
        session_params["allow_promotion_codes"] = True

    session = client.checkout.sessions.create(params=session_params)
    return CheckoutResponse(url=session.url)


@router.get("/payments/subscription")
async def get_subscription(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    # Main subscription (non-blue-tick, active or pending cancellation)
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.escort_id == escort.id,
            Subscription.tier != "blue_tick",
            Subscription.status.in_(["active", "cancelling"]),
        )
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalar_one_or_none()

    # Blue Tick subscription status
    bt_result = await db.execute(
        select(Subscription)
        .where(
            Subscription.escort_id == escort.id,
            Subscription.tier == "blue_tick",
            Subscription.status.in_(["active", "cancelling"]),
        )
        .order_by(Subscription.created_at.desc())
    )
    bt_sub = bt_result.scalar_one_or_none()

    return {
        "tier": escort.subscription_tier,
        "status": sub.status if sub else None,
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        "stripe_subscription_id": sub.stripe_subscription_id if sub else None,
        "pending_tier": sub.pending_tier if sub else None,
        "blue_tick_status": bt_sub.status if bt_sub else ("active" if escort.blue_tick_active else None),
        "blue_tick_current_period_end": bt_sub.current_period_end.isoformat() if bt_sub and bt_sub.current_period_end else None,
    }


@router.get("/payments/invoices")
async def get_invoices(
    escort: Escort = Depends(get_current_verified_escort),
):
    if not escort.stripe_customer_id or not settings.STRIPE_SECRET_KEY:
        return {"invoices": []}
    client = _stripe_client()
    try:
        result = client.invoices.list(params={"customer": escort.stripe_customer_id, "limit": 24})
        invoices = []
        for inv in result.data:
            desc = ""
            if inv.get("lines") and inv["lines"].get("data"):
                desc = inv["lines"]["data"][0].get("description", "")
            invoices.append({
                "id": inv["id"],
                "created": inv["created"],
                "amount_paid": inv["amount_paid"],
                "currency": inv.get("currency", "gbp"),
                "status": inv["status"],
                "pdf_url": inv.get("invoice_pdf"),
                "hosted_url": inv.get("hosted_invoice_url"),
                "description": desc,
            })
        return {"invoices": invoices}
    except Exception as e:
        print(f"[STRIPE] Invoice fetch failed for customer {escort.stripe_customer_id}: {e}")
        return {"invoices": []}


@router.get("/payments/config")
async def get_stripe_config():
    return {"publishable_key": settings.STRIPE_PUBLISHABLE_KEY}


@router.post("/payments/blue-tick-checkout", response_model=CheckoutResponse)
async def create_blue_tick_checkout(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if escort.subscription_tier in ["premium", "elite"]:
        raise HTTPException(
            status_code=400,
            detail="Blue Tick is included free with your Premium or Elite plan. Complete identity verification to activate it — no extra charge."
        )
    if escort.blue_tick_stripe_subscription_id:
        raise HTTPException(status_code=400, detail="You already have an active Blue Tick subscription")

    if not settings.STRIPE_BLUE_TICK_MONTHLY_PRICE_ID or not settings.STRIPE_BLUE_TICK_SETUP_PRICE_ID:
        raise HTTPException(status_code=503, detail="Blue Tick pricing not configured")

    client = _stripe_client()

    customer_id = escort.stripe_customer_id
    if not customer_id:
        customer = client.customers.create(params={
            "email": escort.email,
            "name": escort.stage_name,
            "metadata": {"escort_id": str(escort.id)},
        })
        customer_id = customer.id
        escort.stripe_customer_id = customer_id
        await db.flush()

    session = client.checkout.sessions.create(params={
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [
            {"price": settings.STRIPE_BLUE_TICK_MONTHLY_PRICE_ID, "quantity": 1},
            {"price": settings.STRIPE_BLUE_TICK_SETUP_PRICE_ID, "quantity": 1},
        ],
        "subscription_data": {
            "metadata": {"escort_id": str(escort.id), "tier": "blue_tick"},
        },
        "success_url": f"{settings.FRONTEND_URL}/dashboard/verify?blue_tick=success",
        "cancel_url": f"{settings.FRONTEND_URL}/dashboard/verify?blue_tick=cancelled",
        "metadata": {"escort_id": str(escort.id), "tier": "blue_tick"},
        "allow_promotion_codes": True,
    })

    return CheckoutResponse(url=session.url)


@router.post("/payments/upgrade-tier", response_model=MessageResponse)
async def upgrade_tier(
    body: CheckoutRequest,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    """Switch an existing subscription to a different tier (or billing period) without creating
    a new subscription. The existing Stripe subscription is modified in-place so the escort is
    never charged for two plans simultaneously. Stripe prorates the difference immediately."""
    if body.tier not in TIER_PRICE_MAP:
        raise HTTPException(status_code=400, detail="Invalid tier")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")
    if not escort.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found. Use the checkout flow to subscribe.")

    price_key = TIER_PRICE_MAP[body.tier][body.billing]
    price_id = getattr(settings, price_key, "")
    if not price_id:
        if body.billing == "annual":
            raise HTTPException(status_code=503, detail="Annual billing is not yet available. Please select monthly billing.")
        raise HTTPException(status_code=503, detail="Tier price not configured")

    client = _stripe_client()

    # Retrieve the current subscription to get the item ID and current price
    try:
        sub = client.subscriptions.retrieve(escort.stripe_subscription_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not retrieve your current subscription from Stripe")

    if not sub["items"]["data"]:
        raise HTTPException(status_code=400, detail="Subscription has no items")

    item_id = sub["items"]["data"][0]["id"]
    current_price_id = sub["items"]["data"][0]["price"]["id"]

    # Guard against no-op: compare actual Stripe price IDs, not tier names.
    # This correctly allows switching monthly→annual on the same tier.
    if current_price_id == price_id:
        raise HTTPException(status_code=400, detail="You are already on this plan with this billing period")

    is_downgrade = TIER_ORDER.get(body.tier, 0) < TIER_ORDER.get(escort.subscription_tier, 0)

    if is_downgrade:
        # Downgrade: switch price at next renewal only — no credit, no immediate charge.
        # The user keeps the higher tier until their current billing period ends.
        client.subscriptions.update(
            escort.stripe_subscription_id,
            params={
                "items": [{"id": item_id, "price": price_id}],
                "proration_behavior": "none",
                "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
            },
        )

        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == escort.stripe_subscription_id,
                Subscription.status == "active",
            )
        )
        sub_record = sub_result.scalar_one_or_none()
        if sub_record:
            sub_record.pending_tier = body.tier
            sub_record.stripe_price_id = price_id
        # escort.subscription_tier stays as-is until the period ends

        await db.flush()
        tier_label = body.tier.capitalize()
        return MessageResponse(
            message=f"Downgrade to {tier_label} scheduled. You'll keep your current plan until the end of your billing period."
        )

    # Upgrade: charge prorated difference immediately and switch right away
    client.subscriptions.update(
        escort.stripe_subscription_id,
        params={
            "items": [{"id": item_id, "price": price_id}],
            "proration_behavior": "always_invoice",
            "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
        },
    )

    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == escort.stripe_subscription_id,
            Subscription.status == "active",
        )
    )
    sub_record = sub_result.scalar_one_or_none()
    if sub_record:
        sub_record.tier = body.tier
        sub_record.stripe_price_id = price_id
        sub_record.pending_tier = None  # clear any pending downgrade if upgrading again

    escort.subscription_tier = body.tier
    await db.flush()

    tier_label = body.tier.capitalize()
    return MessageResponse(message=f"Successfully upgraded to {tier_label}! Your billing has been adjusted.")


def _period_end_from_stripe(updated: dict) -> datetime | None:
    ts = updated.get("current_period_end")
    return datetime.utcfromtimestamp(ts) if ts else None


@router.post("/payments/cancel", response_model=MessageResponse)
async def cancel_subscription(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if not escort.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    sub_result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == escort.stripe_subscription_id)
    )
    existing = sub_result.scalar_one_or_none()
    if existing and existing.status == "cancelling":
        raise HTTPException(status_code=400, detail="Your subscription is already scheduled to cancel at the end of the billing period")

    client = _stripe_client()
    updated = client.subscriptions.update(
        escort.stripe_subscription_id,
        params={"cancel_at_period_end": True},
    )
    period_end = _period_end_from_stripe(updated)

    if existing:
        existing.status = "cancelling"
        if period_end:
            existing.current_period_end = period_end
    else:
        # Subscription pre-dates our DB tracking — create the record now
        db.add(Subscription(
            escort_id=escort.id,
            tier=escort.subscription_tier,
            status="cancelling",
            stripe_subscription_id=escort.stripe_subscription_id,
            current_period_end=period_end,
        ))
    await db.flush()
    return MessageResponse(message="Subscription will cancel at the end of the current billing period")


@router.post("/payments/cancel-blue-tick", response_model=MessageResponse)
async def cancel_blue_tick(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if not escort.blue_tick_stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active Blue Tick subscription found")

    bt_result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == escort.blue_tick_stripe_subscription_id)
    )
    existing = bt_result.scalar_one_or_none()
    if existing and existing.status == "cancelling":
        raise HTTPException(status_code=400, detail="Your Blue Tick is already scheduled to cancel at the end of the billing period")

    client = _stripe_client()
    updated = client.subscriptions.update(
        escort.blue_tick_stripe_subscription_id,
        params={"cancel_at_period_end": True},
    )
    period_end = _period_end_from_stripe(updated)

    if existing:
        existing.status = "cancelling"
        if period_end:
            existing.current_period_end = period_end
    else:
        # Blue Tick pre-dates our DB tracking — create the record now
        db.add(Subscription(
            escort_id=escort.id,
            tier="blue_tick",
            status="cancelling",
            stripe_subscription_id=escort.blue_tick_stripe_subscription_id,
            current_period_end=period_end,
        ))
    await db.flush()
    return MessageResponse(message="Blue Tick will cancel at the end of the current billing period")


@router.post("/payments/reactivate", response_model=MessageResponse)
async def reactivate_subscription(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if not escort.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No subscription found")

    sub_result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == escort.stripe_subscription_id)
    )
    existing = sub_result.scalar_one_or_none()
    if not existing or existing.status != "cancelling":
        raise HTTPException(status_code=400, detail="Subscription is not scheduled for cancellation")

    client = _stripe_client()
    client.subscriptions.update(
        escort.stripe_subscription_id,
        params={"cancel_at_period_end": False},
    )
    existing.status = "active"
    await db.flush()
    return MessageResponse(message="Subscription reactivated! Auto-renewal is back on.")


@router.post("/payments/reactivate-blue-tick", response_model=MessageResponse)
async def reactivate_blue_tick(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if not escort.blue_tick_stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No Blue Tick subscription found")

    bt_result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == escort.blue_tick_stripe_subscription_id)
    )
    existing = bt_result.scalar_one_or_none()
    if not existing or existing.status != "cancelling":
        raise HTTPException(status_code=400, detail="Blue Tick is not scheduled for cancellation")

    client = _stripe_client()
    client.subscriptions.update(
        escort.blue_tick_stripe_subscription_id,
        params={"cancel_at_period_end": False},
    )
    existing.status = "active"
    await db.flush()
    return MessageResponse(message="Blue Tick reactivated! Auto-renewal is back on.")


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data, db, background_tasks)

    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data, db)

    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data, db)

    elif event_type == "invoice.paid":
        await _handle_invoice_paid(data, db)

    elif event_type == "invoice.payment_failed":
        pass

    return {"received": True}


async def _handle_checkout_completed(session: dict, db: AsyncSession, background_tasks: BackgroundTasks):
    escort_id = session.get("metadata", {}).get("escort_id")
    tier = session.get("metadata", {}).get("tier")
    subscription_id = session.get("subscription")
    stripe_customer_id = session.get("customer")
    if not escort_id or not tier or not subscription_id:
        return

    result = await db.execute(select(Escort).where(Escort.id == escort_id))
    escort = result.scalar_one_or_none()
    if not escort:
        return

    # Security: verify the Stripe customer matches the stored customer for this escort.
    # Prevents forged metadata from hijacking another escort's subscription.
    if escort.stripe_customer_id and escort.stripe_customer_id != stripe_customer_id:
        print(f"[SECURITY] Stripe webhook customer mismatch for escort {escort_id}: "
              f"expected {escort.stripe_customer_id}, got {stripe_customer_id}")
        return

    # Store customer ID if this is their first payment
    if not escort.stripe_customer_id and stripe_customer_id:
        escort.stripe_customer_id = stripe_customer_id

    sub_obj = stripe.Subscription.retrieve(
        subscription_id, api_key=settings.STRIPE_SECRET_KEY
    )
    period_start = datetime.utcfromtimestamp(sub_obj["current_period_start"])
    period_end = datetime.utcfromtimestamp(sub_obj["current_period_end"])
    price_id = sub_obj["items"]["data"][0]["price"]["id"] if sub_obj["items"]["data"] else None
    amount = sub_obj["items"]["data"][0]["price"]["unit_amount"] if sub_obj["items"]["data"] else None

    if tier == "blue_tick":
        escort.blue_tick_stripe_subscription_id = subscription_id

        # Create / replace Subscription record so cancellation state can be tracked via webhooks
        old_bt_result = await db.execute(
            select(Subscription).where(
                Subscription.escort_id == escort.id,
                Subscription.tier == "blue_tick",
                Subscription.status.in_(["active", "cancelling"]),
            )
        )
        for old_bt in old_bt_result.scalars():
            old_bt.status = "replaced"
        db.add(Subscription(
            escort_id=escort.id,
            tier="blue_tick",
            status="active",
            stripe_subscription_id=subscription_id,
            stripe_price_id=price_id,
            amount_gbp=amount,
            current_period_start=period_start,
            current_period_end=period_end,
        ))

        # Only create a pending verification record if one doesn't already exist
        existing = await db.execute(
            select(Verification).where(
                Verification.escort_id == escort.id,
                Verification.level == 3,
                Verification.status == "pending",
            )
        )
        if not existing.scalar_one_or_none():
            db.add(Verification(
                escort_id=escort.id,
                level=3,
                status="pending",
            ))
            await db.flush()
            background_tasks.add_task(
                send_verification_submitted_to_admin,
                escort_stage_name=escort.stage_name,
                escort_email=escort.email,
                submission_level=3,
            )
        else:
            await db.flush()
        return

    # Standard subscription tier
    old_subs_result = await db.execute(
        select(Subscription).where(
            Subscription.escort_id == escort.id,
            Subscription.status == "active",
        )
    )
    for old_sub in old_subs_result.scalars():
        old_sub.status = "replaced"

    sub = Subscription(
        escort_id=escort.id,
        tier=tier,
        status="active",
        stripe_subscription_id=subscription_id,
        stripe_price_id=price_id,
        amount_gbp=amount,
        current_period_start=period_start,
        current_period_end=period_end,
    )
    db.add(sub)

    escort.subscription_tier = tier
    escort.stripe_subscription_id = subscription_id
    escort.subscription_expires_at = period_end
    await db.flush()


async def _handle_subscription_updated(sub_obj: dict, db: AsyncSession):
    subscription_id = sub_obj.get("id")
    status = sub_obj.get("status")  # active, past_due, cancelled, trialing
    cancel_at_period_end = sub_obj.get("cancel_at_period_end", False)
    escort_id = sub_obj.get("metadata", {}).get("escort_id")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    period_start = datetime.utcfromtimestamp(sub_obj["current_period_start"]) if sub_obj.get("current_period_start") else None
    period_end = datetime.utcfromtimestamp(sub_obj["current_period_end"]) if sub_obj.get("current_period_end") else None

    # Detect billing period renewal: period_start advanced beyond the stored one
    period_renewed = (
        period_start is not None
        and sub.current_period_start is not None
        and period_start > sub.current_period_start
    )

    sub.status = "cancelling" if cancel_at_period_end else status
    if period_start:
        sub.current_period_start = period_start
    if period_end:
        sub.current_period_end = period_end

    if escort_id:
        escort_result = await db.execute(select(Escort).where(Escort.id == escort_id))
        escort = escort_result.scalar_one_or_none()
        if escort:
            if period_end:
                escort.subscription_expires_at = period_end
            # Apply pending downgrade now that the new billing period has started
            if period_renewed and sub.pending_tier:
                escort.subscription_tier = sub.pending_tier
                sub.tier = sub.pending_tier
                sub.pending_tier = None

    await db.flush()


async def _handle_subscription_deleted(sub_obj: dict, db: AsyncSession):
    subscription_id = sub_obj.get("id")
    tier = sub_obj.get("metadata", {}).get("tier")
    escort_id = sub_obj.get("metadata", {}).get("escort_id")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = "cancelled"
        sub.cancelled_at = datetime.utcnow()

    if escort_id:
        escort_result = await db.execute(select(Escort).where(Escort.id == escort_id))
        escort = escort_result.scalar_one_or_none()
        if escort:
            if tier == "blue_tick":
                escort.blue_tick_active = False
                escort.blue_tick_stripe_subscription_id = None
                if escort.verification_level >= 3:
                    escort.verification_level = 2
            else:
                escort.subscription_tier = "free"
                escort.stripe_subscription_id = None
                escort.subscription_expires_at = None
    await db.flush()


async def _handle_invoice_paid(invoice: dict, db: AsyncSession):
    """Award 1 free month credit to the referrer when a referred escort makes their first real payment."""
    if invoice.get("billing_reason") not in ("subscription_cycle", "subscription_create"):
        return
    if invoice.get("amount_paid", 0) == 0:
        return

    stripe_customer_id = invoice.get("customer")
    if not stripe_customer_id:
        return

    result = await db.execute(
        select(Escort).where(
            Escort.stripe_customer_id == stripe_customer_id,
            Escort.referred_by_code.isnot(None),
            Escort.referral_reward_claimed == False,
        )
    )
    referred = result.scalar_one_or_none()
    if not referred:
        return

    referred.referral_reward_claimed = True

    ref_result = await db.execute(
        select(Escort).where(Escort.referral_code == referred.referred_by_code)
    )
    referrer = ref_result.scalar_one_or_none()
    if not referrer or not referrer.stripe_customer_id:
        await db.flush()
        return

    sub_result = await db.execute(
        select(Subscription)
        .where(
            Subscription.escort_id == referrer.id,
            Subscription.status.in_(["active", "cancelling"]),
            Subscription.tier != "blue_tick",
        )
        .order_by(Subscription.created_at.desc())
    )
    referrer_sub = sub_result.scalar_one_or_none()
    if not referrer_sub or not referrer_sub.amount_gbp:
        await db.flush()
        return

    credit = (referrer_sub.amount_gbp // 12
              if referrer_sub.amount_gbp in _ANNUAL_AMOUNTS
              else referrer_sub.amount_gbp)
    try:
        stripe.Customer.create_balance_transaction(
            referrer.stripe_customer_id,
            amount=-credit,
            currency="gbp",
            description=f"Referral reward: {referred.stage_name} joined using your code",
            api_key=settings.STRIPE_SECRET_KEY,
        )
    except Exception as e:
        print(f"[STRIPE] Referral credit failed for referrer {referrer.id}: {e}")

    await db.flush()

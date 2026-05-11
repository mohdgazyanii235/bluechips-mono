import calendar as cal
import stripe
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.discount import DiscountCode
from app.models.escort import Escort, EscortPhoto
from app.models.platform_config import PlatformConfig
from app.models.subscription import Subscription
from app.models.verification import Verification
from app.models.webhook_event import WebhookEvent
from app.routers.deps import get_current_verified_escort
from app.schemas.common import MessageResponse
from app.services.email_service import (
    send_verification_submitted_to_admin,
    send_downgrade_photo_warning,
    send_profile_paused_photo_limit,
)

_TIER_PHOTO_LIMITS = {"free": 3, "essential": 8, "premium": 50, "elite": 50}

router = APIRouter(tags=["Payments"])

TIER_ORDER = {"free": 0, "essential": 1, "premium": 2, "elite": 3}

# Maps tier+billing → PlatformConfig field names for Stripe price ID and pence amount
_TIER_STRIPE_FIELD = {
    "essential": {"monthly": "stripe_essential_monthly_id", "annual": "stripe_essential_annual_id"},
    "premium":   {"monthly": "stripe_premium_monthly_id",   "annual": "stripe_premium_annual_id"},
    "elite":     {"monthly": "stripe_elite_monthly_id",     "annual": "stripe_elite_annual_id"},
}
_TIER_PENCE_FIELD = {
    "essential": {"monthly": "essential_monthly_pence", "annual": "essential_annual_pence"},
    "premium":   {"monthly": "premium_monthly_pence",   "annual": "premium_annual_pence"},
    "elite":     {"monthly": "elite_monthly_pence",     "annual": "elite_annual_pence"},
}


# ---------------------------------------------------------------------------
# Billing cycle helpers — all subscriptions anchor to 1st of month / Jan 1st
# ---------------------------------------------------------------------------

def _next_month_first() -> date:
    """Calendar date for the 1st of next month (UTC today)."""
    today = datetime.utcnow().date()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def _next_jan_first() -> date:
    """Calendar date for January 1st of next year (UTC today)."""
    return date(datetime.utcnow().year + 1, 1, 1)


def _to_unix(d: date) -> int:
    """Convert a date (UTC midnight) to a Unix timestamp."""
    return int(cal.timegm(datetime(d.year, d.month, d.day).timetuple()))


def _monthly_prorate_info() -> dict:
    """
    Returns info needed to prorate a monthly subscription based on the current calendar month.
    remaining_days: days from today until the 1st of next month.
    days_in_month: total days in the current calendar month.
    next_1st: the date for the 1st of next month.
    fraction: remaining_days / days_in_month
    """
    today = datetime.utcnow().date()
    next_1st = _next_month_first()
    remaining_days = (next_1st - today).days
    days_in_month = cal.monthrange(today.year, today.month)[1]
    return {
        "today": today,
        "next_1st": next_1st,
        "remaining_days": remaining_days,
        "days_in_month": days_in_month,
        "fraction": remaining_days / days_in_month,
    }


def _annual_prorate_info() -> dict:
    """
    Returns info needed to prorate an annual subscription based on the current calendar year.
    """
    today = datetime.utcnow().date()
    next_jan1 = _next_jan_first()
    remaining_days = (next_jan1 - today).days
    days_in_year = 366 if (today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)) else 365
    return {
        "today": today,
        "next_1st": next_jan1,
        "remaining_days": remaining_days,
        "days_in_month": days_in_year,  # reuse field name for generic use
        "fraction": remaining_days / days_in_year,
    }


async def _get_platform_config(db: AsyncSession) -> PlatformConfig:
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=503, detail="Platform pricing not configured")
    return cfg


def _stripe_client() -> stripe.StripeClient:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payments not configured")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


async def _build_stripe_discount(
    client: stripe.StripeClient,
    db: AsyncSession,
    body: "CheckoutRequest",
    escort: Escort,
    cfg: PlatformConfig,
) -> Optional[str]:
    """Validate discount/referral code, apply redemption, return a Stripe coupon ID (or None)."""
    percent_off = None
    duration_months = None
    label = None

    # Auto-apply the code attached at signup (e.g. founding-member invite link) if
    # the user didn't explicitly enter a code. Only applies once — once redeemed
    # (current_redemptions >= max_redemptions) the auto-apply is silently skipped.
    effective_discount_code = body.discount_code
    if not effective_discount_code and not body.referral_code and escort.signup_discount_code_id:
        auto_result = await db.execute(
            select(DiscountCode).where(
                DiscountCode.id == escort.signup_discount_code_id,
                DiscountCode.is_active == True,
            )
        )
        auto_dc = auto_result.scalar_one_or_none()
        if auto_dc and (auto_dc.max_redemptions is None or auto_dc.current_redemptions < auto_dc.max_redemptions):
            # Only auto-apply if the code is valid for the selected tier
            if not auto_dc.applicable_tiers or body.tier in auto_dc.applicable_tiers:
                effective_discount_code = auto_dc.code

    if effective_discount_code:
        code = effective_discount_code.strip().upper()
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
        annual_pence = getattr(cfg, _TIER_PENCE_FIELD[body.tier]["annual"], 0)
        amount_off = max(1, int((annual_pence / 12) * (percent_off / 100) * duration_months))
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
    if body.tier not in _TIER_STRIPE_FIELD:
        raise HTTPException(status_code=400, detail="Invalid tier. Choose: essential, premium, or elite")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")

    cfg = await _get_platform_config(db)
    stripe_field = _TIER_STRIPE_FIELD[body.tier][body.billing]
    price_id = getattr(cfg, stripe_field, "")
    if not price_id:
        if body.billing == "annual":
            raise HTTPException(status_code=503, detail="Annual billing is not yet available. Please select monthly billing.")
        raise HTTPException(status_code=503, detail="Tier price not configured")

    # Block if a verification is pending
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

    coupon_id = await _build_stripe_discount(client, db, body, escort, cfg)

    # Anchor billing to 1st of next month (monthly) or Jan 1st (annual)
    # Stripe will automatically prorate the first invoice for the partial period.
    anchor_date = _next_month_first() if body.billing == "monthly" else _next_jan_first()
    anchor_ts = _to_unix(anchor_date)

    session_params: dict = {
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{settings.FRONTEND_URL}/dashboard/verify?payment=success",
        "cancel_url": f"{settings.FRONTEND_URL}/dashboard/subscription?payment=cancelled",
        "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
        "subscription_data": {
            "metadata": {"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
            "billing_cycle_anchor": anchor_ts,
            "proration_behavior": "create_prorations",
        },
    }
    if coupon_id:
        session_params["discounts"] = [{"coupon": coupon_id}]
    else:
        session_params["allow_promotion_codes"] = True

    session = client.checkout.sessions.create(params=session_params)
    return CheckoutResponse(url=session.url)


@router.get("/payments/upgrade-preview")
async def get_upgrade_preview(
    tier: str,
    billing: str = "monthly",
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns what the escort will be charged (or told) when changing plans.
    Used by the frontend to show a confirmation modal before proceeding.
    """
    if tier not in _TIER_STRIPE_FIELD:
        raise HTTPException(status_code=400, detail="Invalid tier")
    if billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")

    cfg = await _get_platform_config(db)
    current_tier = escort.subscription_tier

    # Determine proration window
    if billing == "annual":
        info = _annual_prorate_info()
    else:
        info = _monthly_prorate_info()

    remaining_days: int = info["remaining_days"]
    total_days: int = info["days_in_month"]
    # Format as "1 July 2026"
    d: date = info["next_1st"]
    next_billing_date: str = f"{d.day} {d.strftime('%B')} {d.year}"

    new_price_pence: int = getattr(cfg, _TIER_PENCE_FIELD[tier][billing], 0)

    is_upgrade = TIER_ORDER.get(tier, 0) > TIER_ORDER.get(current_tier, 0)

    if current_tier == "free" or not escort.stripe_subscription_id:
        # New subscription via checkout — show what Stripe will charge for the partial month
        charge_now = round(new_price_pence * remaining_days / total_days)
        return {
            "type": "new",
            "from_tier": current_tier,
            "to_tier": tier,
            "billing": billing,
            "charge_now_pence": charge_now,
            "then_pence": new_price_pence,
            "remaining_days": remaining_days,
            "total_days": total_days,
            "next_billing_date": next_billing_date,
        }

    old_billing = "monthly"  # assume monthly for current sub (most common)
    old_price_pence: int = getattr(cfg, _TIER_PENCE_FIELD[current_tier][old_billing], 0)

    if is_upgrade:
        diff = new_price_pence - old_price_pence
        charge_now = max(0, round(diff * remaining_days / total_days))
        return {
            "type": "upgrade",
            "from_tier": current_tier,
            "to_tier": tier,
            "billing": billing,
            "charge_now_pence": charge_now,
            "then_pence": new_price_pence,
            "remaining_days": remaining_days,
            "total_days": total_days,
            "next_billing_date": next_billing_date,
        }
    else:
        # Downgrade: no charge today, effective from next billing date
        return {
            "type": "downgrade",
            "from_tier": current_tier,
            "to_tier": tier,
            "billing": billing,
            "charge_now_pence": 0,
            "then_pence": new_price_pence,
            "remaining_days": remaining_days,
            "total_days": total_days,
            "next_billing_date": next_billing_date,
            "effective_date": next_billing_date,
        }


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

    cfg = await _get_platform_config(db)
    if not cfg.stripe_blue_tick_monthly_id or not cfg.stripe_blue_tick_setup_id:
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

    # Anchor Blue Tick to 1st of next month as well
    anchor_ts = _to_unix(_next_month_first())

    session = client.checkout.sessions.create(params={
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [
            {"price": cfg.stripe_blue_tick_monthly_id, "quantity": 1},
            {"price": cfg.stripe_blue_tick_setup_id, "quantity": 1},
        ],
        "subscription_data": {
            "metadata": {"escort_id": str(escort.id), "tier": "blue_tick"},
            "billing_cycle_anchor": anchor_ts,
            "proration_behavior": "create_prorations",
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
    background_tasks: BackgroundTasks,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    """
    Switch an existing subscription to a different tier.

    Upgrades: charge a calendar-month pro-rata amount immediately (difference × remaining days / days in month),
    then update the subscription price. No Stripe-side proration — we control the exact amount.

    Downgrades: switch price at next billing period with no immediate charge.
    """
    if body.tier not in _TIER_STRIPE_FIELD:
        raise HTTPException(status_code=400, detail="Invalid tier")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")
    if not escort.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found. Use the checkout flow to subscribe.")

    cfg = await _get_platform_config(db)
    stripe_field = _TIER_STRIPE_FIELD[body.tier][body.billing]
    price_id = getattr(cfg, stripe_field, "")
    if not price_id:
        if body.billing == "annual":
            raise HTTPException(status_code=503, detail="Annual billing is not yet available. Please select monthly billing.")
        raise HTTPException(status_code=503, detail="Tier price not configured")

    client = _stripe_client()

    try:
        sub = client.subscriptions.retrieve(escort.stripe_subscription_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not retrieve your current subscription from Stripe")

    if not sub["items"]["data"]:
        raise HTTPException(status_code=400, detail="Subscription has no items")

    item_id = sub["items"]["data"][0]["id"]
    current_price_id = sub["items"]["data"][0]["price"]["id"]

    if current_price_id == price_id:
        raise HTTPException(status_code=400, detail="You are already on this plan with this billing period")

    is_downgrade = TIER_ORDER.get(body.tier, 0) < TIER_ORDER.get(escort.subscription_tier, 0)

    if is_downgrade:
        # Downgrade: switch price at next renewal — no immediate charge.
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
        await db.flush()

        # Send photo warning email if escort has more photos than new tier allows
        new_photo_limit = _TIER_PHOTO_LIMITS.get(body.tier, 3)
        from sqlalchemy import func as sqlfunc
        photo_count_result = await db.execute(
            select(sqlfunc.count()).select_from(EscortPhoto).where(EscortPhoto.escort_id == escort.id)
        )
        photo_count = photo_count_result.scalar() or 0
        if photo_count > new_photo_limit:
            info = _monthly_prorate_info()
            d = info["next_1st"]
            billing_date_str = f"{d.day} {d.strftime('%B')} {d.year}"
            background_tasks.add_task(
                send_downgrade_photo_warning,
                escort_email=escort.email,
                stage_name=escort.stage_name,
                current_photos=photo_count,
                new_limit=new_photo_limit,
                excess=photo_count - new_photo_limit,
                new_tier=body.tier,
                billing_date=billing_date_str,
            )

        tier_label = body.tier.capitalize()
        return MessageResponse(
            message=f"Downgrade to {tier_label} scheduled. You'll keep your current plan until the end of your billing period."
        )

    # ── Upgrade: charge calendar-based pro-rata immediately ──────────────────

    if body.billing == "annual":
        info = _annual_prorate_info()
    else:
        info = _monthly_prorate_info()

    remaining_days: int = info["remaining_days"]
    total_days: int = info["days_in_month"]
    today = info["today"]

    # Current subscription's billing interval
    current_interval = sub["items"]["data"][0]["price"].get("recurring", {}).get("interval", "month")
    old_billing = "annual" if current_interval == "year" else "monthly"

    old_price_pence: int = getattr(cfg, _TIER_PENCE_FIELD[escort.subscription_tier][old_billing], 0)
    new_price_pence: int = getattr(cfg, _TIER_PENCE_FIELD[body.tier][body.billing], 0)

    # If switching billing period along with tier, compare monthly-equivalent rates
    if old_billing != body.billing:
        old_monthly = getattr(cfg, _TIER_PENCE_FIELD[escort.subscription_tier]["monthly"], 0)
        new_monthly = getattr(cfg, _TIER_PENCE_FIELD[body.tier]["monthly"], 0)
        diff_pence = new_monthly - old_monthly
    else:
        diff_pence = new_price_pence - old_price_pence

    pro_rata_pence = max(0, round(diff_pence * remaining_days / total_days))

    # Create and immediately charge a Stripe invoice for the pro-rata amount
    if pro_rata_pence > 0:
        if not escort.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No Stripe customer found for this account")
        invoice_id: Optional[str] = None
        try:
            month_name = today.strftime("%B")
            client.invoice_items.create(params={
                "customer": escort.stripe_customer_id,
                "amount": pro_rata_pence,
                "currency": "gbp",
                "description": (
                    f"Plan upgrade: {escort.subscription_tier.capitalize()} → {body.tier.capitalize()} "
                    f"({remaining_days} of {total_days} days remaining in {month_name})"
                ),
            })
            invoice_obj = client.invoices.create(params={
                "customer": escort.stripe_customer_id,
                "auto_advance": False,
            })
            invoice_id = invoice_obj.id
            finalized_invoice = client.invoices.finalize_invoice(invoice_id, params={})
            if finalized_invoice.amount_due > 0 and finalized_invoice.status != "paid":
                client.invoices.pay(invoice_id, params={})
        except stripe.StripeError as e:
            err_msg = getattr(e, "user_message", None) or str(e)
            if invoice_id:
                try:
                    client.invoices.void_invoice(invoice_id, params={})
                except Exception:
                    pass
            raise HTTPException(status_code=402, detail=f"Payment failed: {err_msg}")

    # Update subscription price — no Stripe proration (we already charged manually above)
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
        sub_record.tier = body.tier
        sub_record.stripe_price_id = price_id
        sub_record.pending_tier = None

    escort.subscription_tier = body.tier
    # Auto-grant Blue Tick when upgrading to premium/elite if identity already verified
    if body.tier in ("premium", "elite") and escort.verification_level >= 2:
        escort.blue_tick_active = True
    await db.flush()

    tier_label = body.tier.capitalize()
    return MessageResponse(message=f"Successfully upgraded to {tier_label}!")


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

    event_id = event["id"]
    event_type = event["type"]
    data = event["data"]["object"]

    # Idempotency: record the event ID before processing. ON CONFLICT DO NOTHING
    # means duplicate deliveries are no-ops. The insert is part of the request
    # transaction, so if processing fails downstream, the rollback also rolls
    # back the event_id insertion and Stripe will retry.
    dedup_stmt = pg_insert(WebhookEvent).values(
        id=event_id,
        event_type=event_type,
        received_at=datetime.utcnow(),
    ).on_conflict_do_nothing(index_elements=["id"])
    result = await db.execute(dedup_stmt)
    if result.rowcount == 0:
        # Already processed — return 200 so Stripe stops retrying
        return {"received": True, "duplicate": True}

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data, db, background_tasks)

    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data, db, background_tasks)

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
    if escort.stripe_customer_id and escort.stripe_customer_id != stripe_customer_id:
        print(f"[SECURITY] Stripe webhook customer mismatch for escort {escort_id}: "
              f"expected {escort.stripe_customer_id}, got {stripe_customer_id}")
        return

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


async def _handle_subscription_updated(sub_obj: dict, db: AsyncSession, background_tasks: BackgroundTasks):
    subscription_id = sub_obj.get("id")
    status = sub_obj.get("status")
    cancel_at_period_end = sub_obj.get("cancel_at_period_end", False)
    event_customer_id = sub_obj.get("customer")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    period_start = datetime.utcfromtimestamp(sub_obj["current_period_start"]) if sub_obj.get("current_period_start") else None
    period_end = datetime.utcfromtimestamp(sub_obj["current_period_end"]) if sub_obj.get("current_period_end") else None

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

    # Load escort via our DB FK on the Subscription (NOT from webhook metadata).
    # Then defence-in-depth verify the Stripe customer matches our stored one.
    escort_result = await db.execute(select(Escort).where(Escort.id == sub.escort_id))
    escort = escort_result.scalar_one_or_none()
    if escort and event_customer_id and escort.stripe_customer_id and escort.stripe_customer_id != event_customer_id:
        print(f"[SECURITY] subscription.updated customer mismatch for sub {subscription_id}: "
              f"expected {escort.stripe_customer_id}, got {event_customer_id}")
        return
    if escort:
        if period_end:
            escort.subscription_expires_at = period_end
        if period_renewed and sub.pending_tier:
            new_tier = sub.pending_tier
            escort.subscription_tier = new_tier
            sub.tier = new_tier
            sub.pending_tier = None
            # Auto-grant Blue Tick when pending upgrade becomes active at period renewal
            if new_tier in ("premium", "elite") and escort.verification_level >= 2:
                escort.blue_tick_active = True
            # Pause profile if photo count exceeds new tier's limit
            new_photo_limit = _TIER_PHOTO_LIMITS.get(new_tier, 3)
            from sqlalchemy import func as sqlfunc
            photo_count_res = await db.execute(
                select(sqlfunc.count()).select_from(EscortPhoto).where(EscortPhoto.escort_id == escort.id)
            )
            photo_count = photo_count_res.scalar() or 0
            if photo_count > new_photo_limit:
                escort.is_approved = False
                background_tasks.add_task(
                    send_profile_paused_photo_limit,
                    escort_email=escort.email,
                    stage_name=escort.stage_name,
                    current_photos=photo_count,
                    photo_limit=new_photo_limit,
                    new_tier=new_tier,
                )

    await db.flush()


async def _handle_subscription_deleted(sub_obj: dict, db: AsyncSession):
    subscription_id = sub_obj.get("id")
    event_customer_id = sub_obj.get("customer")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()

    # Use the tier from OUR DB record, not the webhook metadata
    tier = sub.tier

    escort_result = await db.execute(select(Escort).where(Escort.id == sub.escort_id))
    escort = escort_result.scalar_one_or_none()
    if escort and event_customer_id and escort.stripe_customer_id and escort.stripe_customer_id != event_customer_id:
        print(f"[SECURITY] subscription.deleted customer mismatch for sub {subscription_id}: "
              f"expected {escort.stripe_customer_id}, got {event_customer_id}")
        return
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

    # If amount > £50 (5000p), treat as annual and divide by 12 to get monthly credit
    amount = referrer_sub.amount_gbp
    credit = amount // 12 if amount > 5000 else amount

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

"""
Payments router — provider-agnostic.

All payment-provider specifics live in app.services.payment_provider.*.
This router only orchestrates business logic + persists state.
"""
import calendar as cal
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.discount import DiscountCode
from app.models.escort import Escort, EscortPhoto
from app.models.outreach import OutreachProspect, STATUS_SIGNED_UP
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
from app.services.payment_provider import (
    get_provider,
    InvalidWebhookSignatureError,
    ProviderApiError,
)
from app.services.payment_provider.base import (
    CheckoutRequest as ProviderCheckoutRequest,
    WebhookEventType,
)

_TIER_PHOTO_LIMITS = {"free": 3, "essential": 8, "premium": 50, "elite": 50}

router = APIRouter(tags=["Payments"])

TIER_ORDER = {"free": 0, "essential": 1, "premium": 2, "elite": 3}

_TIER_PENCE_FIELD = {
    "essential": {"monthly": "essential_monthly_pence", "annual": "essential_annual_pence"},
    "premium":   {"monthly": "premium_monthly_pence",   "annual": "premium_annual_pence"},
    "elite":     {"monthly": "elite_monthly_pence",     "annual": "elite_annual_pence"},
}


# ─── Calendar helpers (provider-agnostic) ────────────────────────────────────

def _next_month_first() -> date:
    today = datetime.utcnow().date()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def _next_jan_first() -> date:
    return date(datetime.utcnow().year + 1, 1, 1)


def _monthly_prorate_info() -> dict:
    today = datetime.utcnow().date()
    next_1st = _next_month_first()
    days_in_month = cal.monthrange(today.year, today.month)[1]
    return {
        "today": today,
        "next_1st": next_1st,
        "remaining_days": (next_1st - today).days,
        "days_in_month": days_in_month,
        "fraction": (next_1st - today).days / days_in_month,
    }


def _annual_prorate_info() -> dict:
    today = datetime.utcnow().date()
    next_jan1 = _next_jan_first()
    days_in_year = 366 if (today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)) else 365
    return {
        "today": today,
        "next_1st": next_jan1,
        "remaining_days": (next_jan1 - today).days,
        "days_in_month": days_in_year,
        "fraction": (next_jan1 - today).days / days_in_year,
    }


async def _get_platform_config(db: AsyncSession) -> PlatformConfig:
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=503, detail="Platform pricing not configured")
    return cfg


# ─── Discount code resolution (provider-agnostic) ────────────────────────────

async def _resolve_discount(
    body: "CheckoutRequest", escort: Escort, db: AsyncSession
) -> tuple[Optional[int], Optional[str], Optional[DiscountCode]]:
    """Validate the discount/referral code and return (percent_off, label, dc).

    Does NOT mutate the discount code's `current_redemptions` — that happens
    later, only on successful checkout creation, so we don't burn redemptions
    on flow errors. Also applies the founding-member claim side effects.
    """
    # Auto-apply the code attached at signup if user didn't enter one.
    effective_code = body.discount_code
    if not effective_code and not body.referral_code and escort.signup_discount_code_id:
        auto_result = await db.execute(
            select(DiscountCode).where(
                DiscountCode.id == escort.signup_discount_code_id,
                DiscountCode.is_active == True,
            )
        )
        auto_dc = auto_result.scalar_one_or_none()
        if auto_dc and (auto_dc.max_redemptions is None or auto_dc.current_redemptions < auto_dc.max_redemptions):
            if not auto_dc.applicable_tiers or body.tier in auto_dc.applicable_tiers:
                effective_code = auto_dc.code

    if effective_code:
        code = effective_code.strip().upper()
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
        return dc.percent_off, code, dc

    if body.referral_code:
        code = body.referral_code.strip().upper()
        ref_result = await db.execute(select(Escort).where(Escort.referral_code == code))
        referrer = ref_result.scalar_one_or_none()
        if not referrer:
            raise HTTPException(status_code=400, detail="Referral code not found")
        if referrer.id == escort.id:
            raise HTTPException(status_code=400, detail="You cannot use your own referral code")
        escort.referred_by_code = code
        return 50, f"REF-{code}", None

    return None, None, None


async def _commit_discount(
    dc: Optional[DiscountCode], escort: Escort, db: AsyncSession
) -> None:
    """Now that checkout was successfully created, redeem the code and apply
    founding-member side effects."""
    if not dc:
        return
    dc.current_redemptions += 1

    code_str = dc.code
    if code_str.startswith("FM-") and not escort.is_founding_member:
        from sqlalchemy import update as sql_update
        claim_result = await db.execute(
            sql_update(PlatformConfig)
            .where(
                PlatformConfig.id == 1,
                PlatformConfig.founding_offer_active == True,
                PlatformConfig.founding_offer_signups < PlatformConfig.founding_offer_limit,
            )
            .values(founding_offer_signups=PlatformConfig.founding_offer_signups + 1)
        )
        if claim_result.rowcount == 1:
            escort.is_founding_member = True
            escort.founding_member_since = datetime.utcnow()
            if not escort.signup_discount_code_id:
                escort.signup_discount_code_id = dc.id
            prospect_result = await db.execute(
                select(OutreachProspect).where(OutreachProspect.discount_code_id == dc.id)
            )
            prospect = prospect_result.scalar_one_or_none()
            if prospect and not prospect.converted_escort_id:
                prospect.converted_escort_id = escort.id
                prospect.signed_up_at = datetime.utcnow()
                prospect.status = STATUS_SIGNED_UP


# ─── Request / response models ───────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    tier: str
    billing: str = "monthly"
    discount_code: Optional[str] = None
    referral_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    url: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    if body.tier not in _TIER_PENCE_FIELD:
        raise HTTPException(status_code=400, detail="Invalid tier. Choose: essential, premium, or elite")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")

    cfg = await _get_platform_config(db)
    unit_amount = getattr(cfg, _TIER_PENCE_FIELD[body.tier][body.billing], 0)
    if not unit_amount or unit_amount <= 0:
        raise HTTPException(status_code=503, detail="Tier price not configured")

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

    percent_off, label, dc = await _resolve_discount(body, escort, db)
    provider = get_provider()

    try:
        result = provider.create_subscription_checkout(ProviderCheckoutRequest(
            amount_pence=unit_amount,
            billing=body.billing,  # type: ignore[arg-type]
            tier=body.tier,
            customer_email=escort.email,
            customer_name=escort.stage_name,
            success_url=f"{settings.FRONTEND_URL}/dashboard/verify?payment=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/subscription?payment=cancelled",
            metadata={"escort_id": str(escort.id), "tier": body.tier, "billing": body.billing},
            discount_percent=percent_off,
            discount_label=label,
        ))
    except ProviderApiError as e:
        raise HTTPException(status_code=502, detail=f"Payment provider error: {e}")

    await _commit_discount(dc, escort, db)
    # Stash the reference so we can correlate the post-checkout postback.
    escort.psp_provider = provider.name
    await db.flush()

    return CheckoutResponse(url=result.url)


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
    if escort.psp_blue_tick_subscription_id or escort.blue_tick_stripe_subscription_id:
        raise HTTPException(status_code=400, detail="You already have an active Blue Tick subscription")

    cfg = await _get_platform_config(db)
    setup_pence = cfg.blue_tick_setup_pence or 0
    monthly_pence = cfg.blue_tick_monthly_pence or 0
    if setup_pence <= 0 or monthly_pence <= 0:
        raise HTTPException(status_code=503, detail="Blue Tick pricing not configured")

    provider = get_provider()
    try:
        result = provider.create_subscription_checkout(ProviderCheckoutRequest(
            amount_pence=monthly_pence,
            billing="monthly",
            tier="blue_tick",
            customer_email=escort.email,
            customer_name=escort.stage_name,
            success_url=f"{settings.FRONTEND_URL}/dashboard/verify?blue_tick=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/verify?blue_tick=cancelled",
            metadata={"escort_id": str(escort.id), "tier": "blue_tick"},
            setup_fee_pence=setup_pence,
        ))
    except ProviderApiError as e:
        raise HTTPException(status_code=502, detail=f"Payment provider error: {e}")

    escort.psp_provider = provider.name
    await db.flush()
    return CheckoutResponse(url=result.url)


@router.get("/payments/upgrade-preview")
async def get_upgrade_preview(
    tier: str,
    billing: str = "monthly",
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    """Tells the frontend what changing tier will cost.

    NOTE on provider differences: Verotel does NOT support in-place price
    changes mid-subscription. For upgrades we have to cancel the existing
    sub and start a fresh checkout. The preview reflects this.
    """
    if tier not in _TIER_PENCE_FIELD:
        raise HTTPException(status_code=400, detail="Invalid tier")
    if billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing must be 'monthly' or 'annual'")

    cfg = await _get_platform_config(db)
    current_tier = escort.subscription_tier
    info = _annual_prorate_info() if billing == "annual" else _monthly_prorate_info()
    new_price_pence = getattr(cfg, _TIER_PENCE_FIELD[tier][billing], 0)
    d = info["next_1st"]
    next_billing_date = f"{d.day} {d.strftime('%B')} {d.year}"

    is_upgrade = TIER_ORDER.get(tier, 0) > TIER_ORDER.get(current_tier, 0)
    has_sub = bool(escort.psp_subscription_id or escort.stripe_subscription_id)

    if current_tier == "free" or not has_sub:
        charge_now = round(new_price_pence * info["remaining_days"] / info["days_in_month"])
        return {
            "type": "new",
            "from_tier": current_tier, "to_tier": tier, "billing": billing,
            "charge_now_pence": charge_now, "then_pence": new_price_pence,
            "remaining_days": info["remaining_days"], "total_days": info["days_in_month"],
            "next_billing_date": next_billing_date,
        }

    if is_upgrade:
        # Verotel can't change price mid-cycle. Tell the UI the user will be
        # charged the full first-period price on the new tier (we cancel old
        # immediately, start new checkout).
        return {
            "type": "upgrade_new_checkout",
            "from_tier": current_tier, "to_tier": tier, "billing": billing,
            "charge_now_pence": new_price_pence, "then_pence": new_price_pence,
            "remaining_days": info["remaining_days"], "total_days": info["days_in_month"],
            "next_billing_date": next_billing_date,
            "notice": "Your current subscription will be cancelled and a new checkout opened.",
        }
    return {
        "type": "downgrade",
        "from_tier": current_tier, "to_tier": tier, "billing": billing,
        "charge_now_pence": 0, "then_pence": new_price_pence,
        "remaining_days": info["remaining_days"], "total_days": info["days_in_month"],
        "next_billing_date": next_billing_date,
        "effective_date": next_billing_date,
        "notice": "Your current plan stays active until the next billing date. Then you'll need to checkout on the new tier.",
    }


@router.post("/payments/upgrade-tier", response_model=CheckoutResponse)
async def upgrade_tier_via_new_checkout(
    body: CheckoutRequest,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    """Verotel cannot modify a subscription's price mid-cycle. So 'upgrade'
    actually means: cancel the existing subscription, then send the user
    through a fresh checkout for the new tier.

    Returns a checkout URL the frontend should redirect to.
    """
    if not (escort.psp_subscription_id or escort.stripe_subscription_id):
        raise HTTPException(status_code=400, detail="No active subscription found. Use the checkout flow to subscribe.")

    provider = get_provider()
    if not provider.supports_in_place_upgrade():
        # Cancel the current one first (it stays active till period end —
        # user pays the new one and the old one expires naturally).
        sub_id = escort.psp_subscription_id
        if sub_id:
            try:
                provider.cancel_subscription(sub_id)
            except ProviderApiError as e:
                # Surface this but don't block — the user can retry cancellation
                # from the admin if it failed. Logging only.
                print(f"[upgrade] cancel failed for {sub_id}: {e}")
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.psp_subscription_id == sub_id,
                Subscription.status == "active",
            )
        )
        existing = sub_result.scalar_one_or_none()
        if existing:
            existing.status = "cancelling"
        await db.flush()

    # Fall through to a fresh checkout flow — same as create_checkout_session.
    return await create_checkout_session(body, escort, db)


@router.get("/payments/subscription")
async def get_subscription(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.escort_id == escort.id,
            Subscription.tier != "blue_tick",
            Subscription.status.in_(["active", "cancelling"]),
        )
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalars().first()

    bt_result = await db.execute(
        select(Subscription)
        .where(
            Subscription.escort_id == escort.id,
            Subscription.tier == "blue_tick",
            Subscription.status.in_(["active", "cancelling"]),
        )
        .order_by(Subscription.created_at.desc())
    )
    bt_sub = bt_result.scalars().first()

    return {
        "tier": escort.subscription_tier,
        "status": sub.status if sub else None,
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        "psp_subscription_id": sub.psp_subscription_id if sub else None,
        "pending_tier": sub.pending_tier if sub else None,
        "blue_tick_status": bt_sub.status if bt_sub else ("active" if escort.blue_tick_active else None),
        "blue_tick_current_period_end": bt_sub.current_period_end.isoformat() if bt_sub and bt_sub.current_period_end else None,
    }


@router.get("/payments/invoices")
async def get_invoices(escort: Escort = Depends(get_current_verified_escort), db: AsyncSession = Depends(get_db)):
    """Invoices = our local subscription rows + their status. Verotel doesn't
    expose a hosted invoice listing API, so we derive history from DB."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.escort_id == escort.id)
        .order_by(Subscription.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()
    return {
        "invoices": [
            {
                "id": str(r.id),
                "created": int(r.created_at.timestamp()),
                "amount_paid": r.amount_gbp or 0,
                "currency": "gbp",
                "status": r.status,
                "description": f"{r.tier.capitalize()} subscription",
            }
            for r in rows
        ]
    }


@router.get("/payments/config")
async def get_provider_config():
    """Public — tells the frontend which provider is active so it can render
    the right messaging. No secrets are returned."""
    return {"provider": settings.PAYMENT_PROVIDER}


@router.post("/payments/cancel", response_model=MessageResponse)
async def cancel_subscription(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    sub_id = escort.psp_subscription_id
    if not sub_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    sub_result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == sub_id)
    )
    existing = sub_result.scalars().first()
    if existing and existing.status == "cancelling":
        raise HTTPException(status_code=400, detail="Your subscription is already scheduled to cancel")

    provider = get_provider()
    try:
        provider.cancel_subscription(sub_id)
    except ProviderApiError as e:
        raise HTTPException(status_code=502, detail=f"Could not cancel: {e}")

    if existing:
        existing.status = "cancelling"
    await db.flush()
    return MessageResponse(message="Subscription will cancel at the end of the current billing period")


@router.post("/payments/cancel-blue-tick", response_model=MessageResponse)
async def cancel_blue_tick(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    sub_id = escort.psp_blue_tick_subscription_id
    if not sub_id:
        raise HTTPException(status_code=400, detail="No active Blue Tick subscription found")
    bt_result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == sub_id)
    )
    existing = bt_result.scalars().first()
    if existing and existing.status == "cancelling":
        raise HTTPException(status_code=400, detail="Your Blue Tick is already scheduled to cancel")

    provider = get_provider()
    try:
        provider.cancel_subscription(sub_id)
    except ProviderApiError as e:
        raise HTTPException(status_code=502, detail=f"Could not cancel Blue Tick: {e}")

    if existing:
        existing.status = "cancelling"
    await db.flush()
    return MessageResponse(message="Blue Tick will cancel at the end of the current billing period")


@router.post("/payments/sync", response_model=MessageResponse)
async def sync_subscription_from_provider(
    escort: Escort = Depends(get_current_verified_escort),
):
    """No-op for Verotel — there's no programmatic 'list customer subscriptions'
    endpoint we can use as a fallback. We rely entirely on webhooks.

    Kept as an endpoint so the frontend success page can call it harmlessly
    if it was wired up under the Stripe era. Returns a friendly message.
    """
    return MessageResponse(message="Sync not required for this provider")


# ─── Webhook ─────────────────────────────────────────────────────────────────

@router.post("/webhooks/verotel")
@router.get("/webhooks/verotel")   # Verotel postbacks are sometimes GET
async def verotel_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    provider = get_provider()
    if provider.name != "verotel":
        raise HTTPException(status_code=503, detail="Verotel is not the active provider")

    try:
        event = provider.verify_and_parse_webhook(
            raw_body=payload,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
        )
    except InvalidWebhookSignatureError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except ProviderApiError as e:
        # Unknown event type — log and 200 so Verotel stops retrying.
        print(f"[verotel webhook] {e}")
        return {"received": True, "ignored": True}

    # Idempotency: dedupe on (subscription_id, event_type, transaction_id).
    # Verotel doesn't have a unique event_id like Stripe, but transaction_id
    # within a subscription is unique per charge.
    dedup_key = f"verotel:{event.subscription_id}:{event.type.value}:{event.transaction_id or ''}"
    dedup_stmt = pg_insert(WebhookEvent).values(
        id=dedup_key,
        event_type=event.type.value,
        received_at=datetime.utcnow(),
    ).on_conflict_do_nothing(index_elements=["id"])
    result = await db.execute(dedup_stmt)
    if result.rowcount == 0:
        return {"received": True, "duplicate": True}

    await _apply_webhook_event(event, db, background_tasks)
    return {"received": True}


async def _apply_webhook_event(event, db: AsyncSession, background_tasks: BackgroundTasks) -> None:
    """Single dispatch point for all canonical event types."""
    if event.type == WebhookEventType.SUBSCRIPTION_CREATED:
        await _handle_subscription_created(event, db, background_tasks)
    elif event.type == WebhookEventType.SUBSCRIPTION_RENEWED:
        await _handle_subscription_renewed(event, db)
    elif event.type == WebhookEventType.SUBSCRIPTION_CANCELLED:
        await _handle_subscription_cancelled(event, db)
    elif event.type == WebhookEventType.SUBSCRIPTION_EXPIRED:
        await _handle_subscription_expired(event, db)
    elif event.type == WebhookEventType.SUBSCRIPTION_REACTIVATED:
        await _handle_subscription_reactivated(event, db)
    elif event.type == WebhookEventType.REFUND_ISSUED:
        await _handle_refund(event, db)
    elif event.type == WebhookEventType.CHARGEBACK:
        await _handle_chargeback(event, db)


async def _find_escort(event, db: AsyncSession) -> Optional[Escort]:
    """Find the escort this event belongs to. Prefer metadata.escort_id, fall
    back to looking up by psp_subscription_id."""
    escort_id = event.metadata.get("escort_id")
    if escort_id:
        result = await db.execute(select(Escort).where(Escort.id == escort_id))
        e = result.scalar_one_or_none()
        if e:
            return e
    if event.subscription_id:
        result = await db.execute(
            select(Escort).where(
                (Escort.psp_subscription_id == event.subscription_id)
                | (Escort.psp_blue_tick_subscription_id == event.subscription_id)
            )
        )
        return result.scalar_one_or_none()
    return None


async def _handle_subscription_created(event, db: AsyncSession, background_tasks: BackgroundTasks):
    escort = await _find_escort(event, db)
    if not escort:
        print(f"[verotel] subscription_created — could not find escort for {event.subscription_id}")
        return

    tier = event.metadata.get("tier") or "essential"
    is_blue_tick = tier == "blue_tick"

    # Replace any older active row of the same kind.
    old_filter = [Subscription.escort_id == escort.id, Subscription.status == "active"]
    if is_blue_tick:
        old_filter.append(Subscription.tier == "blue_tick")
    else:
        old_filter.append(Subscription.tier != "blue_tick")
    old_subs = await db.execute(select(Subscription).where(*old_filter))
    for old in old_subs.scalars():
        old.status = "replaced"

    # Period end: Verotel doesn't tell us this in `initial` postbacks reliably.
    # Approximate based on tier + billing — webhook will overwrite on first rebill.
    billing = event.metadata.get("billing") or "monthly"
    if billing == "annual":
        period_end = datetime.utcnow().replace(month=1, day=1) if datetime.utcnow().month == 12 else datetime.utcnow()
        # Crude — webhook for renewal will correct it.
        period_end = period_end.replace(year=period_end.year + 1)
    else:
        nm = _next_month_first()
        period_end = datetime(nm.year, nm.month, nm.day)

    db.add(Subscription(
        escort_id=escort.id,
        tier=tier,
        status="active",
        psp_provider="verotel",
        psp_subscription_id=event.subscription_id,
        amount_gbp=event.amount_pence,
        current_period_start=datetime.utcnow(),
        current_period_end=period_end,
    ))

    if is_blue_tick:
        escort.psp_blue_tick_subscription_id = event.subscription_id
        # Create a pending verification record so admin reviews the photos.
        existing_v = await db.execute(
            select(Verification).where(
                Verification.escort_id == escort.id,
                Verification.level == 3,
                Verification.status == "pending",
            )
        )
        if not existing_v.scalar_one_or_none():
            db.add(Verification(escort_id=escort.id, level=3, status="pending"))
            background_tasks.add_task(
                send_verification_submitted_to_admin,
                escort_stage_name=escort.stage_name,
                escort_email=escort.email,
                submission_level=3,
            )
    else:
        escort.subscription_tier = tier
        escort.psp_subscription_id = event.subscription_id
        escort.psp_provider = "verotel"
        escort.subscription_expires_at = period_end
        # Auto-grant Blue Tick if already identity-verified on premium/elite.
        if tier in ("premium", "elite") and escort.verification_level >= 2:
            escort.blue_tick_active = True

    await db.flush()


async def _handle_subscription_renewed(event, db: AsyncSession):
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return

    # Recompute next period end based on tier billing cadence in DB.
    nm = _next_month_first()
    sub.current_period_start = datetime.utcnow()
    sub.current_period_end = datetime(nm.year, nm.month, nm.day)

    # If a downgrade was pending, apply it now.
    escort_result = await db.execute(select(Escort).where(Escort.id == sub.escort_id))
    escort = escort_result.scalar_one_or_none()
    if escort and sub.pending_tier:
        new_tier = sub.pending_tier
        escort.subscription_tier = new_tier
        sub.tier = new_tier
        sub.pending_tier = None
        # Photo-limit enforcement
        new_limit = _TIER_PHOTO_LIMITS.get(new_tier, 3)
        from sqlalchemy import func as sqlfunc
        photo_count_res = await db.execute(
            select(sqlfunc.count()).select_from(EscortPhoto).where(EscortPhoto.escort_id == escort.id)
        )
        if (photo_count_res.scalar() or 0) > new_limit:
            escort.is_approved = False
    if escort:
        escort.subscription_expires_at = sub.current_period_end
    await db.flush()


async def _handle_subscription_cancelled(event, db: AsyncSession):
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
    )
    for sub in result.scalars():
        sub.status = "cancelling"
    await db.flush()


async def _handle_subscription_expired(event, db: AsyncSession):
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    escort_result = await db.execute(select(Escort).where(Escort.id == sub.escort_id))
    escort = escort_result.scalar_one_or_none()
    if escort:
        if sub.tier == "blue_tick":
            escort.blue_tick_active = False
            escort.psp_blue_tick_subscription_id = None
            if escort.verification_level >= 3:
                escort.verification_level = 2
        else:
            escort.subscription_tier = "free"
            escort.psp_subscription_id = None
            escort.subscription_expires_at = None
    await db.flush()


async def _handle_subscription_reactivated(event, db: AsyncSession):
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
    )
    for sub in result.scalars():
        if sub.status == "cancelling":
            sub.status = "active"
    await db.flush()


async def _handle_refund(event, db: AsyncSession):
    # Mark the subscription as refunded but DO NOT auto-revoke access — admin
    # will decide whether the user keeps their plan or not (e.g. a partial
    # refund might still leave them subscribed).
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
    )
    for sub in result.scalars():
        # Append a note via the unused field if you have one, otherwise just
        # update status. We use cancelled_at to mark when the refund hit.
        if not sub.cancelled_at:
            sub.cancelled_at = datetime.utcnow()
    await db.flush()


async def _handle_chargeback(event, db: AsyncSession):
    # Chargebacks are serious — instantly revoke access and freeze the escort.
    result = await db.execute(
        select(Subscription).where(Subscription.psp_subscription_id == event.subscription_id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    escort_result = await db.execute(select(Escort).where(Escort.id == sub.escort_id))
    escort = escort_result.scalar_one_or_none()
    if escort:
        escort.subscription_tier = "free"
        escort.psp_subscription_id = None
        escort.subscription_expires_at = None
        escort.is_approved = False  # Hide profile while we investigate
    await db.flush()

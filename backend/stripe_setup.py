"""
Run once to create Stripe products + prices for Bluechips London.
Usage:  python stripe_setup.py
Prints all price IDs to paste into your .env
"""
import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or input("Paste your Stripe secret key (sk_test_…): ").strip()

TIERS = [
    # Monthly plans
    {"name": "Essential",  "nickname": "essential",  "unit_amount": 2499, "env_key": "STRIPE_ESSENTIAL_PRICE_ID",        "interval": "month"},
    {"name": "Premium",    "nickname": "premium",    "unit_amount": 4999, "env_key": "STRIPE_PREMIUM_PRICE_ID",          "interval": "month"},
    {"name": "Elite",      "nickname": "elite",      "unit_amount": 8999, "env_key": "STRIPE_ELITE_PRICE_ID",            "interval": "month"},
    # Annual plans (2 months free = 10 × monthly)
    {"name": "Essential Annual", "nickname": "essential_annual", "unit_amount": 24990, "env_key": "STRIPE_ESSENTIAL_ANNUAL_PRICE_ID", "interval": "year"},
    {"name": "Premium Annual",   "nickname": "premium_annual",   "unit_amount": 49990, "env_key": "STRIPE_PREMIUM_ANNUAL_PRICE_ID",   "interval": "year"},
    {"name": "Elite Annual",     "nickname": "elite_annual",     "unit_amount": 89990, "env_key": "STRIPE_ELITE_ANNUAL_PRICE_ID",     "interval": "year"},
    # Blue Tick add-on
    {"name": "Blue Tick — Setup Fee", "nickname": "blue_tick_setup",    "unit_amount": 1000, "env_key": "STRIPE_BLUE_TICK_SETUP_PRICE_ID",    "interval": None},
    {"name": "Blue Tick — Monthly",   "nickname": "blue_tick_monthly",  "unit_amount": 399,  "env_key": "STRIPE_BLUE_TICK_MONTHLY_PRICE_ID",  "interval": "month"},
]

print("\nCreating Stripe products and prices…\n")

results = {}
for tier in TIERS:
    product = stripe.Product.create(
        name=f"Bluechips London — {tier['name']}",
        metadata={"tier": tier["nickname"]},
    )
    price_params = dict(
        product=product.id,
        unit_amount=tier["unit_amount"],
        currency="gbp",
        nickname=tier["nickname"],
    )
    if tier["interval"]:
        price_params["recurring"] = {"interval": tier["interval"]}

    price = stripe.Price.create(**price_params)
    results[tier["env_key"]] = price.id

    if tier["interval"] == "year":
        label = f"£{tier['unit_amount'] / 100:.2f}/year"
    elif tier["interval"] == "month":
        label = f"£{tier['unit_amount'] / 100:.2f}/month"
    else:
        label = f"£{tier['unit_amount'] / 100:.2f} one-time"

    print(f"  ✓ {tier['name']} ({label}): {price.id}")

print("\n── Add these to your .env ──────────────────────────────")
for key, value in results.items():
    print(f"{key}={value}")
print("────────────────────────────────────────────────────────\n")

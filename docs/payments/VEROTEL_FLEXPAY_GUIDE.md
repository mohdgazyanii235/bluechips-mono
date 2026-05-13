# Verotel FlexPay — Build, Setup & Deploy Runbook

End-to-end checklist for migrating Bluechips London payments from Stripe to Verotel FlexPay.
Branch: `payments/verotel-flexpay`.

> **Sensitive section:** payments processing for adult-vertical merchants. Every step in this
> runbook is procedural. Do NOT shortcut steps — the cost of mistakes (declined cards, lost
> revenue, processor reserves frozen) is significant.

---

## Phase 0 — Apply for a Verotel merchant account

Verotel is the long pole. Backend code is ready to deploy the moment you receive credentials.

### 0.1 Documents to prepare BEFORE applying

Have these as PDFs/scans in one folder:

- [ ] **Business registration**: Companies House certificate (Ltd) or self-employed tax registration
- [ ] **Director / signing officer ID**: passport or driving licence (front + back)
- [ ] **Director proof of address**: utility bill < 3 months old
- [ ] **Business bank account proof**: statement < 3 months, business name on header
- [ ] **Domain ownership proof**: WHOIS lookup screenshot showing your name OR ICANN registration
- [ ] **Website screenshots**: Home page, pricing, terms, privacy, refund policy — all live and visible
- [ ] **Description of business model** (short): "Independent companion advertising directory. Subscription fees only — no transactions between users."
- [ ] **Expected monthly volume** estimate
- [ ] **Average transaction amount** (£18.99 / £49.99 / £89.99 tier examples)
- [ ] **Refund policy** published on your site
- [ ] **Terms and conditions** that explicitly disclaim agency relationship

### 0.2 Apply

1. Go to https://www.verotel.com/en/sign-up.html
2. Choose **FlexPay** (not Cascade Billing — that's an add-on for later)
3. Submit the application with all the documents above
4. Expected timeline: **3–10 business days** for first response, **2–4 weeks** for full approval

### 0.3 During underwriting

Verotel may come back with questions about:
- Whether you handle bookings (answer: no, advertising only)
- Age verification process (answer: ID verification before listing goes live)
- Refund policy specifics
- Affiliate / referral disclosure

**Be honest and detailed.** Hiding things now means a worse rate or a clawback later.

### 0.4 On approval — what you'll receive

Email from Verotel with:
- **Shop ID** (e.g. `12345`)
- **Signature Key** (long random string — keep this *secret*, treat like a password)
- **API username + password** for Control Center programmatic access
- Login link to your Verotel Control Center
- The full merchant integration PDF

---

## Phase 1 — Local development setup

### 1.1 Switch to the Verotel branch

```bash
git fetch origin
git checkout payments/verotel-flexpay
docker compose down
docker compose up -d --build
```

### 1.2 Apply the new migration

```bash
docker compose exec backend alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade a47c3b8de219 -> b8c4f2a91d63, add psp_* columns for provider-agnostic payment tracking
```

### 1.3 Populate `.env` (still in test mode, no real creds needed yet)

Use the new `.env.example` as a template. Critical new section:

```bash
PAYMENT_PROVIDER=verotel
VEROTEL_SHOP_ID=TEST_SHOP                         # any string for now; real value from Verotel later
VEROTEL_SIGNATURE_KEY=test-signature-key-12345    # any string ≥ 16 chars
VEROTEL_API_USERNAME=test-api-user
VEROTEL_API_PASSWORD=test-api-pass
VEROTEL_TEST_MODE=true
```

Restart backend so it picks up env vars:

```bash
docker compose restart backend
```

### 1.4 Smoke test

```bash
# 1. Health check
curl http://localhost:8000/api/health
# expect: {"status":"ok",...}

# 2. Provider check
curl http://localhost:8000/api/payments/config
# expect: {"provider":"verotel"}

# 3. Run the Verotel unit tests
docker compose exec backend python -m pytest tests/unit/services/test_verotel_provider.py --noconftest --no-cov -v
# expect: 27 passed
```

If all three pass, your local app is wired correctly. You can't actually complete a checkout
until you have real Verotel credentials, but the URL-construction and signature logic is verified.

---

## Phase 2 — Connect to your Verotel sandbox (after approval)

### 2.1 Log into Verotel Control Center

URL: https://controlcenter.verotel.com

Note: Verotel's interface looks dated. Don't be alarmed — the underlying processing is mature.

### 2.2 Configure your Shop / Website

1. **Websites → Add Website** (if not already done during application)
   - URL: `https://bluechips.live`
   - Description: "Independent companion advertising directory"
   - Site verified by Verotel team — usually within 24h

2. **Website settings → Subscription products**
   - Don't create individual price-locked products. Our app sends `priceAmount`
     dynamically via `price_data`-equivalent flow. Verify your shop is configured
     to accept dynamic pricing (this is the default for FlexPay).

3. **Website settings → Postback URL**
   - Set to: `https://api.bluechips.live/api/webhooks/verotel`
   - Method: POST
   - Confirm "Send postbacks for all events" is enabled

4. **Website settings → Success / Cancel URLs**
   - Success: `https://bluechips.live/dashboard/verify?payment=success`
   - Cancel: `https://bluechips.live/dashboard/subscription?payment=cancelled`
   - (Our app overrides these per checkout anyway, but set them as fallbacks)

5. **API access → Generate credentials**
   - Note the username + password
   - Restrict to `Cancel Subscription` permission only (defence in depth)

### 2.3 Test mode credentials

In **Control Center → Websites → Test Mode**:
- Toggle test mode ON
- Verotel provides test card PANs in their merchant docs — **use only these for sandbox**
- Test transactions don't process real funds and don't count toward reserves

### 2.4 Update local `.env` with real test credentials

```bash
VEROTEL_SHOP_ID=12345                              # from Control Center
VEROTEL_SIGNATURE_KEY=<actual-signature-key>       # from Control Center
VEROTEL_API_USERNAME=<actual-api-user>
VEROTEL_API_PASSWORD=<actual-api-pass>
VEROTEL_TEST_MODE=true                             # stays true until you go live
```

Restart backend: `docker compose restart backend`

---

## Phase 3 — Verify VEROTEL_VERIFY markers against the merchant docs

The code contains `# VEROTEL_VERIFY:` comments where the public spec is ambiguous.
Cross-check each one against your received merchant PDF:

```bash
grep -rn "VEROTEL_VERIFY" backend/app/
```

Expected matches (and what to verify):
- `verotel.py:LIVE_CHECKOUT_BASE` — exact live + test host URLs
- `verotel.py:event_map` — exact event name strings in postbacks
- `verotel.py:create_subscription_checkout` — param names (`subscriptionPriceAmount`
  vs `recurringPriceAmount`), `trialAmount`/`trialPeriod` route
- `verotel.py:_sign` — confirm separator (`:` vs `|`) and whether values are URL-encoded
- `verotel.py:cancel_subscription` — exact endpoint path

If anything differs from the docs, fix the file and re-run unit tests.

---

## Phase 4 — Local end-to-end test against Verotel sandbox

This is the only way to find integration bugs before production.

### 4.1 Expose your local webhook to Verotel

Verotel postbacks can't reach `localhost:8000`. You need a tunnel:

```bash
# Install ngrok if you haven't already
npm install -g ngrok
# OR: choco install ngrok  (Windows)

# In one terminal:
ngrok http 8000
```

Copy the `https://xxx.ngrok-free.app` URL. In Verotel Control Center → Website settings,
**temporarily** change the postback URL to:
```
https://xxx.ngrok-free.app/api/webhooks/verotel
```

### 4.2 Walk through each test in `docs/testing/verotel-flexpay-test-plan.xlsx`

Open the Excel file. Work through the **34 High priority** tests one by one. For each:

1. Read pre-conditions
2. Perform the test steps in your local environment
3. Validate against the "What to Check" column
4. Mark Pass/Fail in the Status column

**Critical tests that MUST pass before production:**
- PR-01 to PR-03 — Provider wiring
- CK-01 to CK-06 — Checkout URL construction
- HC-01 to HC-04 — Hosted checkout flow with test card
- WH-01 to WH-13 — Webhook handling (especially signature verification)
- SL-01 to SL-04 — Cancel / upgrade flows
- DC-01 to DC-03 — Discount + founding member integration
- PD-01 to PD-04 — Production readiness checklist

### 4.3 Common test failures and fixes

| Failure | Cause | Fix |
|---|---|---|
| Webhook signature mismatch | Separator char in `_sign()` doesn't match Verotel's | Edit `verotel.py:_sign` — try `\|` or `+` |
| Checkout URL rejected by Verotel | param name spelt differently | Cross-ref merchant doc, edit `create_subscription_checkout` params dict |
| Cancel endpoint 404 | API path differs | Check `cancel_subscription` URL against API guide |
| Test cards don't work | Wrong sandbox host | Update `LIVE_CHECKOUT_BASE` / `TEST_CHECKOUT_BASE` |

After each fix, re-run unit tests: `python -m pytest tests/unit/services/test_verotel_provider.py --noconftest --no-cov`

---

## Phase 5 — Deploy to production

Only proceed when all High priority tests pass in local sandbox.

### 5.1 Prepare production `.env`

On the production server (`ip-172-31-29-36`):

```bash
ssh admin@ip-172-31-29-36
cd ~/bluechips-mono/backend

# Backup current .env
cp .env .env.backup-$(date +%F)

# Edit
nano .env
```

Add the Verotel block (replace test-mode values with **live** credentials from Verotel
Control Center once they flip your shop to live mode):

```bash
PAYMENT_PROVIDER=verotel
VEROTEL_SHOP_ID=<LIVE_SHOP_ID>
VEROTEL_SIGNATURE_KEY=<LIVE_SIGNATURE_KEY>
VEROTEL_API_USERNAME=<LIVE_API_USER>
VEROTEL_API_PASSWORD=<LIVE_API_PASS>
VEROTEL_TEST_MODE=false                          # IMPORTANT — false in prod
VEROTEL_WEBHOOK_PATH=/api/webhooks/verotel
```

You can remove the old `STRIPE_*` env vars from prod `.env` — they're no longer used.

### 5.2 Deploy the code

```bash
cd ~/bluechips-mono
git fetch origin
git checkout payments/verotel-flexpay
git pull origin payments/verotel-flexpay
```

### 5.3 Run the migration

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Verify:
```bash
docker compose -f docker-compose.prod.yml exec db psql -U bluechips -d bluechips_london \
  -c "SELECT version_num FROM alembic_version;"
# Expect: b8c4f2a91d63
```

### 5.4 Rebuild and restart backend

```bash
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

### 5.5 Smoke test live

```bash
curl https://api.bluechips.live/api/health
curl https://api.bluechips.live/api/payments/config
# expect: {"provider":"verotel"}
```

### 5.6 Verify Verotel postback URL is set to PROD

In Verotel Control Center → Website settings → Postback URL:
```
https://api.bluechips.live/api/webhooks/verotel
```

(Make sure you reverted any ngrok URL you used during testing.)

### 5.7 Make one real test purchase

Use a **real card with a small purchase** (Essential monthly is the cheapest tier).
This is the only way to verify live cards process end-to-end.

After the purchase:
1. Confirm Verotel Control Center shows the sale
2. Confirm postback hit your prod logs:
   `docker compose -f docker-compose.prod.yml logs --tail=50 backend | grep verotel`
3. Confirm DB row created:
   ```sql
   SELECT escort_id, tier, status, psp_subscription_id, current_period_end
   FROM subscriptions ORDER BY created_at DESC LIMIT 1;
   ```
4. Confirm the escort's UI shows the new tier
5. **Cancel and refund the test purchase** via Verotel Control Center

### 5.8 Frontend deploy

Frontend changes (`paymentsApi`, removed `reactivate*` calls, etc.) need a fresh build:

```bash
cd frontend
git pull
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## Phase 6 — Migrate existing Stripe subscribers (if any)

If you have live Stripe subscriptions when Stripe pulls the plug, those customers will
stop being billed automatically. Two options:

### Option A — Email and have them resubscribe (recommended for low volume)

```
Subject: Important: Payment processor change

Hi {stage_name},

We've moved to a new payment processor that better serves our industry.
Your current subscription will end at the next billing date.

To continue without interruption, please re-subscribe before {date}:
https://bluechips.live/dashboard/subscription

Your founding-member status and lifetime discount carry over automatically.
```

### Option B — Build a migration tool

Not recommended unless you have >100 active paying customers. The complexity
(Verotel needs each customer to enter card details fresh — there's no card-on-file
migration between processors) doesn't pay off for small volumes.

---

## Phase 7 — Monitor post-launch

For the first week after going live:

- [ ] Check `webhook_events` table daily — count by `event_type`
- [ ] Watch backend logs for `[verotel webhook]` warnings:
  ```bash
  docker compose -f docker-compose.prod.yml logs backend | grep -i verotel
  ```
- [ ] Check Verotel Control Center daily for declined transactions, chargebacks
- [ ] Compare expected MRR (from DB) to Verotel's reported MRR — should match within rounding

If a postback signature ever fails in prod, **don't ignore it**. Could indicate:
- Verotel rotated their signature key (rare)
- A tampered request from a hostile actor
- Our `_sign()` logic has drifted from theirs

---

## Rollback plan

If something breaks in production after deploy:

```bash
# 1. Stop accepting new checkouts (admin emergency)
ssh admin@ip-172-31-29-36
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.config import settings
settings.PAYMENT_PROVIDER = ''   # disables all new checkouts gracefully
"
# This isn't persistent. For persistence, edit .env and restart.

# 2. To fully revert to a clean state:
git checkout main
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
# But note: Stripe code on main no longer accepts new subscriptions either
# (we already removed it). You'd need to revert further.

# 3. To force-cancel a runaway integration in Verotel:
# Log into Verotel Control Center → API access → revoke the API key.
# All cancel_subscription calls will start failing with 401, surfacing the bug.
```

---

## Reference — files changed in this branch

```
backend/app/services/payment_provider/          (new — entire package)
backend/app/routers/payments.py                  (replaced)
backend/app/main.py                              (Stripe-config init removed)
backend/app/config.py                            (Stripe vars → Verotel vars)
backend/app/models/escort.py                     (added psp_* columns)
backend/app/models/subscription.py               (added psp_* columns)
backend/alembic/versions/b8c4f2a91d63_*.py       (new migration)
backend/requirements.txt                         (removed stripe pkg)
backend/stripe_setup.py                          (deleted)
backend/.env.example                             (new)
backend/tests/unit/services/test_verotel_provider.py (new — 27 tests)
frontend/src/api/payments.ts                     (Stripe references removed)
frontend/src/pages/dashboard/SubscriptionPage.tsx (upgrade flow redirects to checkout)
frontend/src/pages/dashboard/MySubscriptionsPage.tsx (reactivate now informational)
frontend/src/pages/dashboard/VerifyPage.tsx      (sync method renamed)
docs/testing/generate_verotel_test_plan.py       (new)
docs/testing/verotel-flexpay-test-plan.xlsx      (new — 47 tests)
docs/payments/VEROTEL_FLEXPAY_GUIDE.md           (this file)
```

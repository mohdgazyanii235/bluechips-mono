# Bluechips London — Complete Project Reference

## Project Overview

**Bluechips London** is a premium adult companion advertising directory for London. It operates as a technology platform intermediary — similar in legal model to Gumtree or Fiverr — where self-employed adult entertainers pay to list their profiles and clients browse them. We are not an escort agency, do not employ companions, do not handle payments between clients and companions, and are not a party to any arrangement made through the platform.

**Live domain:** bluechips.live
**Admin email:** mohdgazyanii235@gmail.com
**Business model:** SaaS subscription fees from companions (not commission from bookings)

---

## Technology Stack

### Backend
- **FastAPI** 0.115.5 (async Python)
- **SQLAlchemy** 2.0 (async mode with `asyncpg`)
- **Alembic** for database migrations
- **PostgreSQL** 14+ (via Docker)
- **Redis** (session/caching, currently underutilised)
- **Stripe SDK** v11 for payments
- **Pillow** for image processing/thumbnails
- **boto3** for AWS S3 / Cloudflare R2 file storage
- **aiosmtplib** for sending email
- **bcrypt** for password hashing
- **python-jose** for JWT tokens
- **Pydantic v2** for request/response validation

### Frontend
- **React** 18 + **TypeScript**
- **Vite** as the build tool
- **React Router** v6
- **TanStack Query** (React Query) for data fetching + caching
- **Zustand** for auth state (persisted in localStorage)
- **Framer Motion** for animations
- **Tailwind CSS** for styling (dark luxury theme: gold/ivory on near-black)
- **React Hook Form** + **Zod** for form validation
- **react-helmet-async** for SEO meta tags

### Infrastructure
- **Docker Compose** for local development
  - `backend` (FastAPI + uvicorn)
  - `db` (PostgreSQL)
  - `redis` (Redis)
- Environment variables read from `backend/.env`

---

## Directory Structure

```
BluechipsLondon/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, lifespan
│   │   ├── config.py                # Settings (pydantic-settings, reads .env)
│   │   ├── database.py              # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── escort.py            # Escort, EscortPhoto, EscortService
│   │   │   ├── admin.py             # Admin user model
│   │   │   ├── verification.py      # Verification submissions
│   │   │   ├── subscription.py      # Stripe subscription records
│   │   │   ├── boost.py             # Profile boost model (future)
│   │   │   └── borough.py           # London boroughs
│   │   ├── routers/
│   │   │   ├── auth.py              # Register, login, verify-email
│   │   │   ├── escorts.py           # Public escort listing + my-profile CRUD
│   │   │   ├── payments.py          # Stripe checkout, webhooks, invoices
│   │   │   ├── upload.py            # Photo upload/delete
│   │   │   ├── verification.py      # Document upload for identity/blue tick
│   │   │   ├── admin.py             # Admin auth + verification review + escort management
│   │   │   ├── boroughs.py          # Borough list
│   │   │   └── deps.py              # Auth dependencies (get_current_escort, get_current_admin)
│   │   ├── schemas/
│   │   │   ├── escort.py            # Pydantic v2 request/response models
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── email_service.py     # SMTP email functions
│   │   │   └── storage_service.py   # S3/R2/local file storage
│   │   └── utils/
│   │       ├── security.py          # JWT, bcrypt, token generation
│   │       ├── slugify.py           # URL-safe slug generation
│   │       └── rate_limit.py        # In-memory rate limiter (per-IP)
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial_schema.py
│   │       ├── 5252eaf02a13_add_whatsapp_phone_bluetick_fields.py
│   │       └── a3f1c8e29d74_add_profile_type_token_expiry_couples.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                         # NEVER commit — see Environment Variables section
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Route definitions
│   │   ├── main.tsx
│   │   ├── api/
│   │   │   ├── escorts.ts           # escortsApi (list, profile, contactClick)
│   │   │   ├── payments.ts          # paymentsApi (checkout, upgrade, invoices, cancel)
│   │   │   ├── admin.ts             # adminApi (login, verifications, escorts)
│   │   │   └── client.ts            # Axios instance with auth interceptor
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Layout.tsx       # Main layout + DashboardLayout
│   │   │   │   ├── Navbar.tsx       # Auth-aware nav; shows "Join Us" only when logged out
│   │   │   │   └── Footer.tsx       # Legal disclaimer footer
│   │   │   ├── escort/
│   │   │   │   ├── EscortCard.tsx   # Grid card (photo, name, badges, rate)
│   │   │   │   ├── EscortGrid.tsx   # Grid + skeleton loading
│   │   │   │   ├── VerificationBadge.tsx
│   │   │   │   └── ServiceTags.tsx
│   │   │   ├── search/
│   │   │   │   └── FilterPanel.tsx  # Filters: borough, ethnicity, rate, couples toggle, etc.
│   │   │   ├── age-gate/
│   │   │   │   └── AgeGate.tsx      # 18+ confirmation (localStorage persisted)
│   │   │   └── ui/                  # Button, Badge, Input, Select, Spinner, etc.
│   │   ├── hooks/
│   │   │   ├── useEscorts.ts        # useEscorts, useEscortProfile, useMyProfile, etc.
│   │   │   └── useBoroughs.ts
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SearchPage.tsx       # /escorts with FilterPanel
│   │   │   ├── EscortProfilePage.tsx # /escorts/:slug — profile + direct contact buttons
│   │   │   ├── AboutPage.tsx        # Legal/about page
│   │   │   ├── SafetyPage.tsx
│   │   │   ├── JoinPage.tsx         # Marketing + pricing for companions
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   └── VerifyEmailPage.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardPage.tsx         # Stats, alerts, upsell, quick actions
│   │   │   │   ├── EditProfilePage.tsx        # Profile form
│   │   │   │   ├── PhotosPage.tsx             # Photo upload/manage
│   │   │   │   ├── SubscriptionPage.tsx       # Monthly/annual plan selection + Blue Tick
│   │   │   │   ├── MySubscriptionsPage.tsx    # Active plans, invoices, cancellation flow
│   │   │   │   └── VerifyPage.tsx             # Identity/blue tick verification status
│   │   │   └── admin/
│   │   │       ├── AdminLoginPage.tsx
│   │   │       ├── AdminLayout.tsx
│   │   │       ├── AdminDashboardPage.tsx
│   │   │       ├── AdminVerificationsPage.tsx
│   │   │       ├── AdminVerificationDetailPage.tsx
│   │   │       └── AdminEscortsPage.tsx
│   │   ├── store/
│   │   │   ├── authStore.ts         # Zustand: escort JWT + profile info
│   │   │   └── adminStore.ts        # Zustand: admin JWT
│   │   └── types/
│   │       └── escort.ts            # TypeScript interfaces + constants
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── stripe_setup.py                  # One-time Stripe product/price creation script
└── CLAUDE.md                        # This file
```

---

## Database Models

### Escort (escorts table)
Core user model. One escort per account.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | String(255) UNIQUE | Lowercased on write |
| hashed_password | String(255) | bcrypt |
| stage_name | String(100) | Display name |
| slug | String(120) UNIQUE | URL-safe, auto-generated from stage_name |
| age | Integer | 18–99 validated |
| nationality | String(80) | |
| ethnicity | String(80) | |
| height_cm | Integer | |
| build | String(20) | slim/athletic/curvy/petite/bbw |
| hair_colour | String(50) | |
| eye_colour | String(50) | |
| dress_size | String(20) | |
| chest | String(30) | |
| borough_id | UUID FK → boroughs.id | |
| availability_type | String(10) | incall/outcall/both |
| profile_type | String(20) | individual/couple (default: individual) |
| rate_30min | Integer | GBP pence? No — stored as £ integer |
| rate_1hour | Integer | GBP |
| rate_2hours | Integer | GBP |
| rate_overnight | Integer | GBP |
| about_me | String(600) | Max 600 chars |
| languages | ARRAY(String) | e.g. ["English", "French"] |
| booking_notice | String(100) | e.g. "1 hour notice" |
| std_tested | Boolean | default False |
| std_tested_date | String(20) | e.g. "Jan 2026" |
| whatsapp_number | String(30) | Shown directly on public profile |
| phone_number | String(30) | Shown directly on public profile |
| verification_level | Integer | 0=none, 1=email, 2=identity, 3=blue_tick |
| is_email_verified | Boolean | |
| email_verification_token | String(255) | Cleared after use |
| email_verification_token_expires_at | DateTime | 24h expiry |
| is_active | Boolean | Admin can deactivate |
| is_approved | Boolean | Admin can remove from search |
| available_now | Boolean | Manual toggle |
| profile_complete | Boolean | age+borough+about_me+availability all set |
| subscription_tier | String(20) | free/essential/premium/elite |
| subscription_expires_at | DateTime | |
| stripe_customer_id | String(100) | Stripe customer ID |
| stripe_subscription_id | String(100) | Main subscription |
| blue_tick_active | Boolean | True only after admin approval |
| blue_tick_stripe_subscription_id | String(100) | Blue Tick subscription |
| profile_views | Integer | Incremented on profile page load |
| contact_clicks | Integer | Incremented on WhatsApp/Call/Text clicks |
| created_at | DateTime | |
| updated_at | DateTime | onupdate |
| last_seen_at | DateTime | |

**Computed properties:**
- `primary_photo_url` — first photo marked is_primary, or first photo, or None
- `photo_limit` — 3 (free) / 8 (essential) / 50 (premium+elite)

### EscortPhoto (escort_photos table)
| Column | Type |
|--------|------|
| id | UUID PK |
| escort_id | UUID FK → escorts.id CASCADE |
| url | String(500) |
| thumbnail_url | String(500) |
| is_primary | Boolean |
| sort_order | Integer |
| created_at | DateTime |

### EscortService (escort_services table)
Tag-per-row for services. Allowed tags defined in `escorts.py:ALLOWED_SERVICE_TAGS`.

### Borough (boroughs table)
London boroughs with SEO fields and `escort_count`.

### Verification (verifications table)
| Column | Type |
|--------|------|
| id | UUID PK |
| escort_id | UUID FK |
| level | Integer | 2=identity, 3=blue_tick |
| status | String(20) | pending/approved/rejected |
| id_document_url | String(500) | S3 key or local path |
| selfie_url | String(500) | |
| match_selfie_url | String(500) | Blue Tick only |
| admin_notes | Text | Rejection reason |
| reviewed_by | String(100) | Admin email |
| submitted_at | DateTime | |
| reviewed_at | DateTime | |
| stripe_payment_intent_id | String(100) | For refunds |
| stripe_charge_id | String(100) | |
| refunded_at | DateTime | |
| refund_id | String(100) | Stripe refund ID |

### Subscription (subscriptions table)
Tracks each Stripe subscription event.

### Admin (admins table)
| Column | Type |
|--------|------|
| id | UUID PK |
| email | String(255) UNIQUE |
| hashed_password | String(255) |
| is_active | Boolean |
| created_at | DateTime |

---

## API Endpoints

All routes prefixed with `/api`.

### Authentication (`/api/auth`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | — | Register escort (rate-limited: 5/hr/IP) |
| POST | `/login` | — | Login (rate-limited: 10/10min/IP+email) |
| POST | `/verify-email?token=...` | — | Verify email token (24h expiry) |
| POST | `/change-password` | escort JWT | Change password |

### Escorts (`/api/escorts`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/escorts` | — | Paginated list with filters |
| GET | `/escorts/me` | escort JWT | Dashboard profile (includes private fields) |
| PUT | `/escorts/me` | escort JWT | Update profile |
| PATCH | `/escorts/me/available-now` | escort JWT | Toggle available now |
| GET | `/escorts/:slug` | — | Public profile (increments view count) |
| POST | `/escorts/:slug/contact-click` | — | Record contact button click |

**Search filters (GET /escorts):** `borough_slug`, `ethnicity`, `availability_type`, `profile_type` (individual/couple), `min_age`, `max_age`, `min_rate`, `max_rate`, `std_tested`, `available_now`, `blue_tick_only`, `service_tag`, `page`, `per_page`

**Sort order:** elite → premium → essential → free, then verification_level desc, then available_now desc, then updated_at desc

### Payments (`/api/payments`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/payments/checkout` | escort JWT (verified) | Create Stripe Checkout session |
| POST | `/payments/upgrade-tier` | escort JWT (verified) | Modify existing subscription in-place |
| POST | `/payments/blue-tick-checkout` | escort JWT (verified) | Blue Tick checkout (setup £10 + £3.99/mo) |
| GET | `/payments/subscription` | escort JWT (verified) | Current subscription details |
| GET | `/payments/invoices` | escort JWT (verified) | Stripe invoice history |
| GET | `/payments/config` | — | Stripe publishable key |
| POST | `/payments/cancel` | escort JWT (verified) | Set cancel_at_period_end |
| POST | `/payments/cancel-blue-tick` | escort JWT (verified) | Cancel Blue Tick |
| POST | `/webhooks/stripe` | Stripe signature | Webhook handler |

**Webhook events handled:**
- `checkout.session.completed` → creates Subscription record, updates escort tier/blue_tick
- `customer.subscription.updated` → updates Subscription status, period_end
- `customer.subscription.deleted` → marks subscription cancelled, resets tier

**IMPORTANT:** Webhook validates that `session.customer` matches `escort.stripe_customer_id` to prevent forged metadata attacks.

### Upload (`/api/upload`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/upload/photo` | escort JWT (verified) | Upload photo (validated: content-type + magic bytes) |
| DELETE | `/upload/photo/:id` | escort JWT (verified) | Delete photo |
| PATCH | `/upload/photo/:id/set-primary` | escort JWT (verified) | Set primary photo |

### Verification (`/api/verification`)
Document submission for identity (level 2) and blue tick (level 3).

### Admin (`/api/admin`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/login` | — | Admin login (rate-limited: 5/15min/IP) |
| GET | `/admin/stats` | admin JWT | Platform stats |
| GET | `/admin/verifications/pending` | admin JWT | Pending verifications list |
| GET | `/admin/verifications/:id` | admin JWT | Detail with signed document URLs |
| POST | `/admin/verifications/:id/approve` | admin JWT | Approve → update escort.verification_level |
| POST | `/admin/verifications/:id/reject` | admin JWT | Reject → Stripe refund + sub cancel + email |
| GET | `/admin/escorts` | admin JWT | List all escorts |
| PATCH | `/admin/escorts/:id/toggle-active` | admin JWT | Activate/deactivate escort |

---

## Subscription Plans

| Tier | Monthly | Annual | Photo limit |
|------|---------|--------|-------------|
| Free | £0 | — | 3 |
| Essential | £24.99/mo | £249.90/yr | 8 |
| Premium | £49.99/mo | £499.90/yr | 50 |
| Elite | £89.99/mo | £899.90/yr | 50 |
| Blue Tick | £10 setup + £3.99/mo | — | (add-on) |

Annual = 10× monthly (equivalent to 2 months free).

Stripe price IDs stored in `.env` and `config.py`. Run `stripe_setup.py` once to create products/prices.

---

## Authentication Flows

### Escort Authentication
1. Register → bcrypt password hash stored → email verification token generated (24h expiry)
2. Email verification → `is_email_verified = True`, `verification_level = 1`
3. Login → JWT access token (default 60 min expiry, configurable)
4. Token sent as `Authorization: Bearer <token>` header
5. Decoded in `deps.py:get_current_escort`

### Admin Authentication
1. Admin account auto-created on startup from `ADMIN_EMAIL` env var
2. Password auto-generated if `ADMIN_INITIAL_PASSWORD` not set (printed to console once)
3. Login via `POST /api/admin/login` → JWT token
4. Admin tokens decoded by `deps.py:get_current_admin`
5. Frontend stores admin token in Zustand `adminStore` (localStorage)

---

## Payment & Verification Flows

### Standard Subscription
```
Escort clicks Subscribe → POST /payments/checkout → Stripe Checkout URL
  → User pays → Stripe fires checkout.session.completed webhook
  → _handle_checkout_completed:
      - Verifies escort.stripe_customer_id matches session.customer (SECURITY)
      - Creates/replaces Subscription record
      - Updates escort.subscription_tier
      - Sets escort.stripe_subscription_id
```

### Upgrading Plan (existing subscriber)
```
POST /payments/upgrade-tier → modifies existing Stripe subscription in-place
  → proration_behavior: "always_invoke" → Stripe charges/credits difference immediately
  → Updates DB immediately (webhook also fires to confirm)
```

### Blue Tick
```
Escort pays Blue Tick → POST /payments/blue-tick-checkout
  → Stripe checkout with two line_items: setup fee (one-time) + monthly recurring
  → checkout.session.completed → sets escort.blue_tick_stripe_subscription_id
  → Creates Verification(level=3, status="pending") record
  → Sends email to admin via BackgroundTasks
  → Admin reviews in /admin/verifications
  → On approve: escort.blue_tick_active = True, escort.verification_level = 3
  → On reject: Stripe refund + subscription cancel + escort.blue_tick_active = False + email
```

### Identity Verification (level 2)
Handled via `verification.py` router — escort uploads ID document + selfie.

---

## Security Measures

- **Rate limiting:** Login 10/10min, admin login 5/15min, registration 5/hr (in-memory, per-IP)
- **JWT validation:** `SECRET_KEY` must not be the dev default in production (startup check)
- **File upload:** Content-type header + magic byte validation (JPEG/PNG/WebP)
- **Stripe webhook:** Signature verification via `STRIPE_WEBHOOK_SECRET` + customer ID cross-check
- **Security headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS (production only)
- **API docs:** Disabled in production (`APP_ENV=production` → docs_url=None)
- **Phone validation:** Regex-validated on input (international format)
- **Email token expiry:** 24 hours from registration

---

## Environment Variables

All in `backend/.env`:

```bash
# App
APP_NAME=Bluechips London
APP_ENV=development           # production for live
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://bluechips:bluechips_secret@db:5432/bluechips_london

# Redis
REDIS_URL=redis://redis:6379/0

# Security — CHANGE SECRET_KEY IN PRODUCTION
SECRET_KEY=insecure-dev-key-change-in-production   # REQUIRED: random 64-char string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ESSENTIAL_PRICE_ID=price_...          # £24.99/mo
STRIPE_PREMIUM_PRICE_ID=price_...            # £49.99/mo
STRIPE_ELITE_PRICE_ID=price_...              # £89.99/mo
STRIPE_ESSENTIAL_ANNUAL_PRICE_ID=price_...   # £249.90/yr
STRIPE_PREMIUM_ANNUAL_PRICE_ID=price_...     # £499.90/yr
STRIPE_ELITE_ANNUAL_PRICE_ID=price_...       # £899.90/yr
STRIPE_BLUE_TICK_SETUP_PRICE_ID=price_...    # £10 one-time
STRIPE_BLUE_TICK_MONTHLY_PRICE_ID=price_...  # £3.99/mo

# Email (SMTP)
EMAIL_FROM=noreply@bluechips.live
EMAIL_FROM_NAME=Bluechips London
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password

# Admin
ADMIN_EMAIL=mohdgazyanii235@gmail.com
ADMIN_INITIAL_PASSWORD=           # Leave blank to auto-generate on first boot

# AWS S3 / Cloudflare R2
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=auto
S3_BUCKET_NAME=bluechips-media
S3_ENDPOINT_URL=                  # R2: https://<account-id>.r2.cloudflarestorage.com
S3_PUBLIC_URL=                    # CDN/public URL for served files
```

---

## Development Setup

```bash
# Start all services
docker compose up -d

# Run migrations
docker compose exec backend alembic upgrade head

# Set up Stripe products/prices (run once, outside Docker)
cd backend
pip install stripe python-dotenv
python stripe_setup.py

# Frontend dev server
cd frontend
npm install
npm run dev
```

**IMPORTANT:** After changing `.env`, restart with `docker compose up -d backend` (not `restart`) to re-read env_file.

---

## Known Fixes & History

### WhatsApp/contact not showing on profiles (FIXED)
`_build_profile` in `escorts.py` was not including `whatsapp_number`/`phone_number` when constructing `EscortProfileOut`. Fixed by adding both fields explicitly.

### Blue Tick "Apply" button showing for subscribed users (FIXED)
`GET /escorts/me` was hand-constructing `EscortDashboardOut` and omitting fields including `blue_tick_stripe_subscription_id`. Fixed by using `model_validate()` pattern that iterates `model_fields`.

### Stripe tier upgrade double-charging (FIXED)
Was creating a new Stripe subscription instead of modifying existing. Fixed via `POST /payments/upgrade-tier` which calls `subscriptions.update()` in-place.

### Blue Tick checkout setup fee error (FIXED)
Stripe newer API removed `subscription_data.add_invoice_items`. Fixed by putting setup fee in `line_items` alongside recurring price.

### `asyncio.create_task()` for emails (FIXED)
Changed to `BackgroundTasks.add_task()` in webhook handler to ensure reliable execution.

### Migration NOT NULL error (FIXED)
`blue_tick_active` added without `server_default`. Fixed by adding `server_default=sa.text('false')`.

---

## Key Business Rules

1. **Free tier** escorts: basic listing, 3 photos, no contact buttons visible to clients (WhatsApp shown only for paid tiers — NOTE: currently all tiers show contact buttons if numbers are set)
2. **Paid tiers** (Essential/Premium/Elite): more photos, priority placement, contact buttons
3. **Blue Tick** requires: active paid subscription + identity verification (level 2) first
4. **Blue Tick** is admin-approved after payment — creates a Verification(level=3) record, admin reviews and approves/rejects
5. **Identity verification (level 2)** requires: active paid subscription + document upload
6. On **verification rejection**: Stripe refund + subscription cancelled + email sent
7. Escorts can toggle **Available Now** freely from dashboard
8. **Profile visibility**: `is_active=True AND is_approved=True AND is_email_verified=True`
9. **Search ordering**: elite > premium > essential > free, then verification_level desc, then available_now desc, then updated_at desc
10. **Couples**: profile_type='couple' — filterable separately; shown with 💑 Couple badge

---

## Frontend State Management

### authStore (Zustand, persisted)
```typescript
{ isAuthenticated, token, escort_id, stage_name, subscription_tier, verification_level, profile_complete }
```
Set on login/register, cleared on logout.

### adminStore (Zustand, persisted)
```typescript
{ isAuthenticated, token, email }
```
Set on admin login, cleared on admin logout.

### React Query caches
- `my-profile` — `GET /escorts/me`
- `subscription` — `GET /payments/subscription`
- `invoices` — `GET /payments/invoices`
- `escorts` — `GET /escorts` (paginated, by filters)
- `escort/:slug` — `GET /escorts/:slug`
- `boroughs` — `GET /boroughs`

---

## Legal & Compliance

Bluechips London operates as a **technology platform intermediary** in the UK, analogous to Gumtree or Fiverr. Key legal basis:

- Escort advertising is **fully legal** in England, Scotland, and Wales
- We are **not an escort agency** under the Sexual Offences Act 2003
- We comply with **UK Online Safety Act 2023** — we have content reporting mechanisms
- We comply with **UK GDPR / Data Protection Act 2018** — personal data handling
- We comply with **ASA advertising regulations** — no misleading claims

**Companion self-certification:** All companions certify they are 18+ on registration. Paid subscribers undergo ID + age verification by our admin team before Blue Tick is issued.

**Platform liability:** As a platform intermediary, Bluechips London is not liable for the accuracy of listings or conduct of individuals listed. All arrangements are private, direct, and voluntary between clients and companions.

---

## Deployment Notes

- Set `APP_ENV=production` in `.env`
- Set a strong random `SECRET_KEY` (startup will reject the dev default)
- Set `ALLOWED_ORIGINS` to your production domain only
- Configure SMTP for emails (Gmail App Password recommended for low volume)
- Configure Stripe live keys and webhook signing secret
- Set up Cloudflare R2 or AWS S3 for media storage
- API docs auto-disabled in production (`/api/docs`, `/api/redoc` return 404)
- HTTPS enforced via HSTS header once behind reverse proxy

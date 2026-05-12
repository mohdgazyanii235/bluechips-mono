---
name: Security-critical paths
description: Endpoints and code paths that must always be covered by security tests
type: project
---

These paths have history of subtle bugs and must always have negative-path security tests:

1. `POST /api/webhooks/stripe` - signature verification, idempotency via `WebhookEvent.id`, customer-id cross-check inside `_handle_checkout_completed` / `_handle_subscription_updated` / `_handle_subscription_deleted`.
2. `POST /api/auth/verify-email` - 24h token expiry, single-use, no SQL injection in `?token=`.
3. `POST /api/admin/login` and `POST /api/auth/login` - rate-limited (5/15min admin, 10/10min escort). Must NOT leak whether an email exists.
4. `POST /api/upload/photo` - magic-byte validation (not just content-type), per-tier photo limit, requires `is_email_verified`.
5. `GET /private/{key}` - HMAC signed URL with path-traversal defence (resolve and ensure stays under uploads root).
6. Admin endpoints under `/api/admin/*` - all gated by `get_current_admin`; escort JWT must NOT authenticate as admin and vice-versa (both decoded with same SECRET_KEY but `sub` is looked up in different tables).

**Why:** A recent security fix (commit f7c4613) addressed C1/C2/C3/H1 in these areas. Tests guard against regressions.

**How to apply:** When you touch ANY of these files - `routers/payments.py`, `routers/auth.py`, `routers/upload.py`, `routers/admin.py`, `services/storage_service.py` - re-run the matching security suite and add a case for the new branch.

---
name: Mocking conventions
description: How to mock external services (Stripe, S3, SMTP) safely
type: feedback
---

Always mock external network calls; never let tests hit real APIs.

**Why:** The Stripe live key is real money; SMTP credentials are limited; S3/R2 quota matters. CI environments don't have access regardless.

**How to apply:**
- Stripe: patch `stripe.StripeClient`, `stripe.Webhook.construct_event`, `stripe.Subscription.retrieve`, `stripe.Customer.create_balance_transaction`, `stripe.Refund.create`, `stripe.Invoice.list`, `stripe.Subscription.delete`. Stripe accesses fields via `obj["field"]` and `obj.get("field")` - prefer `MagicMock()` with `__getitem__` configured OR plain dicts depending on the call site. Build a `mock_stripe` fixture that yields a namespace of all common patches.
- S3/storage: in tests force `settings.use_s3 = False` (or just leave AWS creds blank) so the local-filesystem code-path runs; point `LOCAL_UPLOADS_DIR` at `tmp_path`. For pure-unit tests, patch `app.services.storage_service.upload_image` / `upload_document` / `delete_file` to return canned values.
- SMTP: `email_service.send_email` short-circuits when `SMTP_USER` is empty - rely on that in tests (it just prints to stdout and returns True). For tests that assert "an email was sent", patch the specific high-level helper (e.g. `send_verification_email`) instead of `aiosmtplib`.

When generating image bytes for upload tests use PIL in-memory:
```python
from PIL import Image
import io
def make_jpeg_bytes(size=(100,100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=(255,0,0)).save(buf, format="JPEG")
    return buf.getvalue()
```

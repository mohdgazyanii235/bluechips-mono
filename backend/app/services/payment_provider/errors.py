class PaymentProviderError(Exception):
    """Base for all payment provider failures."""


class ProviderNotConfiguredError(PaymentProviderError):
    """Raised when PAYMENT_PROVIDER env / required secrets are missing."""


class ProviderApiError(PaymentProviderError):
    """The provider returned an error to a server-to-server API call."""
    def __init__(self, message: str, *, status_code: int | None = None, raw: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw = raw


class InvalidWebhookSignatureError(PaymentProviderError):
    """Webhook payload failed signature validation. Reject the request."""

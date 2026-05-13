"""
Payment provider abstraction.

The rest of the app must NOT import Verotel (or any other provider) directly.
Always go through `get_provider()` so we can swap providers via env config.
"""
from functools import lru_cache
from app.config import settings
from app.services.payment_provider.base import PaymentProvider
from app.services.payment_provider.errors import (
    PaymentProviderError, ProviderNotConfiguredError, ProviderApiError,
    InvalidWebhookSignatureError,
)


@lru_cache(maxsize=1)
def get_provider() -> PaymentProvider:
    name = (settings.PAYMENT_PROVIDER or "").lower().strip()
    if name == "verotel":
        from app.services.payment_provider.verotel import VerotelFlexPayProvider
        return VerotelFlexPayProvider()
    raise ProviderNotConfiguredError(
        f"PAYMENT_PROVIDER must be set to a supported provider. Got: {name!r}"
    )


__all__ = [
    "get_provider",
    "PaymentProvider",
    "PaymentProviderError",
    "ProviderNotConfiguredError",
    "ProviderApiError",
    "InvalidWebhookSignatureError",
]

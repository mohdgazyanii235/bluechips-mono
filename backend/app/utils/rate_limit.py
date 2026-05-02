"""Simple in-memory rate limiter.

Tracks request timestamps per identifier (e.g. IP + endpoint).
For multi-process deployments, swap the deque store for a Redis-backed implementation.
"""
import time
from collections import defaultdict, deque
from typing import Deque

_store: dict[str, Deque[float]] = defaultdict(deque)


def is_rate_limited(
    identifier: str,
    max_attempts: int = 5,
    window_seconds: int = 300,
) -> bool:
    """Return True if the identifier has exceeded the rate limit."""
    now = time.time()
    dq = _store[identifier]
    while dq and dq[0] < now - window_seconds:
        dq.popleft()
    if len(dq) >= max_attempts:
        return True
    dq.append(now)
    return False

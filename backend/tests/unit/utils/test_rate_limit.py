"""Unit tests for the in-memory rate limiter.

The limiter uses a sliding window over per-identifier deques. Critical
properties to verify:
- The (N+1)-th request inside the window is blocked.
- Old timestamps outside the window are evicted, freeing capacity.
- Different identifiers are independent.
- Edge: max_attempts=1 blocks the second request immediately.
"""
from __future__ import annotations

import time

import pytest

from app.utils.rate_limit import is_rate_limited, _store


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


def test_first_n_attempts_allowed():
    for i in range(5):
        assert is_rate_limited("ip-1", max_attempts=5, window_seconds=60) is False, f"attempt {i+1} should pass"


def test_attempt_over_limit_blocked():
    for _ in range(5):
        is_rate_limited("ip-2", max_attempts=5, window_seconds=60)
    assert is_rate_limited("ip-2", max_attempts=5, window_seconds=60) is True


def test_identifiers_are_independent():
    for _ in range(5):
        is_rate_limited("ip-A", max_attempts=5, window_seconds=60)
    # ip-B is fresh - first attempt must pass
    assert is_rate_limited("ip-B", max_attempts=5, window_seconds=60) is False


def test_window_expiry_evicts_old_timestamps(monkeypatch):
    """Manipulate time to confirm old entries are evicted."""
    base = 1_000_000.0
    times = iter([
        base, base + 1, base + 2,           # three calls in quick succession
        base + 65, base + 66, base + 67, base + 68,  # past 60s window
    ])

    def fake_time():
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)

    # Within window - 3 of 3 allowed
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    # After window slides, the old three are evicted; new attempts succeed.
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is False
    # 4th in new window blocks
    assert is_rate_limited("ip-evict", max_attempts=3, window_seconds=60) is True


def test_max_attempts_one_blocks_second():
    assert is_rate_limited("ip-tight", max_attempts=1, window_seconds=60) is False
    assert is_rate_limited("ip-tight", max_attempts=1, window_seconds=60) is True

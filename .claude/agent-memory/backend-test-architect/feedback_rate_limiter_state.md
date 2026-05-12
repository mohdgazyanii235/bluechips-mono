---
name: Rate limiter is module-level state
description: The in-memory rate limiter persists across tests; must be reset
type: feedback
---

`app.utils.rate_limit._store` is a module-level `defaultdict(deque)`. State persists across tests in the same process.

**Why:** Without an autouse fixture clearing it, the second test that hits `/api/auth/register` or `/api/auth/login` from the same client IP will already be counted from prior tests and may hit the 429.

**How to apply:** Add this in `conftest.py`:
```python
@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.utils.rate_limit import _store
    _store.clear()
    yield
    _store.clear()
```

Test the rate limiter behaviour explicitly in `tests/unit/utils/test_rate_limit.py` (sliding window, eviction, identifier isolation).

---
name: Test architecture
description: How tests are wired up in this repo - framework, DB, fixtures
type: project
---

Backend tests live in `backend/tests/` with the following layout:

- `conftest.py` - root fixtures (app, async client, DB session, escort/admin factories, stripe mocks)
- `unit/` - utilities, schemas, services
- `api/` - per-router endpoint tests
- `integration/` - cross-router flows (register -> verify -> login, checkout -> webhook -> subscription)
- `security/` - auth/authz, file validation, webhook signature, SQL/XSS attempts
- `fixtures/` - reusable model factories

**Why:** The harness pipeline runs `pytest -x` so file order and conftest scope matter. Per-test transaction rollback is implemented by overriding `app.dependency_overrides[get_db]` to yield a transactional session that rolls back at teardown.

**How to apply:** When adding a new router or model, mirror its tests under both `api/` (HTTP-level) and either `unit/` or `integration/` for logic-level. Always reset the in-memory rate-limiter store in an autouse fixture.

Stack:
- pytest 7.4.0, pytest-asyncio 0.21.0 (asyncio_mode=auto)
- httpx.AsyncClient with ASGITransport for FastAPI
- aiosqlite for in-memory async tests OR a dedicated `bluechips_test` Postgres database (the seed migration uses ARRAY and JSONB so Postgres is preferred for full fidelity)
- pytest-cov target: 95% minimum, 100% goal

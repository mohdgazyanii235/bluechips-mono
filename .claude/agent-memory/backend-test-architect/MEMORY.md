# Backend Test Architect — Memory Index

- [Project test architecture](project_test_architecture.md) — Stack, structure, and runtime conventions for Bluechips London backend tests
- [Security-critical paths](project_security_paths.md) — Paths that must always be covered by security tests
- [Mocking conventions](feedback_mocking_conventions.md) — How to mock Stripe, S3, SMTP without hitting the network
- [In-memory rate limiter quirk](feedback_rate_limiter_state.md) — `_store` is module-level; tests must reset it between runs

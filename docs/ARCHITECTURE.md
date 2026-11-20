# Architecture

Browser UI (HTML/CSS/JavaScript) -> FastAPI REST API -> SQLite database.
Authentication: PBKDF2 password hashing and HMAC-signed expiring bearer token.
Core workflows: identity, vehicle CRUD, rule-based tyre screening, CSV preview and maintenance work orders.

For production: replace local SQLite with PostgreSQL; move secrets to managed secret storage; add HTTPS, rate limits, audit trail, refresh-token/session revocation, role policy enforcement, backups, monitoring and automated security tests. Add model-serving endpoints only after data governance and independent model validation.

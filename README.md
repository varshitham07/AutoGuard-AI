# AutoGuard AI

**Vehicle fleet management, tyre telemetry screening and maintenance tracking.**

AutoGuard AI is a working software MVP with a browser interface and a FastAPI backend. When run locally, the interface sends requests to the backend, which stores accounts, vehicles and maintenance work orders in SQLite.

## Choose how to run it

### Public preview (GitHub Pages)

Open: https://varshitham07.github.io/AutoGuard-AI/

GitHub Pages only hosts static files. This public preview therefore uses browser-local demo storage; its accounts and records are not shared across browsers or devices. It is not the full multi-user backend deployment.

### Full working application (Windows)

1. Install Python 3.10 or newer.
2. Download this repository from GitHub (Code → Download ZIP) and extract it.
3. Double-click `START_AUTOGUARD_WINDOWS.bat`.
4. Wait for the server to start and open `http://127.0.0.1:8000`.
5. Create an account and use the fleet, tyre screening and maintenance modules.

The local website connects to the FastAPI backend and stores accounts, vehicles, work orders and tyre screening history in the local SQLite database file. Keep the server terminal open while using the website. The interface displays whether it is running in backend mode or browser-preview mode.

Manual setup:
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

API health check: `http://127.0.0.1:8000/api/health`
Interactive API documentation: `http://127.0.0.1:8000/docs`

## Working capabilities

- Account registration and login with PBKDF2 password hashing and signed expiring bearer tokens.
- Fleet vehicle create, list and delete.
- Tyre telemetry screening using transparent, configurable demonstration rules, with saved per-account screening history.
- CSV upload, parsing checks and preview.
- Maintenance work-order creation and status tracking.
- Dashboard summary and recent maintenance activity.

## Important model and safety disclosures

- **EngineGuard is not yet a trained engine-failure predictor.** The interface describes a future modelling workflow; no engine failure risk score or validated model accuracy is currently produced.
- **TyreGuard is rule-based, not machine learning.** It flags readings against supplied manufacturer pressure limits and demonstration temperature indicators. These thresholds are not universal safety limits.
- **Tyre image inspection is preview-only.** No computer-vision classifier is currently connected.
- CSV upload checks file structure and previews rows. It does not train a model or infer failure labels.
- This is a software demonstration and decision-support MVP, not a substitute for professional vehicle inspection or OEM guidance.

## API routes

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/vehicles`
- `POST /api/tyres/screen`, `GET /api/tyres/history`
- `POST /api/data/preview`
- `GET/POST/PATCH /api/work-orders`
- `GET /api/dashboard/summary`

## Automated checks

GitHub Actions runs the API test suite on pushes and pull requests to `main`. The tests cover health, account registration, vehicle/work-order flow, tyre screening history, invalid OEM pressure ranges and account-level vehicle isolation.

Run the same checks locally with:
```bash
pip install -r requirements-dev.txt
pytest -q
```

## Before real-world deployment

The current backend uses local SQLite and a demonstration default signing secret. A public multi-user deployment needs a managed database, a unique secret stored outside source control, HTTPS, rate limiting, backups, audit logging, account/session controls and security testing. Do not expose the current default configuration to production traffic.

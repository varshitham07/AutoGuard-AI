# AutoGuard AI

**Explainable vehicle-health screening and maintenance intelligence — company demonstration MVP.**

AutoGuard AI brings fleet records, tyre telemetry screening, maintenance actions and diagnostic workflows into one web application.

## Deploy a public demo (Render)

1. Open [Render](https://render.com/) and sign in.
2. Choose **New → Blueprint**.
3. Connect the GitHub repository `varshitham07/AutoGuard-AI`.
4. Select the `main` branch. Render should detect the root-level `render.yaml`.
5. Review the service settings and choose **Apply** / **Deploy**.
6. When the service is live, open the generated `https://...onrender.com` URL. Add `/api/health` to the URL to confirm the backend health check returns `status: ok`.

The free service may sleep when idle, and its local filesystem is ephemeral. SQLite demo data can be lost after a restart or redeploy. Use managed PostgreSQL and persistent operational controls for continued use.

## Run locally on Windows

1. Install Python 3.10 or newer.
2. Double-click `START_AUTOGUARD_WINDOWS.bat`.
3. Wait for dependencies to install; the browser opens at `http://127.0.0.1:8000`.
4. Register an account. The first registered account is assigned the administrator role for the demonstration.

Manual setup:
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

For tests, install `requirements-dev.txt` and run `pytest`.

## Working capabilities

- Account registration and login (PBKDF2 password hashing; signed expiring bearer tokens).
- Fleet vehicle create/list/delete.
- Tyre telemetry screening using transparent demonstration rules.
- CSV upload, parsing checks and preview.
- Maintenance work-order creation and status tracking.
- Dashboard summary and recent activity.

## Model and safety disclosures

- **EngineGuard is an integration-ready track, not a trained failure predictor in this package.** A valid SCANIA Component X dataset, schema inspection, leakage-safe target definition, training and independent evaluation are required before publishing model scores or component-risk predictions.
- **TyreGuard sensor screening is rule-based**, not a trained model. It flags values for review; it cannot guarantee detection or prediction of sudden tyre blowouts. Thresholds must be configured for the specific tyre, vehicle, load and manufacturer.
- **Tyre image inspection is an upload/preview workflow only**, not a computer-vision classifier. Do not describe an uploaded image as AI-diagnosed.
- CSV analysis reports the structure and sample rows of an uploaded file. It does not turn unlabelled data into ground-truth failure predictions.
- This MVP is a demonstration and decision-support prototype, not a substitute for driver judgement, professional inspection or OEM guidance.

## API

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/vehicles`
- `POST /api/tyres/screen`
- `POST /api/data/preview`
- `GET/POST/PATCH /api/work-orders`
- `GET /api/dashboard/summary`
- Interactive API docs: `/docs`; health: `/api/health`.

## Production hardening still required

Use HTTPS, managed PostgreSQL, secret management, rate limiting, audit logging, backups, session/token revocation, role-policy review, security testing and manufacturer-approved thresholds before real deployment. The current authentication and local SQLite setup are for a controlled demonstration only.

## Suggested company walkthrough

1. Register and show the fleet dashboard.
2. Add a vehicle.
3. Open TyreGuard and screen a sample telemetry record; explain the evidence and limitations.
4. Upload a CSV to Data Lab and show its schema/preview.
5. Create a maintenance work order from a finding.
6. Show EngineGuard as the SCANIA dataset/model integration track, explicitly noting that model validation is pending.

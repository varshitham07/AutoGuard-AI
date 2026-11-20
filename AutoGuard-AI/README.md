# AutoGuard AI
**Explainable vehicle-health screening and maintenance intelligence — company demonstration MVP**

AutoGuard AI brings fleet records, tyre telemetry screening, maintenance actions and diagnostic workflows into one local web application.

## Public deployment (Render)
This repository includes `render.yaml` for a one-service deployment. Push the project to a GitHub repository, sign in to Render, choose **New → Blueprint**, connect that repository, and deploy the `render.yaml` blueprint. Render will build the Python service and provide its public HTTPS URL. The free service uses an ephemeral filesystem: local SQLite data may be lost on restart/redeploy, so use managed PostgreSQL or persistent storage for ongoing use.

## Run on Windows
1. Install Python 3.10+.
2. Double-click `START_AUTOGUARD_WINDOWS.bat`.
3. Wait for dependencies to install; the browser opens at `http://127.0.0.1:8000`.
4. Register a user account. The first registered account is an administrator.

Or run manually:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Working capabilities
- Local account registration and login (PBKDF2 password hashing; signed bearer tokens).
- Fleet vehicle create/list/delete.
- Tyre telemetry screening using transparent, configurable demonstration rules.
- CSV upload and basic schema/summary validation.
- Maintenance work-order creation and tracking.
- Dashboard summary and recent activity.

## Important model and safety disclosures
- **EngineGuard is an integration-ready module, not a trained failure predictor in this package.** A valid SCANIA Component X dataset, schema inspection, leakage-safe target definition, training and independent evaluation are required before publishing model scores or component-risk predictions.
- **TyreGuard sensor screening is rule-based**, not a trained model. It flags values/trends for review; it cannot guarantee detection or prediction of sudden tyre blowouts. Thresholds must be configured for the specific tyre, vehicle, load and manufacturer.
- **Tyre image inspection is an interface/workflow placeholder**, not a computer-vision classifier. Do not describe an uploaded image as AI-diagnosed.
- CSV analysis reports what is present in the uploaded file; it does not turn unlabelled data into ground-truth failure predictions.
- This MVP is for demonstration and decision support, not a substitute for driver judgement, professional inspection or OEM guidance.

## API
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/vehicles`
- `POST /api/tyres/screen`
- `POST /api/data/preview`
- `GET/POST/PATCH /api/work-orders`
- `GET /api/dashboard/summary`
- Interactive API docs: `/docs`

## Production hardening still required
Use HTTPS, managed PostgreSQL, secret management, rate limiting, audit logging, backups, role policy review, security testing and manufacturer-approved thresholds before real deployment. Local SQLite and local token storage are for a controlled demonstration only.

## Suggested company walkthrough
1. Register and show the fleet dashboard.
2. Add a vehicle.
3. Open TyreGuard and screen a sample telemetry record; explain the evidence and limitations.
4. Upload a CSV to Data Lab and show schema/quality feedback.
5. Create a maintenance work order from the finding.
6. Show EngineGuard as the SCANIA dataset/model integration track, explicitly noting that model validation is pending.

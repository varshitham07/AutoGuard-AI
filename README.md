# AutoGuard AI

**Vehicle fleet management, tyre telemetry screening and maintenance tracking.**

AutoGuard AI is a working software MVP with a browser interface and a FastAPI backend. When run locally, the interface sends requests to the backend, which stores accounts, vehicles and maintenance work orders in SQLite.

## Choose how to run it

### Public preview (GitHub Pages)

Open: https://varshitham07.github.io/AutoGuard-AI/

GitHub Pages only hosts static files. The preview supports a browser-local demonstration flow for fleet vehicles, tyre screening, work orders, service history, reports, alerts and basic built-in assistant guidance. Its demo account and records stay in that browser only, are not secure multi-user authentication and are not shared across browsers or devices. Generative AI and the trained Scania model require the local FastAPI backend.

### Full working application (Windows)

1. Install Python 3.10 or newer.
2. Download this repository from GitHub (Code → Download ZIP) and extract it.
3. Double-click `START_AUTOGUARD_WINDOWS.bat`.
4. Wait for the server to start and open `http://127.0.0.1:8000`.
5. Create an account and use the fleet, tyre screening and maintenance modules.

The local website connects to the FastAPI backend and stores accounts, vehicles, work orders, tyre screening history and service records in the local SQLite database file. Keep the server terminal open while using the website. The Windows launcher creates and keeps a local signing secret in `.autoguard_secret` so saved browser sessions remain valid between restarts. The interface displays whether it is running in backend mode or browser-preview mode.

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

- AI Mechanic assistant endpoint and chat interface. In local mode it can explain a limited set of common symptoms and retrieve the signed-in owner's saved work orders, service records and tyre checks. The GitHub Pages preview uses a separate limited browser-local guidance fallback. For full generative conversations, configure an optional OpenAI API key on the backend; see [AI assistant setup](docs/AI_ASSISTANT.md).

- Account registration and login with PBKDF2 password hashing and signed expiring bearer tokens.
- Fleet vehicle create, list and delete.
- Tyre telemetry screening using transparent, configurable demonstration rules, with saved per-account screening history.
- CSV upload, parsing checks and preview.
- Maintenance work-order creation and status tracking.
- Service history with parts/labour cost totals, next-service date and odometer reminders, and account-scoped records.
- Monotonic odometer updates to support mileage-based service reminders.
- Dashboard summary and recent maintenance activity.
- Printable vehicle health reports combining the selected vehicle profile, service records, recorded costs, tyre screening history and work orders; use the browser print dialog to save as PDF.
- Alerts and reminders centre that surfaces due service entries, tyre screening flags and high/critical unfinished work orders from saved records.
- Fleet Insights & Cost Analytics with vehicle filtering, monthly recorded service spend, service-type breakdown, vehicle-wise cost comparison, work-order status and CSV export.

## Important model and safety disclosures

- **EngineGuard supports a reproducible Scania APS model workflow.** Train it locally using the official dataset and `docs/MODEL_TRAINING.md`. The repository does not include the large raw dataset or a pre-trained model, so predictions remain unavailable until you download the data and train the model.
- **TyreGuard is rule-based, not machine learning.** It flags readings against supplied manufacturer pressure limits and demonstration temperature indicators. These thresholds are not universal safety limits.
- **Tyre image inspection is preview-only.** No computer-vision classifier is currently connected.
- CSV upload checks file structure and previews rows. It does not train a model. The EngineGuard prediction upload uses the trained Scania model only after the training step is completed.
- This is a software demonstration and decision-support MVP, not a substitute for professional vehicle inspection or OEM guidance.

## Machine-learning setup\n\nRun `DOWNLOAD_SCANIA_DATA_WINDOWS.bat` to download the official UCI data, then run `TRAIN_AUTOGUARD_MODEL_WINDOWS.bat` to install ML dependencies and train. You can also install `requirements-ml.txt` and run `python train_model.py` manually. See [docs/MODEL_TRAINING.md](docs/MODEL_TRAINING.md) for the complete steps and limitations.\n\n## API routes

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/vehicles`; `PATCH /api/vehicles/{vehicle_id}/odometer`
- `GET/POST /api/service-records`
- `POST /api/tyres/screen`, `GET /api/tyres/history`\n- `GET /api/model/status`, `POST /api/model/predict`, `GET /api/model/history`
- `POST /api/assistant/chat` (owner-scoped vehicle and maintenance context)
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

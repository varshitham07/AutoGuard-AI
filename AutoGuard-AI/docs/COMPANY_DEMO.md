# AutoGuard AI — 5-minute company walkthrough

## Opening
AutoGuard AI is a vehicle-health and maintenance intelligence prototype. It combines a fleet asset register, evidence-linked tyre telemetry screening, dataset intake and maintenance action tracking in one workflow.

## Demonstration sequence
1. Register a workspace account. Explain that the first local account is provisioned as administrator for the demo.
2. Register one vehicle in Fleet Management.
3. Open TyreGuard Sensors. Enter a tyre position, pressure, temperature and speed. If known, enter the vehicle/tyre manufacturer's specified pressure range. Run screening and show the flags and recommended follow-up.
4. Open Data Lab and upload a UTF-8 CSV. Show the detected columns, row count and sample rows.
5. Create a work order and change its status to In progress or Completed.
6. Open EngineGuard and explain the dataset-to-model validation plan.

## Technical explanation
- FastAPI exposes authenticated REST endpoints.
- SQLite persists accounts, vehicles and work orders locally.
- Passwords are stored as PBKDF2-HMAC-SHA256 hashes with unique salts.
- Tyre screening is transparent rule-based logic; the response includes evidence, flags, recommendations and a disclaimer.
- CSV intake performs file-size, encoding and parsing checks.

## What is not claimed
There is no trained EngineGuard failure model, no trained tyre-image classifier, and no measured model accuracy in this MVP. Those are subsequent research and validation tasks. Do not claim the tyre screening predicts sudden blowouts or that the prototype is production-certified.

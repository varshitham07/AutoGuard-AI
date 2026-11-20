# Company demo walkthrough

## What the MVP demonstrates

1. Create an operator account and sign in.
2. Register a fleet vehicle and review the fleet list.
3. Enter tyre pressure, temperature and speed with manufacturer limits; review the rule-based evidence.
4. Convert a tyre warning into a maintenance work order.
5. Update work-order status and review the dashboard.
6. Open EngineGuard to see the Scania APS dataset scope and model readiness.
7. After completing the separate model-training steps, upload a CSV with the official 170 Scania sensor feature headers to run real model inference.

## Be accurate when presenting

- Fleet, account, work-order and tyre screening features are functional in the local FastAPI + SQLite application.
- TyreGuard uses transparent screening rules; it is not a tyre-failure ML model.
- EngineGuard uses the official Scania APS failure dataset workflow. A trained model is not included in the repository by default. Download the official dataset and run `python train_model.py` before demonstrating predictions.
- Scania APS predictions are specific to the heavy-truck Air Pressure System dataset, not passenger-car engine diagnostics.
- GitHub Pages is a static preview. Use the local Windows startup script for the backend-backed demo.
- Do not present sample values or untrained model outputs as real predictive results.

## Model preparation

Follow [MODEL_TRAINING.md](MODEL_TRAINING.md). The training script creates validation metrics from the downloaded dataset and writes a local model artifact that is intentionally excluded from Git.

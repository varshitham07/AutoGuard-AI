@echo off
setlocal
title Train AutoGuard AI - Scania APS Model
cd /d "%~dp0"
if not exist data\raw\aps_failure_training_set.csv (
  echo Dataset missing.
  echo Download the official APS Failure at Scania Trucks archive from:
  echo https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks
  echo Extract aps_failure_training_set.csv into data\raw\
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-ml.txt
python train_model.py
echo.
echo If training succeeded, restart AutoGuard AI to load the model.
pause

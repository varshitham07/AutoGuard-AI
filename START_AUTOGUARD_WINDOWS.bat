@echo off
setlocal
title AutoGuard AI
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. Install Python 3.10 or newer.
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not defined APP_SECRET (
  for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_urlsafe(48))"') do set "APP_SECRET=%%i"
)
if not defined DATABASE_PATH set "DATABASE_PATH=%CD%\autoguard.db"
echo.
echo Starting AutoGuard AI at http://127.0.0.1:8000
start "" http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause

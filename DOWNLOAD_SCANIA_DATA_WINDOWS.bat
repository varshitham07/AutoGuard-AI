@echo off
setlocal
title Download official Scania APS dataset
cd /d "%~dp0"
if not exist data\raw mkdir data\raw
set "ZIP=%CD%\data\raw\aps_dataset.zip"
set "URL=https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip"
echo Downloading the official UCI Scania APS dataset (about 54 MB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP%'"
if errorlevel 1 (
  echo Download failed. Open the official UCI page manually:
  echo https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks
  pause
  exit /b 1
)
echo Extracting archive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%CD%\data\raw\extracted' -Force"
if errorlevel 1 (
  echo Extraction failed.
  pause
  exit /b 1
)
for /r "%CD%\data\raw\extracted" %%F in (aps_failure_training_set.csv) do copy /y "%%F" "%CD%\data\raw\aps_failure_training_set.csv" >nul
if not exist data\raw\aps_failure_training_set.csv (
  echo Could not locate aps_failure_training_set.csv in the archive.
  pause
  exit /b 1
)
del "%ZIP%"
echo Dataset ready at data\raw\aps_failure_training_set.csv
echo Next: double-click TRAIN_AUTOGUARD_MODEL_WINDOWS.bat
pause

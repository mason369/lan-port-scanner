@echo off
title LAN Port Scanner

python --version >/dev/null 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python 3.7+
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

python -c "import tabulate" >/dev/null 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Starting LAN Port Scanner...
python app.py

if errorlevel 1 pause

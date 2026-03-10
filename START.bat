@echo off
title LAN Port Scanner

echo Checking Python...
python --version >/dev/null 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found
python --version
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
    echo.
)

echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment activation script not found
    pause
    exit /b 1
)
echo.

echo Checking dependencies...
python -c "import PyQt6" >/dev/null 2>&1
if errorlevel 1 (
    echo Installing PyQt6 and dependencies...
    echo This may take 1-2 minutes, please wait...
    echo.
    python -m pip install --upgrade pip >/dev/null
    pip install PyQt6 tabulate
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        echo Try manually:
        echo   pip install PyQt6 tabulate
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
    echo.
)

echo Starting LAN Port Scanner (Qt6)...
echo.
python app_qt.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo.
    echo Troubleshooting:
    echo 1. Make sure PyQt6 is installed: pip install PyQt6
    echo 2. Try: python app_qt.py
    echo 3. Check error messages above
    pause
)

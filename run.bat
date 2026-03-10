@echo off
chcp 65001 >/dev/null 2>&1
title LAN Port Scanner - Auto Install

echo.
echo ========================================
echo   LAN Port Scanner v1.0
echo   Auto Install and Start
echo ========================================
echo.

REM Check Python installation
python --version >/dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] Python not detected
    echo.
    echo Please install Python 3.7 or higher
    echo Download: https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python detected
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] First run, creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        echo Please ensure Python is fully installed with venv module
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
) else (
    echo [OK] Virtual environment exists
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Check if dependencies are installed
python -c "import tabulate" >/dev/null 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        echo.
        echo Possible causes:
        echo 1. Network connection issues
        echo 2. Outdated pip version
        echo 3. Insufficient permissions
        echo.
        echo Solutions:
        echo 1. Check network connection
        echo 2. Run: python -m pip install --upgrade pip
        echo 3. Run this script as administrator
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Dependencies already installed
    echo.
)

REM Start application
echo ========================================
echo   Starting GUI...
echo ========================================
echo.
python app.py

REM Check exit status
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Application error
    echo ========================================
    echo.
    echo Possible causes:
    echo 1. Missing dependencies
    echo 2. Incompatible Python version
    echo 3. GUI environment issues
    echo.
    echo Solutions:
    echo 1. Delete venv folder and run again
    echo 2. Ensure Python 3.7+
    echo 3. Try CLI mode: python cli.py --help
    echo.
    pause
)

REM Keep window open on error
if errorlevel 1 pause

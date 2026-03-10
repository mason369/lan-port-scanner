@echo off
title LAN Port Scanner

echo Installing dependencies...
pip install PyQt6 tabulate

echo.
echo Starting application...
python app_qt.py

pause

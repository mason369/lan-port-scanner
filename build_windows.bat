@echo off
title Build Windows Executable

echo ========================================
echo   Building Windows Executable
echo ========================================
echo.

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --name="LAN-Port-Scanner" --onefile --windowed --add-data "scanner.py;." app_qt.py

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Executable location: dist\LAN-Port-Scanner.exe
echo.

pause

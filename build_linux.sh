#!/bin/bash

echo "========================================"
echo "  Building Linux Executable"
echo "========================================"
echo ""

echo "Installing PyInstaller..."
pip install pyinstaller

echo ""
echo "Building executable..."
pyinstaller --name="lan-port-scanner" --onefile --add-data "scanner.py:." app_qt.py

echo ""
echo "========================================"
echo "Build complete!"
echo "========================================"
echo ""
echo "Executable location: dist/lan-port-scanner"
echo ""
echo "To run: ./dist/lan-port-scanner"
echo ""

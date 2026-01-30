#!/bin/bash
# script/build.sh - Build standalone binary using PyInstaller

# Exit on error
set -e

# Ensure dependencies are installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

echo "Building Cap2Obs..."

# Create binary
# --onefile: Create a single executable file
# --name: Name of the output binary
# --clean: Clean cache before building
pyinstaller --clean --onefile --name cap2obs cap2obs/__main__.py

echo ""
echo "Build successful!"
echo "Binary location: dist/cap2obs"
echo "You can move this to your bin path: sudo cp dist/cap2obs /usr/local/bin/"

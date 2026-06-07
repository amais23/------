#!/bin/bash
set -e

echo "Building chess_engine.so..."

# Check if running inside docker or locally
if [ -f "/opt/python/cp310-cp310/bin/python" ]; then
    echo "Running inside Docker container..."
    /opt/python/cp310-cp310/bin/python setup.py build_ext --inplace
else
    echo "Running locally..."
    python3 setup.py build_ext --inplace
fi

# Clean build directory
rm -rf build

echo "Build successful! Library created:"
ls -lh chess_engine*.so || ls -lh chess_engine*.pyd

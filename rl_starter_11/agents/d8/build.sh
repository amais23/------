#!/bin/bash
set -e

echo "Building chess_engine_d8_han.so..."

# Check if running inside docker or locally
if [ -f "/opt/python/cp310-cp310/bin/python" ]; then
    echo "Running inside Docker container..."
    gcc -c src/weights.S -o src/weights.o
    /opt/python/cp310-cp310/bin/python setup.py build_ext --inplace
else
    echo "Running locally..."
    clang -arch arm64 -arch x86_64 -c src/weights.S -o src/weights.o
    if [ -f "../../../.venv/bin/python3" ]; then
        ../../../.venv/bin/python3 setup.py build_ext --inplace
    elif [ -f "../../../.venv/bin/python" ]; then
        ../../../.venv/bin/python setup.py build_ext --inplace
    else
        python3 setup.py build_ext --inplace
    fi
fi

# Clean build directory
rm -rf build

echo "Build successful! Library created:"
ls -lh chess_engine_d8_han*.so || ls -lh chess_engine_d8_han*.pyd

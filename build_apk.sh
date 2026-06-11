#!/bin/bash
# StudyMate APK Build Script
# Run on Ubuntu/Debian or WSL
set -e

echo "=== StudyMate APK Builder ==="

# Install dependencies
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev

pip install --upgrade pip buildozer cython

# Build APK
cd "$(dirname "$0")"
buildozer android debug

echo "=== Build complete! ==="
echo "APK located in: $(pwd)/bin/"

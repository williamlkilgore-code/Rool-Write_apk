#!/bin/bash
# Build script for PRNG Dice Android APK
# This script builds the APK using buildozer

set -e

echo "================================================"
echo "PRNG Dice Game - Android APK Build Script"
echo "================================================"

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is required but not installed."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command python3
check_command pip

# Install/update buildozer if needed
echo "Installing/updating buildozer..."
pip install --upgrade buildozer cython

# Install required system dependencies (for Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        build-essential \
        git \
        python3 \
        python3-dev \
        ffmpeg \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libportmidi-dev \
        libswscale-dev \
        libavformat-dev \
        libavcodec-dev \
        zlib1g-dev \
        libgstreamer1.0 \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        libgstreamer-plugins-bad1.0-dev \
        autoconf \
        automake \
        libtool \
        pkg-config \
        openjdk-17-jdk \
        unzip \
        zip
fi

# Navigate to project directory
cd "$(dirname "$0")"

echo "Building Android APK (debug)..."
buildozer android debug

echo "================================================"
echo "Build complete!"
echo "APK location: ./bin/"
echo "================================================"

# List the built APK
if [ -d "bin" ]; then
    echo "Built APK files:"
    ls -la bin/*.apk 2>/dev/null || echo "No APK files found in bin/"
fi

# Dockerfile for building PRNG Dice Android APK
# Based on official Python image with Android SDK tools

FROM python:3.11-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    openjdk-17-jdk \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    autoconf \
    automake \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libltdl-dev \
    patch \
    zip \
    lbzip2 \
    && rm -rf /var/lib/apt/lists/*

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install buildozer and kivy
RUN pip install --upgrade pip setuptools wheel
RUN pip install buildozer kivy cython 'sh>=1.10,<2.0'

# Create app directory
WORKDIR /app

# Copy source code
COPY . /app/

# Accept Android SDK licenses
RUN mkdir -p /root/.buildozer/android/platform/android-sdk/licenses && \
    echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > /root/.buildozer/android/platform/android-sdk/licenses/android-sdk-license

# Build the APK
CMD ["buildozer", "android", "debug"]

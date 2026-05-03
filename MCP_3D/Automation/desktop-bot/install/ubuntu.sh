#!/bin/bash

# Ubuntu Environment Setup Script for Desktop Automation Bot

# Exit on any error
set -e

# Ensure script is run with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo: sudo bash $0"
   exit 1
fi

# Update package lists
echo "Updating package lists..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-dev \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    scrot \
    wget \
    git \
    xvfb \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0

# Check if desktop environment is available for additional GUI libraries
if [ "$XDG_CURRENT_DESKTOP" != "" ]; then
    echo "Desktop environment detected. Installing additional GUI libraries..."
    apt-get install -y \
        libxcb-cursor0
fi

# Create project directory
PROJECT_DIR="/opt/desktop-bot"
mkdir -p "$PROJECT_DIR"

# Clone project (replace with actual repository URL)
echo "Cloning desktop automation bot repository..."
git clone https://github.com/automatyzer/desktop-bot.git "$PROJECT_DIR"

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt

# Verify all requirements are installed
pip install lxml python-dotenv apscheduler schedule requests \
            flask flask-cors flask-limiter gunicorn pytest \
            werkzeug termcolor pyautogui paramiko pytesseract \
            pillow opencv-python

# Set permissions
chown -R $(logname):$(logname) "$PROJECT_DIR"

# Cleanup
apt-get clean
apt-get autoremove -y

echo "Desktop Automation Bot environment setup complete!"
echo "To activate the virtual environment, run: source $PROJECT_DIR/venv/bin/activate"
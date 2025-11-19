#!/bin/bash

# Navigate to script directory to ensure paths are relative to the script location
cd "$(dirname "$0")"

# Dependency Check
NEEDS_INSTALL=false

if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Python is not installed."
    NEEDS_INSTALL=true
fi

if ! command -v yay &> /dev/null; then
    echo "yay is not installed."
    NEEDS_INSTALL=true
fi

if [ "$NEEDS_INSTALL" = true ]; then
    echo "Missing dependencies detected."
    read -p "Install python and yay using pacman? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo pacman -S python yay
    else
        echo "Dependencies are required to proceed. Please install them manually."
        exit 1
    fi
fi

# Determine python command
PYTHON_CMD=python
if ! command -v python &> /dev/null; then
    PYTHON_CMD=python3
fi

# Virtual Environment Setup
if [ ! -d ".venv" ]; then
    echo "Setting up GOAT'd Environment..."
    $PYTHON_CMD -m venv .venv
    ./.venv/bin/pip install -r requirements.txt
fi

# Refresh sudo credentials to avoid password prompt inside the TUI
echo "Please enter your sudo password to allow administrative tasks:"
sudo -v

# Keep sudo alive in the background
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Launch
./.venv/bin/python src/main.py
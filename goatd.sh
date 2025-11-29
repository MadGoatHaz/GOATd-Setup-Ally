#!/bin/bash

# -----------------------------------------------------------------------------
# GOATd Wrapper Script - v1.1 Self-Healing
# -----------------------------------------------------------------------------

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure we are running from the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Configuration
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# -----------------------------------------------------------------------------
# 1. Root Permission Safety Checks
# -----------------------------------------------------------------------------

CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)

# Scenario A: User ran this script with 'sudo', which is generally bad for venv creation.
if [ "$CURRENT_UID" -eq 0 ]; then
    echo -e "${YELLOW}WARNING: You are running this wrapper as root!${NC}"
    echo "This will create root-owned files in your directory, potentially causing"
    echo "permission errors when you run as a normal user later."
    echo
    echo "The recommended way is to run: ./goatd.sh"
    echo "The application will ask for sudo privileges when needed."
    echo
    read -p "Do you strictly intend to run the entire application as root? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting to protect file permissions."
        exit 1
    fi
fi

# Scenario B: User is running normally, but a previous 'sudo' run left a root-owned .venv
if [ "$CURRENT_UID" -ne 0 ] && [ -d "$VENV_DIR" ]; then
    # Check owner of the directory
    OWNER_NAME=$(stat -c '%U' "$VENV_DIR" 2>/dev/null || ls -ld "$VENV_DIR" | awk '{print $3}')
    
    if [ "$OWNER_NAME" == "root" ]; then
        echo -e "${RED}CRITICAL: Detected a root-owned '$VENV_DIR' directory while running as user '$CURRENT_USER'.${NC}"
        echo "This prevents the script from updating dependencies or running correctly."
        echo "This likely happened because the script was previously run with 'sudo'."
        echo
        echo "To fix this, I need to delete the old environment so I can rebuild it for you."
        
        read -p "May I use 'sudo' temporarily to remove the corrupted '$VENV_DIR'? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if sudo rm -rf "$VENV_DIR"; then
                echo -e "${GREEN}Root-owned environment removed successfully.${NC}"
            else
                echo -e "${RED}Failed to remove '$VENV_DIR'. Please remove it manually and try again.${NC}"
                exit 1
            fi
        else
            echo "Cannot proceed with permission conflict. Exiting."
            exit 1
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 2. System Dependency Checks
# -----------------------------------------------------------------------------

NEEDS_INSTALL=false

# Check for Python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}Error: Python is not installed.${NC}"
        NEEDS_INSTALL=true
    fi
fi

# Check for yay (Arch Linux helper) - Optional but recommended based on previous script
if ! command -v yay &> /dev/null; then
    # Only enforce strict check if likely on Arch
    if [ -f /etc/arch-release ]; then
        echo -e "${YELLOW}Warning: 'yay' is missing.${NC}"
        NEEDS_INSTALL=true
    fi
fi

if [ "$NEEDS_INSTALL" = true ]; then
    echo "Missing recommended system dependencies."
    if [ -f /etc/arch-release ]; then
        read -p "Install python and yay using pacman? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo pacman -S python yay --noconfirm
        else
            echo "Please install dependencies manually."
            exit 1
        fi
    else
        echo "Please ensure Python 3 is installed on your system."
        exit 1
    fi
fi

# Check for System Clipboard Tools (wl-clipboard or xclip)
# Required for "Copy Logs" functionality
if ! command -v wl-copy &> /dev/null && ! command -v xclip &> /dev/null; then
    if command -v pacman &> /dev/null; then
        echo "Installing system clipboard tools..."
        sudo pacman -S --noconfirm wl-clipboard xclip
    else
        echo -e "${YELLOW}Warning: System clipboard tools (wl-clipboard or xclip) missing.${NC}"
        echo "The 'Copy Logs' feature may not function correctly."
    fi
fi

# -----------------------------------------------------------------------------
# 3. Virtual Environment Management (Self-Healing)
# -----------------------------------------------------------------------------
echo "Checking environment..."

# Check if venv exists and is valid (has pip)
VENV_VALID=false
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ] && [ -f "$VENV_DIR/bin/pip" ]; then
    VENV_VALID=true
fi

if [ "$VENV_VALID" = false ]; then
    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Environment appears corrupted. Rebuilding...${NC}"
        rm -rf "$VENV_DIR"
    else
        echo "Creating new virtual environment..."
    fi

    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment!${NC}"
        echo "Please make sure you have write permissions in $(pwd)"
        exit 1
    fi
    
    echo "Upgrading pip..."
    "$VENV_DIR"/bin/pip install --upgrade pip &> /dev/null
fi

# Install/Update requirements
# We run this quietly to ensure deps are always up to date
echo "Verifying Python dependencies..."
"$VENV_DIR"/bin/pip install -r "$REQUIREMENTS" &> /dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies via pip.${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 4. Launch
# -----------------------------------------------------------------------------

# Refresh sudo credentials to avoid password prompt inside the TUI
# The app needs sudo for certain operations (system updates, etc)
echo -e "${GREEN}Environment ready.${NC}"
echo "Please enter your sudo password to allow administrative tasks:"
sudo -v

# Keep sudo alive in the background
# This prevents the sudo timeout from killing long-running tasks inside the app
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

echo -e "${GREEN}Launching GOATd...${NC}"
"$VENV_DIR"/bin/python "$SCRIPT_DIR/src/main.py"
#!/bin/bash
set -e

# -----------------------------------------------------------------------------
# GOATd Wrapper Script - v2.0 Self-Healing
# -----------------------------------------------------------------------------

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Ensure we are running from the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Configuration
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
TEMP_DIRS=()

# -----------------------------------------------------------------------------
# 0. Safety & Cleanup
# -----------------------------------------------------------------------------

cleanup() {
    if [ ${#TEMP_DIRS[@]} -gt 0 ]; then
        log_info "Cleaning up temporary directories..."
        for dir in "${TEMP_DIRS[@]}"; do
            if [ -d "$dir" ]; then
                rm -rf "$dir"
            fi
        done
    fi
}
trap cleanup EXIT INT TERM

# -----------------------------------------------------------------------------
# 1. Distro & Environment Checks
# -----------------------------------------------------------------------------

# Distro Check
if [[ ! -f /etc/arch-release ]] && ! command -v pacman &> /dev/null; then
    log_error "This script requires an Arch Linux-based distribution."
    log_error "File /etc/arch-release not found and 'pacman' is missing."
    exit 1
fi

# Root Permission Check
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)

# Scenario A: User ran this script with 'sudo'
if [ "$CURRENT_UID" -eq 0 ]; then
    log_warn "You are running this wrapper as root!"
    echo "This will create root-owned files in your directory, potentially causing"
    echo "permission errors when you run as a normal user later."
    echo
    echo "The recommended way is to run: ./goatd.sh"
    echo "The application will ask for sudo privileges when needed."
    echo
    read -p "Do you strictly intend to run the entire application as root? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Aborting to protect file permissions."
        exit 1
    fi
fi

# Scenario B: User is running normally, but a previous 'sudo' run left a root-owned .venv
if [ "$CURRENT_UID" -ne 0 ] && [ -d "$VENV_DIR" ]; then
    OWNER_NAME=$(stat -c '%U' "$VENV_DIR" 2>/dev/null || ls -ld "$VENV_DIR" | awk '{print $3}')
    
    if [ "$OWNER_NAME" == "root" ]; then
        log_error "Detected a root-owned '$VENV_DIR' directory while running as user '$CURRENT_USER'."
        echo "This prevents the script from updating dependencies or running correctly."
        echo "This likely happened because the script was previously run with 'sudo'."
        
        read -p "May I use 'sudo' temporarily to remove the corrupted '$VENV_DIR'? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if sudo rm -rf "$VENV_DIR"; then
                log_info "Root-owned environment removed successfully."
            else
                log_error "Failed to remove '$VENV_DIR'. Please remove it manually and try again."
                exit 1
            fi
        else
            log_error "Cannot proceed with permission conflict. Exiting."
            exit 1
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 2. System Dependency Checks
# -----------------------------------------------------------------------------

log_step "Checking system dependencies..."

# Python Check
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    log_warn "Python 3 is not installed."
    read -p "Install python using pacman? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo pacman -S python --noconfirm
        PYTHON_CMD="python"
    else
        log_error "Please install Python 3 manually."
        exit 1
    fi
else
    # Check Python version >= 3.8
    PY_VER=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
        log_error "Python 3.8 or higher is required. Found version $PY_VER"
        exit 1
    fi
fi

# Verify venv module availability
if ! $PYTHON_CMD -m venv --help &> /dev/null; then
    log_warn "Python 'venv' module appears missing."
    read -p "Install python-venv (or ensure python is full install)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # On Arch, venv is usually part of python, but sometimes separate in other distros/custom builds
        # We'll just try reinstalling python to be safe or ensure base-devel
        sudo pacman -S --needed python --noconfirm
    else
        log_error "Python venv module is required."
        exit 1
    fi
fi

# Check for AUR Helper (yay or paru)
AUR_HELPER=""
if command -v paru &> /dev/null; then
    AUR_HELPER="paru"
    log_info "Detected AUR helper: paru"
elif command -v yay &> /dev/null; then
    AUR_HELPER="yay"
    log_info "Detected AUR helper: yay"
fi

# If no helper found, offer to install yay
if [ -z "$AUR_HELPER" ]; then
    log_warn "No AUR helper (yay/paru) found."
    echo "GOATd uses an AUR helper for managing packages."
    read -p "Would you like to install 'yay' now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check for git and base-devel FIRST
        MISSING_DEPS=""
        if ! command -v git &> /dev/null; then MISSING_DEPS="$MISSING_DEPS git"; fi
        if ! pacman -Qi base-devel &> /dev/null; then MISSING_DEPS="$MISSING_DEPS base-devel"; fi
        
        if [ -n "$MISSING_DEPS" ]; then
            log_info "Installing build dependencies: $MISSING_DEPS"
            if ! sudo pacman -S --needed --noconfirm base-devel git; then
                log_error "Failed to install base-devel and git."
                exit 1
            fi
        fi

        log_info "Installing yay..."
        TEMP_DIR=$(mktemp -d)
        TEMP_DIRS+=("$TEMP_DIR") # Add to cleanup list
        
        log_info "Cloning yay into temporary directory..."
        # Robust clone with depth 1 to save bandwidth and time
        if git clone --depth 1 https://aur.archlinux.org/yay.git "$TEMP_DIR/yay"; then
            cd "$TEMP_DIR/yay"
            
            # Ensure we can actually build (user rights)
            if sudo -v; then
                if makepkg -si --noconfirm; then
                    AUR_HELPER="yay"
                    log_info "Successfully installed yay."
                else
                    log_error "Failed to build yay."
                    exit 1
                fi
            else
                log_error "Sudo privileges are required to install yay."
                exit 1
            fi
            
            cd "$SCRIPT_DIR"
        else
            log_error "Failed to clone yay repository."
            exit 1
        fi
        # Explicit cleanup after success so we don't keep it around during app runtime
        rm -rf "$TEMP_DIR"
    else
        log_warn "Proceeding without AUR helper. Functionality may be limited."
    fi
fi

# Export variable for the Python application
export AUR_HELPER

# Check for Clipboard Tools
if ! command -v wl-copy &> /dev/null && ! command -v xclip &> /dev/null; then
    if command -v pacman &> /dev/null; then
        log_info "Installing system clipboard tools..."
        sudo pacman -S --noconfirm wl-clipboard xclip
    else
        log_warn "System clipboard tools (wl-clipboard or xclip) missing."
        echo "The 'Copy Logs' feature may not function correctly."
    fi
fi

# -----------------------------------------------------------------------------
# 3. Virtual Environment Management
# -----------------------------------------------------------------------------

log_step "Checking Python environment..."

VENV_VALID=false
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ] && [ -f "$VENV_DIR/bin/pip" ]; then
    VENV_VALID=true
fi

if [ "$VENV_VALID" = false ]; then
    if [ -d "$VENV_DIR" ]; then
        log_warn "Environment appears corrupted. Rebuilding..."
        rm -rf "$VENV_DIR"
    else
        log_info "Creating new virtual environment..."
    fi

    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        log_error "Failed to create virtual environment!"
        echo "Please make sure you have write permissions in $(pwd)"
        exit 1
    fi
    
    log_info "Upgrading pip..."
    "$VENV_DIR"/bin/pip install --upgrade pip &> /dev/null
fi

log_info "Verifying Python dependencies..."
"$VENV_DIR"/bin/pip install -r "$REQUIREMENTS" &> /dev/null

if [ $? -ne 0 ]; then
    log_error "Failed to install dependencies via pip."
    exit 1
fi

# -----------------------------------------------------------------------------
# 4. Launch
# -----------------------------------------------------------------------------

log_step "Environment ready."

# Refresh sudo credentials for the app
echo "Please enter your sudo password to allow administrative tasks:"
sudo -v

# Keep sudo alive in the background
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

log_info "Launching GOATd..."
exec "$VENV_DIR"/bin/python "$SCRIPT_DIR/src/main.py"
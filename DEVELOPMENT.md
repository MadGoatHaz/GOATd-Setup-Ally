# GOAT'd - Setup Ally: Development Documentation (v1.1 Blueprint)

## 1. v1.1 Core Upgrade Architecture

The v1.1 upgrade focuses on two critical pillars: **Advanced Hardware Management (GPU)** and **Resilient Self-Healing UX**.

### 1.1 GPU Management Architecture

The architecture has been split into specialized components to replace the legacy `src/drivers.py`:
1.  `src/gpu.py`: The backend logic for GPU discovery and system information.
2.  `src/gpu_installer.py`: **(NEW)** Dedicated installer logic handling multi-vendor package resolution, transaction phases, and system configuration.
3.  `src/gpu_ui.py`: Provides the `GPUConfigWidget` and `GSPManagerScreen` (moved from `src/gsp_manager.py`), managing all GPU-related UI interactions.
4.  `src/gsp_manager.py`: The single source of truth for Nvidia GSP firmware logic and safety checks.

#### GPU Tab & System Discovery (UI Layout)
The "GPU" feature is a primary tab alongside "Apps", "Printers", and "Tasks".

-   **Header**: "GPU Management"
-   **Panel A: Discovery (Active)**:
    -   Lists all detected GPUs.
    -   **Fields**: Model, Current Driver, Version, Type (Proprietary/Open).
    -   **GSP Integration**: GSP Firmware status is now integrated directly into this panel.
-   **Panel B: Configuration (Interactive)**:
    -   **Driver Mode Selection**: Proprietary vs Open (RadioSet - Mutually Exclusive).
    -   **Workload Selection**: "Gaming" and "AI / Compute Stack" (Checkboxes - Multi-Select Allowed).
-   **Panel C: Execution (Integrated)**:
    -   **Action**: "Next" button -> **Review Plan** -> "Confirm" button.

#### Installation Logic & Phases (`src/gpu_installer.py`)
The installer uses a phased approach to ensure robust, distinct, or combined deployments.

**1. Logic Split (Matrix)**
*   **Nvidia:**
    *   **Gaming:** `nvidia-utils`, `lib32-nvidia-utils`, `nvidia-settings`, `lib32-nvidia-utils`.
    *   **AI:** `cuda`, `cudnn`, `nvidia-container-toolkit`.
    *   **Base:** `nvidia-dkms` (Proprietary) or `nvidia-open-dkms` (Open).
*   **AMD:**
    *   **Gaming:** `mesa`, `lib32-mesa`, `vulkan-radeon`, `lib32-vulkan-radeon`, `xf86-video-amdgpu`.
    *   **AI:** `rocm-hip-sdk`, `rocm-opencl-sdk`.
    *   **Config:** HSA Override injection for consumer cards in AI mode.
*   **Intel:**
    *   **Gaming:** `mesa`, `lib32-mesa`, `vulkan-intel`, `lib32-vulkan-intel`, `intel-media-driver`.
    *   **AI:** `intel-compute-runtime`, `level-zero-loader`.

**2. Installation Phases**
1.  **Pre-Flight:**
    *   Check internet connectivity.
    *   Check for existing lock files.
    *   Verify sudo privileges.
2.  **Group Config:**
    *   Add current user to `render` and `video` groups (essential for AI/Hardware access without root).
3.  **Package Install:**
    *   Construct and execute the `pacman` transaction.
4.  **Post-Install:**
    *   **Nvidia:** `mkinitcpio -P` (ensure modules are loaded early).
    *   **AMD:** Set HSA environment variables if AI is selected.
    *   **General:** Enable necessary systemd services (e.g., `nvidia-persistenced` if applicable).

#### Logic Flow
1.  **Detection**:
    - Check OS: `/etc/os-release` (EndeavourOS vs Arch Linux).
    - Check Hardware: `lspci` or `nvidia-smi` check.
2.  **Workload Selection** (User Prompt - Multi-Select):
    - **Gaming**: Prioritizes Vulkan/OpenGL performance, overlays, and compatibility tools.
    - **AI / Compute**: Prioritizes CUDA (Nvidia), ROCm (AMD), OpenCL, and container runtimes.
3.  **Review Plan**:
    - User sees a summary of "Packages to Install" and "Configuration Changes" before execution.
4.  **Execution**:
    - Runs through the 4 phases defined above.

### 1.2 Self-Healing Wrapper (`goatd.sh`)

The current wrapper script (`goatd.sh`) suffers from permission fragility when the script is run with `sudo` but the venv was created by a user (or vice versa).

#### The Problem
-   `src/main.py` often needs root privileges for system changes.
-   If the user runs `sudo ./goatd.sh`, the `venv` might be created as root, causing subsequent non-sudo runs to fail or permission denied errors during `pip install`.

#### The v1.1 "Self-Healing" Specification
The new `goatd.sh` must implement the following logic sequence:

1.  **Ownership Check**: Check if `.venv` exists and is owned by `root`. If `root` owned and we are running as `$USER`, **nuke it** (`rm -rf .venv`).
2.  **Auto-Provision**: If `.venv` is missing/deleted, recreate it as the current user.
3.  **Pip Safety**: Run `pip install` with a flag to ignore root warnings if absolutely necessary, but prefer user-mode installation.
4.  **Dependency Checks**: Auto-detects and installs missing system dependencies (`python`, `yay`, `xclip`/`wl-clipboard`) before execution.
5.  **Sudo Keep-Alive**: Maintain the existing `sudo -v` loop for the python script, but ensure the *environment* is user-owned.

### 1.3 System Tasks

#### Nvidia GSP Manager (`src/gsp_manager.py`)
Targeting stuttering issues on RTX cards by managing the GSP firmware state. This feature must be **reversible** and follow the "Glass Box" philosophy.

-   **Safety Protocol (CRITICAL)**:
    -   **Hardware Guardrail (Blackwell)**: Detect RTX 5000 series (Blackwell).
        -   *Action*: If detected, **ABORT**. Blackwell requires Open Modules and GSP.
    -   **Strict Package Verification**: Use `pacman -Qq` for exact matching.
    -   **Blacklist**: `nvidia-open`, `nvidia-open-dkms`.
    -   **Whitelist**: `nvidia`, `nvidia-dkms`, `nvidia-lts`.
    -   **Logic**: System is compatible ONLY if a Whitelist package is present AND NO Blacklist packages are detected.
    -   **Action**: If incompatible, **ABORT** operation. The GSP fix is incompatible with open kernel modules (and Blackwell hardware) and causes boot failures.
-   **Logic Specification**:
    -   **State Detection**: Scan configuration files for `nvidia.NVreg_EnableGpuFirmware=0`.
    -   **Toggle Flow**:
        -   If detected (Disabled/Fixed) -> Offer **"Enable GSP (Revert)"**.
        -   If NOT detected (Enabled/Default) -> Offer **"Disable GSP (Apply Fix)"**.
-   **Bootloader Support**:
    -   **GRUB**: Edit `/etc/default/grub` (specifically `GRUB_CMDLINE_LINUX_DEFAULT`). Run `grub-mkconfig`.
    -   **EndeavourOS (Systemd-boot)**: Edit `/etc/kernel/cmdline`. Run `reinstall-kernels`.
    -   **Vanilla Arch (Systemd-boot)**: "Scenario C".
        -   *Detection*: `/boot/loader/entries/*.conf` exists AND `reinstall-kernels` is missing.
        -   *Action*: Edit `.conf` files directly (append/remove from `options` line).
        -   *Regen*: None needed.
-   **Safety**: Emphasize clean string replacement (no regex hacks that break other params).

---

## 2. App Catalog Specifications (v1.1 Additions)

The following applications are to be added to `src/apps.py` in the appropriate categories.

### 2.1 Hardware Control
**LACT (Linux AMD/Nvidia Control Tool)**
-   **Description**: Modern, GTK4/Rust-based GPU control specifically for RDNA 2/3 and Nvidia.
-   **Source**: AUR (`lact`).
-   **Post-Install Action**: Must enable the daemon service: `sudo systemctl enable --now lactd`.

### 2.2 Gaming
**MangoHud**
-   **Description**: A Vulkan and OpenGL overlay for monitoring FPS, temperatures, CPU/GPU load and more.
-   **Source**: pacman (`mangohud`).
-   **Tier**: Top Tier.

### 2.3 AI & Creative
**LM Studio**
-   **Description**: Easy-to-use desktop application for running local LLMs (Large Language Models).
-   **Source**: AUR (`lm-studio-appimage` or similar binary).
-   **Tier**: God Tier.

---

## 3. Existing System Architecture (Reference)

*Refined from v1.0 docs*

GOAT'd is built using **Python** and the **Textual** TUI framework.

-   **Core Framework**: Textual (CSS-driven TUI).
-   **Language**: Python 3.
-   **Package Management**: Uses `pacman` and automatically detects AUR helpers (`yay`, `paru`, etc.).

### Technical Details
-   **AUR Detection**: `src/config.py` -> `detect_aur_helper()` scans for `paru`, `yay`, `trizen`, `pikaur`, `aura`.
-   **Firewall State**: Uses a global dictionary to track user intent before committing `firewall-cmd` rules.
-   **Printer Logic**: Automates CUPS + Gutenprint installation and service enablement.

## 4. Roadmap

-   [x] **v1.0**: Base App Installer, Firewall, Printer Setup.
-   [x] **v1.1**: GPU Management Module, Self-Healing Wrapper, Expanded Catalog.
-   [x] **Fix & Finish**: Final polish, GSP Manager integration, and dependency hardening.
-   [ ] **v1.2**: Network Manager Integration (WiFi/Bluetooth TUI).

## 5. Current Status & Known Limitations

*Last Audited: 2025-11-29*

This section provides an honest assessment of the current codebase state versus the design spec.

### 5.1 Implemented Features (Stable)
*   **UI Layout & Navigation:** The `GPUConfigWidget` correctly integrates into the main tabbed interface.
*   **GPU Detection:** Correctly identifies Vendor, Model, and Driver state via `src/gpu.py`.
*   **Plan Generation:** `src/gpu_installer.py` correctly generates lists of packages based on user selection (Gaming/AI + Driver Type).
*   **User Group Configuration:** The installer correctly adds the current user to `video` and `render` groups.
*   **GSP Logic:** The `GSPManager` correctly identifies firmware state and generates valid commands for GRUB/Systemd-boot.

### 5.2 Partially Implemented / Incomplete (Beta)
*   **Mkinitcpio Hooks:** The installer runs `sudo mkinitcpio -P` but **does not** edit `/etc/mkinitcpio.conf` to add the required Nvidia modules first. This renders the "early loading" feature non-functional.
*   **AMD HSA Override:** The code flags a warning for consumer cards but does not automatically inject the `HSA_OVERRIDE_GFX_VERSION` environment variable into the user's profile or session.

### 5.3 Missing Features (Planned)
*   **Pre-Flight Checks:** The design calls for internet connectivity checks, lock file detection, and sudo verification. **These are currently missing** from `src/gpu_installer.py`. The command execution assumes a happy path.
*   **Error Handling:** The `ExecutionModal` captures stdout/stderr but does not have robust recovery logic if a `pacman` transaction fails halfway through.
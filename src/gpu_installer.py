import getpass
import os
import shutil
from functools import lru_cache

@lru_cache(maxsize=1)
def detect_aur_helper():
    """Detects an available AUR helper (yay, paru, etc)."""
    helpers = ['paru', 'yay', 'trizen', 'pikaur', 'aura']
    for helper in helpers:
        if shutil.which(helper):
            return helper
    return None

def get_distro_id():
    """
    Reads /etc/os-release to identify the distribution.
    Returns 'endeavouros', 'arch', or 'unknown'.
    """
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        # Handle ID="endeavouros" or ID=arch
                        val = line.split("=")[1].strip().strip('"').strip("'")
                        return val.lower()
    except Exception:
        return "unknown"
    return "unknown"

def get_installation_plan(vendor_id, workloads, driver_type="type_open"):
    """
    Generates an installation plan based on vendor and selected workloads.
    
    :param vendor_id: 'nvidia', 'amd', or 'intel'
    :param workloads: Set or list of selected workloads (e.g., {'gaming', 'ai'})
    :param driver_type: 'type_prop', 'type_open', or 'type_beta'
    :return: Dictionary containing 'packages', 'services', 'post_install_cmds', 'warnings', 'groups', 'nvidia_inst_cmd', 'aur_packages'
    """
    plan = {
        "packages": [],
        "aur_packages": [],
        "services": [],
        "post_install_cmds": [],
        "warnings": [],
        "groups": ["video", "render"],
        "nvidia_inst_cmd": None  # Specific for EndeavourOS Nvidia
    }
    
    workloads = set(workloads) # e.g. {'gaming', 'ai'}
    distro = get_distro_id()
    aur_helper = detect_aur_helper()

    if vendor_id == "nvidia":
        # Handle Beta first (Arch/AUR)
        if driver_type == "type_beta":
            if not aur_helper:
                plan["warnings"].append("Beta drivers require an AUR helper (yay/paru), but none was found.")
            else:
                # Beta packages typically from AUR
                plan["aur_packages"].append("nvidia-beta-dkms")
                plan["aur_packages"].extend(["nvidia-utils-beta", "nvidia-settings-beta"])
                
                if "gaming" in workloads:
                    plan["aur_packages"].append("lib32-nvidia-utils-beta")
                
                if "ai" in workloads:
                     plan["packages"].extend(["cuda", "cudnn", "nvidia-container-toolkit"])

                plan["post_install_cmds"].append("sudo mkinitcpio -P")
                
                # Check for possible conflict with regular packages
                plan["warnings"].append("Installing Beta drivers may conflict with existing Nvidia packages. Manual intervention might be required.")

        # SCENARIO A: EndeavourOS + Nvidia (Standard/Open)
        elif distro == "endeavouros":
            # Construct nvidia-inst command
            cmd_parts = ["nvidia-inst"]
            
            # Driver Type
            if driver_type == "type_prop":
                cmd_parts.append("--closed")
            else:
                # Default to open if not explicitly proprietary
                cmd_parts.append("--open")
            
            # Gaming (32-bit support)
            if "gaming" in workloads:
                cmd_parts.append("--32")
            
            plan["nvidia_inst_cmd"] = " ".join(cmd_parts)
            
            # AI / Extras (Must be installed manually via pacman after nvidia-inst)
            if "ai" in workloads:
                plan["packages"].extend(["cuda", "cudnn", "nvidia-container-toolkit"])

        # SCENARIO B: Arch Linux + Nvidia (Manual Construction - Standard/Open)
        else:
            # Base Driver
            if driver_type == "type_prop":
                plan["packages"].append("nvidia-dkms")
            else:
                # Default to open
                plan["packages"].append("nvidia-open-dkms")
            
            plan["packages"].extend(["nvidia-utils", "nvidia-settings"])
            
            # Gaming
            if "gaming" in workloads:
                plan["packages"].append("lib32-nvidia-utils")
                
            # AI
            if "ai" in workloads:
                plan["packages"].extend(["cuda", "cudnn", "nvidia-container-toolkit"])
                
            # Post Install for Nvidia (Manual Arch Way)
            plan["post_install_cmds"].append("sudo mkinitcpio -P")
        
    elif vendor_id == "amd":
        # SCENARIO C: AMD
        # Gaming
        if "gaming" in workloads:
            plan["packages"].extend([
                "mesa", "lib32-mesa", 
                "vulkan-radeon", "lib32-vulkan-radeon", 
                "xf86-video-amdgpu"
            ])
            
        # AI
        if "ai" in workloads:
            plan["packages"].extend(["rocm-hip-sdk", "rocm-opencl-sdk"])
            plan["warnings"].append("Consumer AMD cards may require HSA_OVERRIDE_GFX_VERSION environment variable for AI/ROCm workloads.")

    elif vendor_id == "intel":
        # SCENARIO C: Intel
        # Gaming
        if "gaming" in workloads:
            plan["packages"].extend([
                "mesa", "lib32-mesa",
                "vulkan-intel", "lib32-vulkan-intel",
                "intel-media-driver"
            ])
            
        # AI
        if "ai" in workloads:
            plan["packages"].extend(["intel-compute-runtime", "level-zero-loader"])

    return plan

def generate_installation_command(plan):
    """
    Converts a plan into a single chained shell command string suitable for ExecutionModal.
    Format: [Install Helper if needed] && [Run Driver Install] && [Install Extras]
    """
    CONFLICTING_STANDARD = [
        "nvidia", "nvidia-dkms", "nvidia-open", "nvidia-open-dkms",
        "nvidia-utils", "lib32-nvidia-utils", "nvidia-lts", "nvidia-settings"
    ]

    CONFLICTING_BETA = [
        "nvidia-beta-dkms", "nvidia-utils-beta", "lib32-nvidia-utils-beta",
        "nvidia-settings-beta", "opencl-nvidia-beta"
    ]

    commands = []
    
    # 1. Group Configuration
    # Use SUDO_USER if available (when running as root via sudo), otherwise current user
    user = os.environ.get("SUDO_USER", getpass.getuser())
    for group in plan.get("groups", []):
        commands.append(f"sudo usermod -aG {group} {user}")

    # Check if we are installing Standard Nvidia drivers
    # This includes EndeavourOS 'nvidia_inst_cmd' OR manual Arch packages
    is_standard_install = False
    if plan.get("nvidia_inst_cmd"):
        is_standard_install = True
    else:
        # Check against standard packages list
        if any(pkg in CONFLICTING_STANDARD for pkg in plan.get("packages", [])):
            is_standard_install = True
            
    # If installing Standard, remove Beta first
    if is_standard_install:
        beta_conflicts = " ".join(CONFLICTING_BETA)
        # Robust removal: check which conflicting packages exist (-Qq) then remove them
        removal_cmd = (
            f'pkgs_to_remove=$(pacman -Qq {beta_conflicts} 2>/dev/null); '
            'if [ -n "$pkgs_to_remove" ]; then '
            'sudo pacman -Rdd --noconfirm $pkgs_to_remove; '
            'fi'
        )
        commands.append(removal_cmd)
        
    # 2. Install Helper / Base Driver (EndeavourOS Nvidia Special Case)
    if plan.get("nvidia_inst_cmd"):
        # Check if nvidia-inst is installed; install if missing
        # We use a subshell or conditional execution to ensure safety
        ensure_helper_cmd = "(pacman -Qi nvidia-inst &>/dev/null || sudo pacman -S --noconfirm nvidia-inst)"
        commands.append(ensure_helper_cmd)
        
        # Run the nvidia-inst command
        inst_cmd = plan["nvidia_inst_cmd"]
        
        # Safety: Ensure the command only contains expected safe characters if possible,
        # but since it's constructed internally in get_installation_plan, we trust it reasonably.
        # We still ensure it starts with sudo.
        
        # Ensure sudo
        if not inst_cmd.strip().startswith("sudo"):
            inst_cmd = f"sudo {inst_cmd}"
            
        # Add noconfirm if possible? nvidia-inst usually has --noconfirm or similar? 
        # nvidia-inst on EOS is interactive strictly speaking? 
        # Checking docs: nvidia-inst is a python script. It might not have a pure non-interactive mode without specific flags.
        # However, existing usage patterns suggest it's used as a CLI tool.
        # We will use the command as constructed.
        commands.append(inst_cmd)

    # 3. Package Installation (Standard Arch or EOS Extras)
    packages = plan.get("packages", [])
    if packages:
        pkg_str = " ".join(packages)
        commands.append(f"sudo pacman -S --noconfirm --needed {pkg_str}")

    # 4. AUR Packages
    aur_packages = plan.get("aur_packages", [])
    if aur_packages:
        helper = detect_aur_helper()
        if helper:
            # Special handling for Beta drivers: remove conflicting standard packages first
            # Check if any beta packages are being installed
            if any(pkg in CONFLICTING_BETA for pkg in aur_packages):
                std_conflicts = " ".join(CONFLICTING_STANDARD)
                # Robust removal: check which conflicting packages exist (-Qq) then remove them
                removal_cmd = (
                    f'pkgs_to_remove=$(pacman -Qq {std_conflicts} 2>/dev/null); '
                    'if [ -n "$pkgs_to_remove" ]; then '
                    'sudo pacman -Rdd --noconfirm $pkgs_to_remove; '
                    'fi'
                )
                commands.append(removal_cmd)

            pkg_str = " ".join(aur_packages)
            commands.append(f"{helper} -S --noconfirm --needed {pkg_str}")
        else:
            # Should have been warned in plan, but failsafe
            pass
        
    # 5. Post-Install Commands
    for cmd in plan.get("post_install_cmds", []):
        if cmd == "sudo mkinitcpio -P":
            # Replace hardcoded mkinitcpio with robust detection (mkinitcpio vs dracut)
            robust_cmd = (
                'if command -v mkinitcpio >/dev/null; then sudo mkinitcpio -P; '
                'elif command -v dracut >/dev/null; then sudo dracut --regenerate-all --force; '
                'else echo "Warning: No known initramfs generator found. Please regenerate manually."; fi'
            )
            commands.append(robust_cmd)
        else:
            commands.append(cmd)
    
    # 6. Services
    services = plan.get("services", [])
    for svc in services:
        commands.append(f"sudo systemctl enable --now {svc}")

    return " && ".join(commands)
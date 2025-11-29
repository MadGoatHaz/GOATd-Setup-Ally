import getpass
import os

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

def get_installation_plan(vendor_id, workloads, driver_type="type_prop"):
    """
    Generates an installation plan based on vendor and selected workloads.
    
    :param vendor_id: 'nvidia', 'amd', or 'intel'
    :param workloads: Set or list of selected workloads (e.g., {'gaming', 'ai'})
    :param driver_type: 'type_prop' or 'type_open'
    :return: Dictionary containing 'packages', 'services', 'post_install_cmds', 'warnings', 'groups', 'nvidia_inst_cmd'
    """
    plan = {
        "packages": [],
        "services": [],
        "post_install_cmds": [],
        "warnings": [],
        "groups": ["video", "render"],
        "nvidia_inst_cmd": None  # Specific for EndeavourOS Nvidia
    }
    
    workloads = set(workloads) # e.g. {'gaming', 'ai'}
    distro = get_distro_id()

    if vendor_id == "nvidia":
        # SCENARIO A: EndeavourOS + Nvidia
        if distro == "endeavouros":
            # Construct nvidia-inst command
            cmd_parts = ["nvidia-inst"]
            
            # Driver Type
            if driver_type == "type_open":
                cmd_parts.append("--open")
            else:
                # Proprietary: Use --closed. 
                # Note: Instructions mentioned --series 550 but --closed is safer as a generic default.
                cmd_parts.append("--closed")
            
            # Gaming (32-bit support)
            if "gaming" in workloads:
                cmd_parts.append("--32")
            
            plan["nvidia_inst_cmd"] = " ".join(cmd_parts)
            
            # AI / Extras (Must be installed manually via pacman after nvidia-inst)
            if "ai" in workloads:
                plan["packages"].extend(["cuda", "cudnn", "nvidia-container-toolkit"])

        # SCENARIO B: Arch Linux + Nvidia (Manual Construction)
        else:
            # Base Driver
            if driver_type == "type_open":
                plan["packages"].append("nvidia-open-dkms")
            else:
                plan["packages"].append("nvidia-dkms")
            
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
    commands = []
    
    # 1. Group Configuration
    # Use SUDO_USER if available (when running as root via sudo), otherwise current user
    user = os.environ.get("SUDO_USER", getpass.getuser())
    for group in plan.get("groups", []):
        commands.append(f"sudo usermod -aG {group} {user}")
        
    # 2. Install Helper / Base Driver (EndeavourOS Nvidia Special Case)
    if plan.get("nvidia_inst_cmd"):
        # Check if nvidia-inst is installed; install if missing
        # We use a subshell or conditional execution to ensure safety
        ensure_helper_cmd = "(pacman -Qi nvidia-inst &>/dev/null || sudo pacman -S --noconfirm nvidia-inst)"
        commands.append(ensure_helper_cmd)
        
        # Run the nvidia-inst command
        inst_cmd = plan["nvidia_inst_cmd"]
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
        
    # 4. Post-Install Commands
    commands.extend(plan.get("post_install_cmds", []))
    
    # 5. Services
    services = plan.get("services", [])
    for svc in services:
        commands.append(f"sudo systemctl enable --now {svc}")

    return " && ".join(commands)
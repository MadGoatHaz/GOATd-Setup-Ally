import subprocess
import json
import shlex
import sys
import shutil

import gsp_manager

def get_system_gpu_info():
    """
    Discovers system GPU information including hardware details,
    installed drivers/packages, and GSP status.
    """
    results = {
        "gpus": [],
        "installed_packages": [],
        "gsp_status": "Unknown",
        "gsp_compatibility": "Unknown",
        "gsp_configured": "Unknown"
    }

    # 1. Package Discovery
    # We check for specific packages relevant to GPU drivers
    target_packages = ["nvidia", "nvidia-lts", "nvidia-dkms", "nvidia-open", "nvidia-open-dkms", "nvidia-beta-dkms", "mesa"]
    
    if shutil.which('pacman'):
        try:
            # Use pacman -Qq to list all installed packages quietly
            # This is safer than -Qs which does a fuzzy search on description
            pacman_res = subprocess.run(['pacman', '-Qq'], capture_output=True, text=True)
            if pacman_res.returncode == 0:
                installed_set = set(pacman_res.stdout.splitlines())
                for pkg in target_packages:
                    if pkg in installed_set:
                        results["installed_packages"].append(pkg)
            else:
                # Log to stderr to avoid corrupting stdout JSON
                print(f"Warning: pacman returned non-zero exit code: {pacman_res.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Error checking packages: {e}", file=sys.stderr)

    # 2. Hardware & Active Driver Discovery
    try:
        # Run lspci -mm for machine-readable hardware info
        lspci_mm_res = subprocess.run(['lspci', '-mm'], capture_output=True, text=True)
        lspci_mm_out = lspci_mm_res.stdout if lspci_mm_res.returncode == 0 else ""

        # Run lspci -k for kernel driver info
        lspci_k_res = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
        lspci_k_out = lspci_k_res.stdout if lspci_k_res.returncode == 0 else ""

        if lspci_mm_out:
            for line in lspci_mm_out.splitlines():
                # lspci -mm format: Slot "Class" "Vendor" "Device" ...
                # We use shlex to correctly parse the quoted strings
                try:
                    parts = shlex.split(line)
                    if len(parts) < 4:
                        continue
                        
                    slot = parts[0]
                    device_class = parts[1]
                    vendor = parts[2]
                    model = parts[3]

                    # Filter for VGA or 3D controllers
                    if "VGA" in device_class or "3D" in device_class:
                        # Determine Type & Vendor ID
                        gpu_type = "Unknown"
                        vendor_id = "unknown"
                        vendor_upper = vendor.upper()

                        if "NVIDIA" in vendor_upper:
                            gpu_type = "NVIDIA"
                            vendor_id = "nvidia"
                        elif "AMD" in vendor_upper or "ATI TECHNOLOGIES" in vendor_upper or vendor_upper.startswith("ATI ") or "ADVANCED MICRO DEVICES" in vendor_upper:
                            gpu_type = "AMD"
                            vendor_id = "amd"
                        elif "INTEL" in vendor_upper:
                            gpu_type = "INTEL"
                            vendor_id = "intel"

                        # Find active driver from lspci -k output
                        driver = "Unknown"
                        if lspci_k_out:
                            # lspci -k groups output by slot. Find the block for this slot.
                            # 01:00.0 VGA ...
                            #   Kernel driver in use: nvidia
                            
                            found_slot = False
                            for k_line in lspci_k_out.splitlines():
                                if k_line.startswith(slot):
                                    found_slot = True
                                    continue
                                
                                if found_slot:
                                    # If we hit another slot definition (starts with digit), stop
                                    if k_line and k_line[0].isdigit():
                                        break
                                    
                                    if "Kernel driver in use:" in k_line:
                                        driver = k_line.split("Kernel driver in use:")[1].strip()
                                        break

                        # Determine driver type details
                        driver_type = "Unknown"
                        if driver == "nouveau":
                            driver_type = "Open Source (Community)"
                        elif driver == "nvidia":
                            # Check installed packages for specific variants first
                            if "nvidia-beta-dkms" in results["installed_packages"]:
                                driver_type = "Nvidia Beta (Proprietary)"
                            elif "nvidia-open-dkms" in results["installed_packages"] or "nvidia-open" in results["installed_packages"]:
                                driver_type = "Nvidia Open Source (Proprietary)"
                            else:
                                # Fallback to /proc check
                                try:
                                    with open("/proc/driver/nvidia/version", "r") as f:
                                        version_content = f.read()
                                        if "Open Source" in version_content or "Open Kernel Module" in version_content:
                                            driver_type = "Proprietary (Open Source Module)"
                                        else:
                                            driver_type = "Proprietary (Closed Source)"
                                except Exception:
                                    driver_type = "Proprietary (Unknown)"

                        results["gpus"].append({
                            "slot": slot,
                            "vendor": vendor,
                            "vendor_id": vendor_id,
                            "model": model,
                            "type": gpu_type,
                            "driver": driver,
                            "driver_type": driver_type
                        })

                except ValueError:
                    # Handle potential parsing errors
                    continue
    except Exception as e:
        print(f"Error during hardware discovery: {e}", file=sys.stderr)

    # 3. GSP Status (NVIDIA specific)
    # Combined check using gsp_manager for configuration and nvidia-smi for active state
    try:
        # A. Check Compatibility (Hardware/Driver Safety)
        compat = gsp_manager.check_nvidia_compatibility()
        results["gsp_compatibility"] = compat

        # B. Check Configured State (Bootloader params)
        # This tells us if the "fix" is applied in config, regardless of active state
        bootloader = gsp_manager.detect_bootloader()
        if bootloader:
            is_disabled_config = gsp_manager.is_gsp_disabled(bootloader)
            results["gsp_configured"] = "Disabled (Fix Applied)" if is_disabled_config else "Enabled (Default)"
        else:
            results["gsp_configured"] = "Unknown (Bootloader not detected)"

        # C. Check Active Runtime State (nvidia-smi)
        results["gsp_status"] = gsp_manager.check_gsp_active_status()

    except Exception as e:
        results["gsp_status"] = f"Error checking GSP: {e}"

    return results

if __name__ == "__main__":
    # When run directly, print the gathered info as JSON for verification
    print(json.dumps(get_system_gpu_info(), indent=2))
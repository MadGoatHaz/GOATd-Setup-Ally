import os
import sys
import subprocess
import shutil
import argparse
import glob

GRUB_CONFIG = "/etc/default/grub"
EOS_CMDLINE = "/etc/kernel/cmdline"
PARAM = "nvidia.NVreg_EnableGpuFirmware=0"

def run_command(cmd, shell=False):
    """Runs a command and returns (returncode, stdout)."""
    try:
        # If shell=True, cmd should be a string. If False, a list.
        result = subprocess.run(cmd, shell=shell, check=False, capture_output=True, text=True)
        return result.returncode, result.stdout.strip()
    except Exception as e:
        return -1, str(e)

def is_blackwell():
    """
    Checks if the GPU is Nvidia Blackwell architecture (RTX 5000 series).
    Blackwell cards require Open Kernel Modules and cannot disable GSP.
    """
    try:
        # Query GPU name.
        # Expected output: "NVIDIA GeForce RTX 5090" or similar.
        cmd = ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
        ret, out = run_command(cmd)
        
        if ret != 0:
            # If nvidia-smi fails, we assume False (or let driver check fail later)
            return False
            
        out_upper = out.upper()
        
        # Safety Check: Explicitly exclude known "RTX 5000" workstation cards from previous gens
        # "RTX 5000 Ada Generation" -> Ada
        # "Quadro RTX 5000" -> Turing
        if "ADA GENERATION" in out_upper:
            return False
        if "QUADRO" in out_upper:
            return False

        # Check for key identifiers
        # "RTX 50" will catch "RTX 5000" (Workstation) unless excluded above.
        # But "RTX 5000" (the workstation card) typically appears as "NVIDIA RTX 5000" or "Quadro RTX 5000".
        # Consumer cards: "GeForce RTX 5090", "GeForce RTX 5080".
        
        # Strict check for consumer Blackwell series
        # We look for "RTX 50" followed by digits that indicate consumer series (5050-5099)
        # Simplification: Match "GEFORCE RTX 50"
        if "GEFORCE RTX 50" in out_upper:
            return True
            
        if "BLACKWELL" in out_upper:
            return True
            
        return False
    except:
        return False

def check_nvidia_compatibility():
    """
    Checks installed Nvidia packages and Hardware to determine compatibility.
    Returns:
        "COMPATIBLE": Safe to proceed.
        "INCOMPATIBLE_BLACKWELL": Blackwell architecture.
        "INCOMPATIBLE_OPEN": Open Kernel Modules.
        "INCOMPATIBLE_NO_DRIVER": No driver found.
    """
    BLACKLIST = ["nvidia-open", "nvidia-open-dkms"]
    WHITELIST = ["nvidia", "nvidia-dkms", "nvidia-lts"]

    # 1. Check Whitelist (Driver Presence)
    driver_found = False
    for pkg in WHITELIST:
        ret, _ = run_command(["pacman", "-Qq", pkg])
        if ret == 0:
            driver_found = True
            break
    
    # Also check blacklist to allow hardware check
    if not driver_found:
        for pkg in BLACKLIST:
            ret, _ = run_command(["pacman", "-Qq", pkg])
            if ret == 0:
                driver_found = True
                break
    
    if not driver_found:
        return "INCOMPATIBLE_NO_DRIVER"

    # 2. Check Hardware (Blackwell Guardrail)
    if is_blackwell():
        return "INCOMPATIBLE_BLACKWELL"

    # 3. Active Driver Check (Proc File)
    try:
        if os.path.exists("/proc/driver/nvidia/version"):
            with open("/proc/driver/nvidia/version", "r") as f:
                content = f.read()
                if "Open Source" in content or "Open Kernel Module" in content:
                    return "INCOMPATIBLE_OPEN"
    except:
        pass

    # 4. Check Blacklist Packages (Fallback)
    for pkg in BLACKLIST:
        ret, _ = run_command(["pacman", "-Qq", pkg])
        if ret == 0:
            return "INCOMPATIBLE_OPEN"

    return "COMPATIBLE"

def detect_bootloader():
    """Detects if using GRUB, Systemd-boot (EOS style), or Manual Systemd-boot."""
    if os.path.exists(EOS_CMDLINE):
        return "systemd-boot"
    
    # Vanilla Arch / Manual Systemd-boot check
    # If reinstall-kernels is missing (Not EOS) and entries exist
    if not shutil.which("reinstall-kernels"):
        if os.path.isdir("/boot/loader/entries"):
            if glob.glob("/boot/loader/entries/*.conf"):
                return "systemd-boot-manual"

    if os.path.exists(GRUB_CONFIG):
        return "grub"
    return None

def is_gsp_disabled(bootloader):
    """
    Checks if the param is present.
    Returns True if GSP is DISABLED (param exists).
    Returns False if GSP is ENABLED (param missing).
    """
    if bootloader == "systemd-boot":
        try:
            with open(EOS_CMDLINE, 'r') as f:
                content = f.read()
            return PARAM in content
        except:
            return False
    elif bootloader == "systemd-boot-manual":
        try:
            files = glob.glob("/boot/loader/entries/*.conf")
            for fpath in files:
                with open(fpath, 'r') as f:
                    if PARAM in f.read():
                        return True
            return False
        except:
            return False
    elif bootloader == "grub":
        try:
            with open(GRUB_CONFIG, 'r') as f:
                content = f.read()
            return PARAM in content
        except:
            return False
    
    return False

def detect_state():
    """
    Combined function to detect bootloader and GSP state.
    Returns (bootloader, is_disabled) or specific error code.
    """
    # Check Compatibility First
    compat = check_nvidia_compatibility()
    if compat != "COMPATIBLE":
        return compat

    bootloader = detect_bootloader()
    if not bootloader:
        return None, None
    return bootloader, is_gsp_disabled(bootloader)

def toggle_gsp(bootloader, disable=True):
    """
    disable=True -> Add param (Disable GSP Firmware)
    disable=False -> Remove param (Enable GSP Firmware)
    """
    print(f"[*] Applying changes: GSP Firmware {'DISABLED' if disable else 'ENABLED'}...")
    
    if bootloader == "systemd-boot":
        return modify_file(EOS_CMDLINE, disable, mode="simple")
    elif bootloader == "systemd-boot-manual":
        files = glob.glob("/boot/loader/entries/*.conf")
        if not files:
            print("[!] No .conf files found in /boot/loader/entries/")
            return False
        
        success_any = False
        for fpath in files:
            if modify_file(fpath, disable, mode="conf"):
                success_any = True
        return success_any
    elif bootloader == "grub":
        return modify_file(GRUB_CONFIG, disable, mode="grub")
    return False

def process_grub_line(line, disable):
    """
    Helper to process a single GRUB config line.
    Parses quoted string, modifies args list, rebuilds string.
    """
    if not line.strip().startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
        return line
    
    try:
        # Robust parsing without regex
        if '="' not in line:
            return line
            
        key, rest = line.split('="', 1)
        
        # Find the last quote to handle content safely
        if '"' not in rest:
            return line
            
        content, suffix = rest.rsplit('"', 1)
        
        # Split arguments by whitespace
        args = content.split()
        
        if disable:
            # Disable GSP -> Add nvidia.NVreg_EnableGpuFirmware=0
            if PARAM not in args:
                args.append(PARAM)
        else:
            # Enable GSP -> Remove nvidia.NVreg_EnableGpuFirmware=0
            if PARAM in args:
                args.remove(PARAM)
        
        # Join back with single spaces
        new_content = " ".join(args)
        return f'{key}="{new_content}"{suffix}'
        
    except Exception:
        return line

def modify_file(filepath, disable, mode="simple"):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        modified = False
        
        for line in lines:
            target_line = False
            
            if mode == "grub":
                if line.strip().startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                    target_line = True
            elif mode == "conf":
                if line.strip().startswith("options"):
                    target_line = True
            else: # simple
                target_line = True

            if not target_line:
                new_lines.append(line)
                continue
            
            original_line = line
            
            if mode == "grub":
                line = process_grub_line(line, disable)
                if line != original_line:
                    modified = True
            else:
                # Systemd-boot logic
                if disable:
                    # ADDING
                    if PARAM not in line:
                        # Systemd-boot (simple or conf options line): just append
                        line = line.strip() + f" {PARAM}\n"
                        modified = True
                else:
                    # REMOVING
                    if PARAM in line:
                        # Systemd-boot (simple or conf)
                        parts = line.strip().split()
                        parts = [p for p in parts if p != PARAM]
                        line = " ".join(parts) + "\n"
                        modified = True
            
            new_lines.append(line)
            
        if not modified and disable:
             if mode == "grub":
                 # Check if it's because the line wasn't found or wasn't changed
                 has_grub_line = any(l.strip().startswith("GRUB_CMDLINE_LINUX_DEFAULT") for l in lines)
                 if not has_grub_line:
                     print("[!] Could not find GRUB_CMDLINE_LINUX_DEFAULT to edit.")
                     return False

        # Write back
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
            
        return True
        
    except Exception as e:
        print(f"[!] Error modifying {filepath}: {e}")
        return False

def regenerate_config(bootloader):
    print("[*] Regenerating boot configuration...")
    
    if bootloader == "systemd-boot-manual":
        print("[*] Configuration files updated directly. No regeneration needed.")
        return True

    if bootloader == "systemd-boot":
        cmd = "reinstall-kernels"
        if shutil.which(cmd):
            ret, out = run_command(["sudo", cmd])
            print(out)
            return ret == 0
        else:
            print(f"[!] '{cmd}' not found. Please regenerate manually.")
            return False
    elif bootloader == "grub":
        cmd = "grub-mkconfig"
        if not shutil.which(cmd):
            print(f"[!] '{cmd}' not found.")
            return False
        
        # Detect output path
        out_path = "/boot/grub/grub.cfg"
        ret, out = run_command(["sudo", cmd, "-o", out_path])
        print(out)
        return ret == 0
    return False

def check_gsp_active_status():
    """
    Checks the active runtime status of GSP Firmware using nvidia-smi.
    Returns a string describing the status:
    - "Enabled (Default)"
    - "Disabled (Fix Applied)"
    - "Unknown"
    - "Error: ..."
    - "N/A (nvidia-smi not found)"
    """
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return "N/A (nvidia-smi not found)"

    try:
        ret, out = run_command([nvidia_smi, '-q'])
        if ret == 0:
            # Look for "GSP Firmware Version"
            for line in out.splitlines():
                if "GSP Firmware Version" in line:
                    # Format: "    GSP Firmware Version                  : 535.113.01"
                    parts = line.split(":")
                    if len(parts) > 1:
                        version = parts[1].strip()
                        if version and version != "N/A":
                            return "Enabled (Default)"
                        else:
                            return "Disabled (Fix Applied)"
            
            # If loop finishes without finding the line
            # Some older drivers or cards might not show the field at all
            return "Unknown (Field missing in nvidia-smi)"
        else:
            return "Error running nvidia-smi"
    except Exception as e:
        return f"Error checking GSP: {e}"

def main_interactive(bootloader):
    """Original interactive mode."""
    is_disabled = is_gsp_disabled(bootloader)
    status_str = "Disabled (Fix Applied)" if is_disabled else "Enabled (Default)"
    
    print(f"[*] Current Nvidia GSP Firmware Status: {status_str}")
    print("")
    print("To fix stuttering on some Pascal/Turing+ cards, GSP should be DISABLED.")
    
    if is_disabled:
        prompt = "Do you want to ENABLE it (Revert to stock)? [y/N]: "
        target_disable = False
    else:
        prompt = "Do you want to DISABLE it (Apply Fix)? [y/N]: "
        target_disable = True
        
    try:
        choice = input(prompt).lower()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
        sys.exit(0)
        
    if choice == 'y':
        if toggle_gsp(bootloader, disable=target_disable):
            if regenerate_config(bootloader):
                print("\n[+] Success! Reboot required to take effect.")
                print("\nTo verify the fix after reboot, run:\n  nvidia-smi -q | grep GSP")
            else:
                print("\n[!] Config updated but regeneration failed. Please check output.")
        else:
            print("\n[!] Failed to modify configuration file.")
    else:
        print("[*] No changes made.")

def main():
    parser = argparse.ArgumentParser(description="Nvidia GSP Firmware Manager")
    parser.add_argument("--check", action="store_true", help="Check status and exit (Prints ENABLED or DISABLED)")
    parser.add_argument("--enable", action="store_true", help="Enable GSP (Revert stock)")
    parser.add_argument("--disable", action="store_true", help="Disable GSP (Apply Fix)")
    
    args = parser.parse_args()

    # Safety Check for Open Kernel Modules
    compat_status = check_nvidia_compatibility()
    if compat_status != "COMPATIBLE":
        if args.check:
            print(compat_status)
            sys.exit(0)
        
        # Diagnose for user message
        print("\n[!] CRITICAL ERROR: Compatibility Check Failed.")
        
        if compat_status == "INCOMPATIBLE_BLACKWELL":
            print("[-] RTX 5000 (Blackwell) series detected.")
            print("[-] Disabling GSP Firmware is not supported on this architecture.")
        elif compat_status == "INCOMPATIBLE_OPEN":
            print("[-] Open Source Kernel Modules detected.")
            print("[-] Disabling GSP Firmware requires proprietary 'nvidia-dkms' (Closed Source) drivers.")
            print("[-] Please switch to proprietary drivers to use this feature.")
        elif compat_status == "INCOMPATIBLE_NO_DRIVER":
            print("[-] No supported Nvidia driver installed.")
        else:
            print(f"[-] Incompatible configuration detected: {compat_status}")
            
        print("[-] Aborting operation.")
        sys.exit(1)
    
    # Check if any args were provided; if not, use interactive mode
    if not (args.check or args.enable or args.disable):
        # Check root for interactive mode (writes needed)
        if os.geteuid() != 0:
            print("[-] This script requires root privileges to modify boot config.")
            print("[-] Please run with sudo.")
        
        bootloader = detect_bootloader()
        if not bootloader:
            print("[!] Could not detect GRUB or Systemd-boot (EOS). Aborting.")
            sys.exit(1)
        
        print(f"[*] Detected Bootloader: {bootloader}")
        main_interactive(bootloader)
        return

    # Argument mode
    bootloader = detect_bootloader()
    if not bootloader:
        print("ERROR: No bootloader detected.") 
        sys.exit(1)

    if args.check:
        is_disabled = is_gsp_disabled(bootloader)
        # If disabled, it means fix is applied.
        # If enabled, it means default state.
        print("DISABLED" if is_disabled else "ENABLED")
        sys.exit(0)
    
    # Modification modes require root
    if os.geteuid() != 0:
        print("ERROR: Root privileges required.")
        sys.exit(1)

    if args.enable:
        # Revert fix
        if toggle_gsp(bootloader, disable=False):
            if regenerate_config(bootloader):
                print("SUCCESS: GSP Enabled (Default). Reboot required.")
                print("\nTo verify the fix after reboot, run:\n  nvidia-smi -q | grep GSP")
                sys.exit(0)
            else:
                print("WARNING: Config updated but regeneration failed.")
                sys.exit(1)
        else:
            print("ERROR: Failed to enable GSP.")
            sys.exit(1)

    if args.disable:
        # Apply fix
        if toggle_gsp(bootloader, disable=True):
            if regenerate_config(bootloader):
                print("SUCCESS: GSP Disabled (Fix Applied). Reboot required.")
                print("\nTo verify the fix after reboot, run:\n  nvidia-smi -q | grep GSP")
                sys.exit(0)
            else:
                print("WARNING: Config updated but regeneration failed.")
                sys.exit(1)
        else:
            print("ERROR: Failed to disable GSP.")
            sys.exit(1)

if __name__ == "__main__":
    # Self-Test
    test_line = 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"'
    expected_disabled = 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash nvidia.NVreg_EnableGpuFirmware=0"'
    expected_enabled = 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"'

    # Test Disable (Add Param)
    res_disabled = process_grub_line(test_line, disable=True)
    assert res_disabled == expected_disabled, f"FAILED Disable: {res_disabled}"

    # Test Enable (Remove Param)
    res_enabled = process_grub_line(res_disabled, disable=False)
    assert res_enabled == expected_enabled, f"FAILED Enable: {res_enabled}"

    print("PASS")
    
    # Only run main if args are present or interactive mode desired,
    # but for this task, we prioritize the test output.
    if len(sys.argv) > 1:
        main()
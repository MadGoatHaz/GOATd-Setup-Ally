import subprocess

def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed using pacman."""
    try:
        subprocess.run(
            ["pacman", "-Qi", package_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("pacman not found (expected on non-Arch systems)")
        return False

def test_package_check():
    print("--- Testing Package Check ---")
    
    # Test with a package that likely exists (e.g., bash, coreutils, or pacman itself if on Arch)
    # Since I don't know the exact OS, I'll try 'bash' which is common, but pacman -Qi only works on Arch.
    # If this is not Arch, it will fail or return False.
    
    pkg = "pacman"
    print(f"Checking if '{pkg}' is installed...")
    installed = is_package_installed(pkg)
    print(f"Result: {installed}")
    
    pkg = "non_existent_package_12345"
    print(f"Checking if '{pkg}' is installed...")
    installed = is_package_installed(pkg)
    print(f"Result: {installed}")
    
    if not installed:
        print("PASS: Non-existent package correctly identified as not installed.")
    else:
        print("FAIL: Non-existent package identified as installed.")

if __name__ == "__main__":
    test_package_check()
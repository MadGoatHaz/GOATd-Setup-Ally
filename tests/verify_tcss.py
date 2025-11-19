import re
import sys

TCSS_PATH = "GOATd/src/styles.tcss"

def check_tcss():
    try:
        with open(TCSS_PATH, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {TCSS_PATH}")
        sys.exit(1)

    errors = []
    
    # 1. Check for CSS Variables Definitions (using --var syntax)
    required_vars = [
        "--bg-main", "--bg-surface", "--text-main", "--text-muted", 
        "--primary", "--secondary", "--accent", "--error"
    ]
    
    print("🔍 Checking Variable Definitions...")
    for var in required_vars:
        if var + ":" not in content:
            errors.append(f"Missing variable definition: {var}")
    
    # 2. Check for Light Mode Overrides
    print("🔍 Checking Light Mode Overrides...")
    if ".light-mode {" not in content:
        errors.append("Missing .light-mode block")
    else:
        # Check if variables are redefined in light mode
        light_mode_block = re.search(r'\.light-mode \{([^}]+)\}', content)
        if light_mode_block:
            block_content = light_mode_block.group(1)
            for var in required_vars:
                if var + ":" not in block_content:
                    errors.append(f"Variable {var} not redefined in .light-mode")
        else:
            errors.append("Could not parse .light-mode block")

    # 3. Check SelectionList usage
    print("🔍 Checking SelectionList Usage...")
    if "SelectionList" not in content:
        errors.append("Missing SelectionList styling")
    if "--accent" not in content: # Should be used for the checkmark
        errors.append("SelectionList or checkmarks might not be using --accent")

    # 4. Check for Hardcoded Bright Green (The "Green X" culprit)
    # We look for #00ff00 or rgb(0, 255, 0) outside of the variable definitions
    print("🔍 Checking for Hardcoded Colors in Components...")
    
    # Remove the variable definition blocks to avoid false positives
    # This is a simple hacky removal, assuming standard formatting
    # Remove the first Screen definition which contains the default vars
    content_no_vars = re.sub(r'Screen \{[^}]+\}', '', content, count=1) 
    # Remove light mode vars
    content_no_vars = re.sub(r'\.light-mode \{[^}]+\}', '', content_no_vars, count=1) 
    
    forbidden_colors = ["#00ff00", "#00ffff", "#4b0082"]
    
    for line in content_no_vars.splitlines():
        for color in forbidden_colors:
            if color in line.lower():
                # Allow comments
                if "/*" in line: 
                    continue
                errors.append(f"Found hardcoded color {color} in line: {line.strip()}")

    if errors:
        print("\n❌ Verification FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ Verification PASSED: Stylesheet is clean and themable.")
        sys.exit(0)

if __name__ == "__main__":
    check_tcss()
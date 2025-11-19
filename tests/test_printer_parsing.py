import re

def parse_yay_output(output):
    lines = output.strip().split('\n')
    results = []
    current_package = None
    
    # Regex to capture: repo, package_name, version
    # Matches lines like: aur/brother-dcp-l2550dw 4.0.0-1 ...
    package_pattern = re.compile(r'^([^/\s]+)/([^\s]+)\s+([^\s]+)')

    for line in lines:
        # Check for package line
        match = package_pattern.match(line)
        if match:
            repo = match.group(1)
            package_name = match.group(2)
            version = match.group(3)
            current_package = package_name
        elif current_package and line.startswith('    '):
            # Description line (indented)
            description = line.strip()
            results.append((f"{current_package} - {description}", current_package))
            current_package = None
            
    return results

def test_parsing():
    print("--- Testing Printer Driver Parsing Logic ---")

    # Case 1: Clean output (yay -Ss --nocolor)
    clean_output = """
aur/brother-dcp-l2550dw 4.0.0-1 (20)
    Brother DCP-L2550DW LPR and CUPS driver
aur/brscan4 0.4.11-1 (15) [installed]
    Sane Scanner Driver for Brother Printers
core/cups 2.4.7-2 (100)
    The CUPS Printing System
"""
    print("\n[Case 1] Testing Clean Output:")
    results = parse_yay_output(clean_output)
    expected_count = 3
    print(f"Found {len(results)} drivers.")
    for label, value in results:
        print(f"  - {label}")
    
    if len(results) == expected_count:
        print("PASS: Correct number of drivers found.")
    else:
        print(f"FAIL: Expected {expected_count}, found {len(results)}")

    # Verify specific extraction
    if results[0][1] == "brother-dcp-l2550dw":
        print("PASS: First package name extracted correctly.")
    else:
        print(f"FAIL: Expected 'brother-dcp-l2550dw', got '{results[0][1]}'")

    # Case 2: Colored output (simulated)
    # Note: The regex provided is anchored to start of line (^), so it is expected to FAIL on colored output 
    # unless the color codes are stripped or the regex is modified. 
    # The task is to use --nocolor, so this test demonstrates WHY --nocolor is needed.
    colored_output = """
\x1b[1maur/\x1b[0m\x1b[1mbrother-dcp-l2550dw\x1b[0m \x1b[1m4.0.0-1\x1b[0m (20)
    Brother DCP-L2550DW LPR and CUPS driver
"""
    print("\n[Case 2] Testing Colored Output (Expect Failure/Empty with current regex):")
    results_colored = parse_yay_output(colored_output)
    print(f"Found {len(results_colored)} drivers.")
    if len(results_colored) == 0:
        print("PASS: Colored output correctly failed to parse (demonstrating need for --nocolor).")
    else:
        print("NOTE: Colored output was parsed (unexpected for this regex).")

if __name__ == "__main__":
    test_parsing()
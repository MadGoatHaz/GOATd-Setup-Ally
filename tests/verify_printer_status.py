import subprocess
import re

def parse_lpstat_output(output):
    """
    Parses lpstat -p output to extract printer names and their status.
    Example output:
    printer Brother_DCP_L2550DW is idle.  enabled since Wed 19 Nov 2025 08:00:00 AM MST
    printer HP_LaserJet_P1102w disabled since Wed 19 Nov 2025 08:00:00 AM MST -
        Unplugged or turned off
    """
    printers = []
    lines = output.splitlines()
    current_printer = None
    
    for line in lines:
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "printer":
            # Format: printer Name is status ...
            name = parts[1]
            # Status is typically "idle", "printing", "disabled", etc.
            # "is idle." -> status = "idle"
            # "disabled" -> status = "disabled"
            # "now printing" -> status = "printing"
            
            status_raw = " ".join(parts[2:])
            status = "Unknown"
            
            if "is idle" in status_raw:
                status = "Idle"
            elif "disabled" in status_raw:
                status = "Disabled"
            elif "now printing" in status_raw:
                status = "Printing"
            else:
                status = status_raw.split('.')[0] # Fallback
                
            printers.append(f"{name} ({status})")
            
    return printers

def test_parsing():
    print("--- Testing lpstat Parsing ---")
    
    sample_output = """printer Brother_DCP_L2550DW is idle.  enabled since Wed 19 Nov 2025 08:00:00 AM MST
printer HP_LaserJet_P1102w disabled since Wed 19 Nov 2025 08:00:00 AM MST -
    Unplugged or turned off
printer Canon_Pixma now printing Brother_DCP_L2550DW-123.  enabled since Wed 19 Nov 2025 08:05:00 AM MST
"""
    
    results = parse_lpstat_output(sample_output)
    print(f"Found {len(results)} printers:")
    for p in results:
        print(f"  - {p}")
        
    expected = [
        "Brother_DCP_L2550DW (Idle)",
        "HP_LaserJet_P1102w (Disabled)",
        "Canon_Pixma (Printing)"
    ]
    
    if results == expected:
        print("PASS: Parsing logic correct.")
    else:
        print("FAIL: Parsing logic incorrect.")
        print(f"Expected: {expected}")
        print(f"Got: {results}")

if __name__ == "__main__":
    test_parsing()
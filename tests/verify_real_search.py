import asyncio
import subprocess
import re
import sys

async def search_drivers(query: str):
    try:
        # Exact command from printer.py
        cmd = ["yay", "-Ss", "--color=never", query]
        print(f"Running command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"Error searching drivers: {stderr.decode().strip()}")
            return

        output = stdout.decode()
        print(f"Raw Output Length: {len(output)}")
        # print(f"Raw Output Sample:\n{output[:500]}...\n")

        lines = output.strip().split('\n')
        
        drivers = []
        current_package = None
        # Exact regex from printer.py
        package_pattern = re.compile(r'^([^/\s]+)/([^\s]+)\s+([^\s]+)')
        
        def strip_ansi(text):
            # Remove OSC sequences (hyperlinks): \x1b] ... \x1b\
            text = re.sub(r'\x1b\].*?\x1b\\', '', text)
            # Remove CSI sequences (colors): \x1b [ ... m (and others)
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)

        print("Parsing output...")
        count = 0
        for line in lines:
            clean_line = strip_ansi(line)
            match = package_pattern.match(clean_line)
            if match:
                if count < 5:
                    print(f"Original: {repr(line)}")
                    print(f"Cleaned:  {repr(clean_line)}")
                    print(f"Groups:   {match.groups()}")
                current_package = match.group(2)
            elif current_package and clean_line.startswith("    "):
                # print(f"Matched Description Line: {line}")
                description = line.strip()
                drivers.append((f"{current_package} - {description}", current_package))
                current_package = None
                count += 1
            # else:
            #     print(f"Unmatched Line: {line}")

        if drivers:
            print(f"\nFound {len(drivers)} drivers:")
            for label, value in drivers:
                print(f"  - {label} (Value: {value})")
        else:
            print("\nNo drivers found.")
            print(f"First 10 lines of raw output for debugging:")
            for line in lines[:10]:
                print(f"'{line}'")

    except Exception as e:
        print(f"Exception during search: {str(e)}")

if __name__ == "__main__":
    # Using 'python' as a common package that should return results
    query = "python"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    asyncio.run(search_drivers(query))
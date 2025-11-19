import subprocess
import sys

class MockPrinterSetup:
    def log_message(self, message):
        print(f"LOG: {message}")

    def _run_command(self, cmd):
        cmd_str = " ".join(cmd)
        self.log_message(f"Executing: {cmd_str}")
        # Using check=True to raise CalledProcessError on failure
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.log_message(f"[red]Command failed with return code {e.returncode}[/red]")
            if e.stdout:
                self.log_message(f"STDOUT:\n{e.stdout}")
            if e.stderr:
                self.log_message(f"STDERR:\n{e.stderr}")
            # We catch and re-raise to verify the logging happened before the raise
            raise e

def test_run_command():
    printer = MockPrinterSetup()
    
    print("--- Testing _run_command Success ---")
    try:
        printer._run_command(["echo", "Hello World"])
        print("PASS: Command succeeded as expected.")
    except Exception as e:
        print(f"FAIL: Command failed unexpectedly: {e}")

    print("\n--- Testing _run_command Failure ---")
    try:
        # Run a command that fails and prints to stderr
        printer._run_command(["ls", "/non/existent/path"])
        print("FAIL: Command succeeded unexpectedly.")
    except subprocess.CalledProcessError:
        print("PASS: Command failed as expected.")
    except Exception as e:
        print(f"FAIL: Unexpected exception type: {type(e)}")

if __name__ == "__main__":
    test_run_command()
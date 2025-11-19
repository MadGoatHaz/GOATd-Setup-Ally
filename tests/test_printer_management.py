import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from GOATd.src.printer import PrinterSetup

class MockPrinterSetup(PrinterSetup):
    def __init__(self):
        # Skip parent init to avoid widget initialization
        self.executed_commands = []
        self.logs = []
        # self.app is a property in Widget, can't set it directly in __init__ easily if we inherit
        # But since we skip parent init, we can't rely on Textual mechanics.
        # Let's mock the _app attribute which the property likely uses, or just mock log_message
        self._app = MagicMock()

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        self._app = value

    def log_message(self, message: str):
        self.logs.append(message)

    async def _run_command(self, cmd):
        self.executed_commands.append(cmd)
        # Mock return for specific commands if needed
        if cmd[0] == "whoami":
            return # process mock handling in real code is complex
        return

    # Mock call for whoami which uses create_subprocess_exec direclty
    # But wait, install_printer uses create_subprocess_exec for whoami?
    # Yes: proc = await asyncio.create_subprocess_exec("whoami", ...)
    # We need to patch the asyncio.create_subprocess_exec in the test method.

class TestPrinterManagement(unittest.IsolatedAsyncioTestCase):
    
    async def test_install_printer_force_overwrite(self):
        printer = MockPrinterSetup()
        
        # Mock subprocess for whoami
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            # Setup mock process for whoami
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b'testuser\n', b'')
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            # Test with Force Overwrite = True
            drivers = ["driver-package"]
            await printer.install_printer(drivers, ip_address="", force=True)
            
            # Check commands
            found_force = False
            for cmd in printer.executed_commands:
                # We are looking for the yay install command
                if cmd[0] == "yay" and "-S" in cmd:
                    print(f"Found install command: {cmd}")
                    if "--overwrite" in cmd and "*" in cmd:
                        found_force = True
            
            self.assertTrue(found_force, "Force overwrite command not found when force=True")

    async def test_install_printer_no_force(self):
        printer = MockPrinterSetup()
        
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b'testuser\n', b'')
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            # Test with Force Overwrite = False
            drivers = ["driver-package"]
            printer.executed_commands = [] # Reset
            await printer.install_printer(drivers, ip_address="", force=False)
            
            for cmd in printer.executed_commands:
                if cmd[0] == "yay" and "-S" in cmd:
                    print(f"Found install command: {cmd}")
                    if "--overwrite" in cmd:
                        self.fail(f"Found --overwrite in command when force=False: {cmd}")

    async def test_uninstall_driver(self):
        printer = MockPrinterSetup()
        drivers = ["driver-package"]
        await printer.uninstall_drivers(drivers) # This calls _run_command directly, doesn't use whoami
        
        # Check commands
        found_uninstall = False
        for cmd in printer.executed_commands:
            if cmd[0] == "yay" and "-Rns" in cmd and "driver-package" in cmd:
                print(f"Found uninstall command: {cmd}")
                found_uninstall = True
        
        self.assertTrue(found_uninstall, "Uninstall command not found")

    def test_lpstat_parsing(self):
        printer = MockPrinterSetup()
        
        sample_output = """printer Brother_DCP_L2550DW is idle.  enabled since Wed 19 Nov 2025 08:00:00 AM MST
printer HP_LaserJet disabled since Mon 01 Jan 2024 00:00:00 AM MST -
    Unplugged or turned off
printer Canon_Pixma now printing Canon_Pixma-123.  enabled since...
"""
        # Mock subprocess.run used in get_configured_printers
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = sample_output
            
            printers = printer.get_configured_printers()
            print(f"Parsed printers: {printers}")
            
            expected = [
                "Brother_DCP_L2550DW (Idle)",
                "HP_LaserJet (Disabled)",
                "Canon_Pixma (Printing)"
            ]
            
            self.assertEqual(printers, expected)

if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'GOATd/src')))

from printer import PrinterSetup
from textual.app import App
from textual.widgets import Button, SelectionList

class TestApp(App):
    def compose(self):
        yield PrinterSetup()

class TestPrinterAutoConfig(unittest.IsolatedAsyncioTestCase):
    async def test_scan_devices_success(self):
        """Test scanning devices parses lpinfo -v output correctly."""
        app = TestApp()
        
        # We use app.run_test() context manager
        async with app.run_test() as pilot:
            printer_setup = app.query_one(PrinterSetup)
            
            # Mock app log_message
            printer_setup.app.log_message = MagicMock()
            printer_setup.log_message = MagicMock()

            # Mock lpinfo -v output
            mock_stdout = b"""network socket
network beh
direct hp
network http
network ipp
direct usb://Brother/DCP-L2550DW?serial=E78234F9N2342
network dnssd://Brother%20HL-L2350DW%20series._ipp._tcp.local/
"""
            
            with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (mock_stdout, b"")
                mock_process.returncode = 0
                mock_exec.return_value = mock_process

                # Call the method directly
                # Note: In a real run_test, we might click the button, but calling method is fine too
                # if we just want to verify logic.
                # BUT, calling async method directly from here needs await
                await printer_setup.scan_devices()

                # Check if lpinfo -v was called
                mock_exec.assert_called_with('lpinfo', '-v', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

                # Check findings in driver_list
                driver_list = printer_setup.query_one("#driver_list", SelectionList)
                options = driver_list._options
                
                # We expect 2 devices
                # 1. usb://Brother/DCP-L2550DW... -> "Brother DCP-L2550DW (USB)"
                # 2. dnssd://... -> "Brother HL-L2350DW series (Network)" or similar
                
                print(f"Found options: {[opt.prompt for opt in options]}")
                
                self.assertEqual(len(options), 2)
                self.assertIn("Brother DCP-L2550DW (USB)  (direct)", str(options[0].prompt))
                self.assertIn("usb://Brother/DCP-L2550DW?serial=E78234F9N2342", options[0].value)
                
                # Check button state updates
                install_btn = printer_setup.query_one("#install_btn", Button)
                self.assertEqual(install_btn.label, "Register Selected Printer")

    async def test_auto_register_success(self):
        """Test auto registration flow."""
        app = TestApp()
        
        async with app.run_test() as pilot:
            printer_setup = app.query_one(PrinterSetup)
            printer_setup.app.log_message = MagicMock()
            printer_setup.log_message = MagicMock()
            
            # Setup dependencies
            uri = "usb://Brother/DCP-L2550DW?serial=E78234F9N2342"
            model_hint = "Brother DCP-L2550DW"
            
            # Mock lpinfo -m output
            mock_stdout_m = b"""brother-Laser-Series.ppd Brother Laser Series
brother-DCP-L2550DW-cups-en.ppd Brother DCP-L2550DW, using cups-en
generic.ppd Generic Printer
"""
            
            with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
                # Configure multiple calls
                process_m = AsyncMock()
                process_m.communicate.return_value = (mock_stdout_m, b"")
                process_m.returncode = 0
                
                process_admin = AsyncMock()
                process_admin.communicate.return_value = (b"", b"")
                process_admin.returncode = 0

                # Identify which call is which
                def side_effect(*args, **kwargs):
                    if args[0] == "lpinfo":
                        return process_m
                    elif args[1] == "lpadmin": # sudo lpadmin ...
                        return process_admin
                    elif args[0] == "whoami": # mocked for other parts if needed
                        p = AsyncMock()
                        p.communicate.return_value = (b"madgoat\n", b"")
                        return p
                    return AsyncMock()
                    
                mock_exec.side_effect = side_effect

                await printer_setup.auto_register_printer(uri, model_hint)
                
                # Verify lpinfo -m called
                calls = mock_exec.call_args_list
                self.assertTrue(any(c[0][0] == 'lpinfo' for c in calls))
                
                # Verify lpadmin called with correct PPD
                lpadmin_call = next((c for c in calls if len(c[0]) > 1 and c[0][1] == 'lpadmin'), None)
                self.assertIsNotNone(lpadmin_call)
                
                cmd_args = lpadmin_call[0]
                print(f"lpadmin called with: {cmd_args}")
                
                self.assertIn("-P", cmd_args)
                ppd_index = cmd_args.index("-P") + 1
                self.assertEqual(cmd_args[ppd_index], "brother-DCP-L2550DW-cups-en.ppd")
                
                self.assertIn("-v", cmd_args)
                uri_index = cmd_args.index("-v") + 1
                self.assertEqual(cmd_args[uri_index], uri)

if __name__ == "__main__":
    unittest.main()
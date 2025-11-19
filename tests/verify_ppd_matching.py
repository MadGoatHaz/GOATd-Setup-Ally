import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
from rich.console import Console

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'GOATd/src')))

from printer import PrinterSetup
from textual.app import App

console = Console()

class TestApp(App):
    def compose(self):
        yield PrinterSetup()

class TestPPDMatching(unittest.IsolatedAsyncioTestCase):
    async def run_test_case(self, description, model_hint, mock_lpinfo_output, expected_ppd_partial):
        console.print(f"\n[bold blue]Test Case: {description}[/]")
        console.print(f"  Model Hint: '{model_hint}'")
        
        app = TestApp()
        async with app.run_test() as pilot:
            printer_setup = app.query_one(PrinterSetup)
            printer_setup.app.log_message = MagicMock()
            printer_setup.log_message = MagicMock()
            
            # Mock subprocess calls
            with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
                # Mock process for lpinfo -m
                process_m = AsyncMock()
                process_m.communicate.return_value = (mock_lpinfo_output.encode(), b"")
                process_m.returncode = 0
                
                # Mock process for lpadmin (success)
                process_admin = AsyncMock()
                process_admin.communicate.return_value = (b"", b"")
                process_admin.returncode = 0

                def side_effect(*args, **kwargs):
                    cmd = args[0] if isinstance(args, tuple) else args
                    if args[0] == "lpinfo" and args[1] == "-m":
                        return process_m
                    elif "lpadmin" in args:
                        return process_admin
                    return AsyncMock()

                mock_exec.side_effect = side_effect

                # Run auto_register
                # URI doesn't matter much for PPD selection logic, but we provide a dummy one
                await printer_setup.auto_register_printer("ipp://192.168.1.5", model_hint)
                
                # Extract the PPD chosen from the lpadmin command
                # lpadmin -p [name] -v [uri] -P [ppd] -E
                calls = mock_exec.call_args_list
                lpadmin_call = None
                for call in calls:
                    args = call[0]
                    if len(args) > 1 and args[1] == "lpadmin":
                        lpadmin_call = args
                        break
                
                if lpadmin_call:
                    try:
                        ppd_index = lpadmin_call.index("-P") + 1
                        chosen_ppd = lpadmin_call[ppd_index]
                        if expected_ppd_partial in chosen_ppd:
                            console.print(f"[green]PASS: Selected PPD '{chosen_ppd}' contains '{expected_ppd_partial}'[/]")
                        else:
                            console.print(f"[red]FAIL: Selected PPD '{chosen_ppd}' does NOT contain '{expected_ppd_partial}'[/]")
                            self.fail(f"Wrong PPD selected: {chosen_ppd}")
                    except ValueError:
                        console.print("[red]FAIL: -P flag not found in lpadmin command[/]")
                        self.fail("lpadmin command malformed")
                else:
                    console.print("[red]FAIL: lpadmin command was never called (likely no PPD match found)[/]")
                    # Dump logs to see why
                    # print(printer_setup.log_message.call_args_list)
                    self.fail("No PPD selected")

    async def test_broad_matching(self):
        # Mock Data: A messy list of drivers
        mock_output = """
lsb/usr/HP/hp-laserjet_p1102.ppd.gz HP LaserJet Professional p1102, hpcups 3.23.5, requires proprietary plugin
gutenprint.5.3://brother-hl-2030/expert Brother HL-2030 - CUPS+Gutenprint v5.3.4
brother-DCP-L2550DW-cups-en.ppd Brother DCP-L2550DW, using cups-en
brother-HL-L2350DW-cups-en.ppd Brother HL-L2350DW, using cups-en
foomatic:Brother-HL-2170W-hl1250.ppd Brother HL-2170W Foomatic/hl1250
"""
        
        # Case 1: Exact(ish) match
        await self.run_test_case(
            "Standard Model Match",
            "Brother DCP-L2550DW",
            mock_output,
            "brother-DCP-L2550DW"
        )

        # Case 2: Case insensitive / imperfect match
        await self.run_test_case(
            "Case Insensitive / Imperfect",
            "brother dcp l2550dw",
            mock_output,
            "brother-DCP-L2550DW"
        )

        # Case 3: Substring / Model number only
        await self.run_test_case(
            "Model Number Only",
            "dcp-l2550dw",
            mock_output,
            "brother-DCP-L2550DW"
        )

    async def test_core_number_fallback(self):
        # Mock Data where exact strings don't match, but numbers do
        mock_output = """
gutenprint.5.3://brother-hl-2030/expert Brother HL-2030
brother-DCP-L2550DW-cups-en.ppd Brother DCP-L2550DW Series
"""
        # User types "Brother 2550" (missing DCP, L, DW)
        await self.run_test_case(
            "Core Number Fallback (2550)",
            "Brother 2550",
            mock_output,
            "brother-DCP-L2550DW"
        )

if __name__ == "__main__":
    print("Starting tests...")
    try:
        unittest.main(verbosity=2)
    except Exception as e:
        print(f"Error: {e}")
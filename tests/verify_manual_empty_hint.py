import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add GOATd/src to path
sys.path.append(os.path.join(os.getcwd(), 'GOATd', 'src'))

try:
    from printer import PrinterSetup
except ImportError as e:
    print(f"Error importing PrinterSetup: {e}")
    sys.exit(1)

async def verify():
    print("Setting up PrinterSetup instance...")
    
    try:
        # Instantiate the widget
        printer_setup = PrinterSetup()
        
        # Mock log_message to capture output and avoid widget lookups
        printer_setup.log_message = MagicMock()
        
        print("Running auto_register_printer with empty hint and generic URI...")
        uri = "ipp://192.168.1.5" # Generic, contains no model info
        model_hint = ""
        
        await printer_setup.auto_register_printer(uri, model_hint)
        
        # Check calls
        calls = printer_setup.log_message.call_args_list
        messages = [args[0][0] for args in calls]
        
        expected_msg = "[red]Could not identify printer model from URI. Please enter the Printer Model in the search box above and try again.[/red]"
        
        print("\nLogged Messages:")
        found = False
        for msg in messages:
            print(f"- {msg}")
            if expected_msg in msg:
                found = True
                
        if found:
            print("\nSUCCESS: Expected error message was logged.")
        else:
            print("\nFAILURE: Expected error message NOT found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"An error occurred during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
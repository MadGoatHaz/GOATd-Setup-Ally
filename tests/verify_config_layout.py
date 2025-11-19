import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "GOATd", "src"))

try:
    from config import SystemConfig, CONFIGS
    from textual.widgets import RichLog
    from textual.containers import Horizontal, Vertical
    import inspect
    from rich.markup import escape

    print("Successfully imported SystemConfig and escape.")

    # Check if SystemConfig inherits from Horizontal
    if issubclass(SystemConfig, Horizontal):
        print("SystemConfig inherits from Horizontal.")
    else:
        print("ERROR: SystemConfig does not inherit from Horizontal.")

    # Check compose method structure (static analysis)
    source = inspect.getsource(SystemConfig.compose)
    if "left-panel" in source and "right-panel" in source:
        print("SystemConfig.compose references left-panel and right-panel classes.")
    else:
        print("WARNING: SystemConfig.compose might not be using split panels correctly.")

    if "#task_log" in source:
        print("SystemConfig.compose references #task_log.")
    else:
        print("ERROR: SystemConfig.compose does not reference #task_log.")

    # Check apply_selected for escape usage
    apply_source = inspect.getsource(SystemConfig.apply_selected)
    if "escape(" in apply_source:
        print("SystemConfig.apply_selected uses escape().")
    else:
        print("ERROR: SystemConfig.apply_selected might not be escaping output.")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
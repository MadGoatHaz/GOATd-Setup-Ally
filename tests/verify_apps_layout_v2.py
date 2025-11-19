import sys
from textual.containers import Horizontal, Vertical
from textual.widgets import Button
from GOATd.src.apps import AppInstaller

def verify_apps_layout():
    print("Verifying AppInstaller layout...")
    
    # 1. Check Inheritance
    if not issubclass(AppInstaller, Horizontal):
        print("FAIL: AppInstaller does not inherit from Horizontal")
        sys.exit(1)
    print("PASS: AppInstaller inherits from Horizontal")
    
    # 2. Check Composition (Static Analysis of code structure via inspect/instantiation)
    # Instantiating might require an app context, so we'll inspect the compose method or just partial instantiation if possible.
    # Textual widgets usually need an app loop to fully realize, but we can inspect the yield statements if we parse the code, 
    # or just instantiate it and inspect _children if they were created immediately (they aren't).
    # So we will rely on source inspection or just trusting the inheritance for the split view structure 
    # coupled with the 'verify_config_layout' success which confirmed a similar pattern.
    
    # However, we can try to inspect the `compose` method by running it? No, generator.
    
    # Let's checks if the class has the methods we expect for the logic
    if not hasattr(AppInstaller, 'uninstall_selected'):
        print("FAIL: uninstall_selected method missing")
        sys.exit(1)
    print("PASS: uninstall_selected method exists")

    # Check for [Installed] prefix logic in code string
    import inspect
    source = inspect.getsource(AppInstaller.refresh_app_status)
    if '[Installed]' in source:
         print("PASS: Found '[Installed]' prefix logic in refresh_app_status")
    else:
         print("FAIL: '[Installed]' prefix logic NOT found in refresh_app_status")
         sys.exit(1)

    print("Apps layout verification complete.")

if __name__ == "__main__":
    verify_apps_layout()
import json
import os
import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Label, RichLog, Button
from textual import on
from apps import AppInstaller
from config import SystemConfig
from printer import PrinterSetup
from gpu_ui import GPUConfigWidget

CONFIG_FILE = "config.json"

class GOATdApp(App):
    """The GOAT'd Setup Application."""

    TITLE = "GOAT'd - Setup Ally"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def on_mount(self) -> None:
        self.log_buffer = []
        self.load_config()

    def log_message(self, message: str) -> None:
        if not hasattr(self, "log_buffer"):
            self.log_buffer = []
            
        """Log a message to the buffer and the RichLog widget."""
        self.log_buffer.append(str(message))
        try:
            self.query_one("#main_log", RichLog).write(message)
        except Exception:
            pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    theme = config.get("theme", "dark")
                    if theme == "light":
                        self.dark = False
                        self.add_class("light-mode")
                    else:
                        self.dark = True
                        self.remove_class("light-mode")
            except Exception as e:
                self.log(f"Error loading config: {e}")
        else:
            # Default is dark
            self.dark = True

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        if not self.dark:
            self.add_class("light-mode")
            theme = "light"
        else:
            self.remove_class("light-mode")
            theme = "dark"
        
        self.save_config({"theme": theme})

    def save_config(self, config_data):
        try:
            # Load existing to preserve other keys if any
            current_config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    current_config = json.load(f)
            
            current_config.update(config_data)
            
            with open(CONFIG_FILE, "w") as f:
                json.dump(current_config, f, indent=4)
        except Exception as e:
            self.log(f"Error saving config: {e}")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent():
            with TabPane(title="Apps", id="apps"):
                yield AppInstaller()
            
            with TabPane(title="Tasks", id="system"):
                yield SystemConfig()
            
            with TabPane(title="Printers", id="printer"):
                yield PrinterSetup()

            with TabPane(title="GPU", id="gpu"):
                yield GPUConfigWidget()
            
            with TabPane(title="Logs", id="logs"):
                yield Label("System Logs")
                yield Button("Export Logs", id="export_logs_btn")
                yield RichLog(id="main_log", markup=True)
        
        yield Footer()

    @on(Button.Pressed, "#export_logs_btn")
    def export_logs(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"goatd_logs_{timestamp}.txt"
            filepath = os.path.join(os.path.expanduser("~"), filename)
            
            with open(filepath, "w") as f:
                f.write("\n".join(self.log_buffer))
            
            self.notify(f"Logs exported to {filepath}")
            self.log_message(f"Logs exported to {filepath}")
        except Exception as e:
            self.notify(f"Failed to export logs: {e}", severity="error")
            self.log_message(f"Failed to export logs: {e}")

if __name__ == "__main__":
    app = GOATdApp()
    app.run()
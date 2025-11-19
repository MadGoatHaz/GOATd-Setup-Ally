import shutil
import subprocess
from textual.app import ComposeResult
from textual.widgets import SelectionList, Button, RichLog, Label
from textual.containers import Vertical, Horizontal
from textual import on
from rich.markup import escape

def check_nvidia():
    return shutil.which("nvidia-smi") is not None

def apply_nvidia():
    try:
        # Detect max power
        result = subprocess.run(["nvidia-smi", "-q", "-d", "POWER"], capture_output=True, text=True)
        if result.returncode != 0:
            return "Failed to query nvidia-smi"
        
        lines = result.stdout.split('\n')
        max_power = None
        for line in lines:
            if "Max Power Limit" in line:
                # Example: "        Max Power Limit           : 175.00 W"
                parts = line.split(':')
                if len(parts) > 1:
                    val_str = parts[1].strip().split(' ')[0] # 175.00
                    max_power = float(val_str)
                    break
        
        if max_power:
            # Create service file content
            service_content = f"""[Unit]
Description=Set NVIDIA Power Limit
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pl {max_power}

[Install]
WantedBy=multi-user.target
"""
            # Write service file (needs sudo)
            # We use tee to write to a root-owned location
            subprocess.run(f"echo '{service_content}' | sudo tee /etc/systemd/system/nvidia-power-limit.service", shell=True, check=True, capture_output=True)
            
            # Reload daemon and enable
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True, capture_output=True)
            res = subprocess.run(["sudo", "systemctl", "enable", "--now", "nvidia-power-limit.service"], check=True, capture_output=True, text=True)
            return f"Nvidia Power Limit set to {max_power}W and service enabled.\n{res.stdout}"
        else:
            return "Could not determine Max Power Limit."

    except Exception as e:
        return f"Error applying Nvidia config: {e}"

def apply_firewall():
    commands = [
        # Steam
        "sudo firewall-cmd --permanent --zone=public --add-port=27031/udp",
        "sudo firewall-cmd --permanent --zone=public --add-port=27036/udp",
        "sudo firewall-cmd --permanent --zone=public --add-port=27015/tcp",
        "sudo firewall-cmd --permanent --zone=public --add-port=27036/tcp",
        # KDE Connect
        "sudo firewall-cmd --permanent --zone=public --add-port=1714-1764/tcp",
        "sudo firewall-cmd --permanent --zone=public --add-port=1714-1764/udp",
        # Reload
        "sudo firewall-cmd --reload"
    ]
    output = []
    for cmd in commands:
        try:
            res = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            output.append(f"Executed: {cmd}\n{res.stdout}")
        except subprocess.CalledProcessError as e:
            # Capture output/error even on failure (though check=True raises before we can read stdout property easily from e,
            # e.stdout/e.stderr are populated if capture_output=True was used in run?)
            # Actually, CalledProcessError does have stdout/stderr attrs if captured.
            output.append(f"Failed: {cmd} ({e})\nOutput: {e.stdout}\nError: {e.stderr}")
    return "\n".join(output)

def apply_bluetooth():
    try:
        res = subprocess.run(["sudo", "systemctl", "enable", "--now", "bluetooth"], check=True, capture_output=True, text=True)
        return f"Bluetooth service enabled and started.\n{res.stdout}"
    except Exception as e:
        return f"Error enabling bluetooth: {e}"

def apply_lm_sensors():
    try:
        # --auto assumes yes to all
        res = subprocess.run(["sudo", "sensors-detect", "--auto"], check=True, capture_output=True, text=True)
        return f"lm_sensors configured (sensors-detect --auto).\n{res.stdout}"
    except Exception as e:
        return f"Error running sensors-detect: {e}"

CONFIGS = [
    {
        "id": "nvidia_power",
        "name": "Nvidia Power Limit",
        "description": "Auto-detect max power and create systemd service to persist it.",
        "check": check_nvidia,
        "apply": apply_nvidia,
        "default": False
    },
    {
        "id": "firewall_gaming",
        "name": "Firewall (Steam & KDE Connect)",
        "description": "Open ports for Steam and KDE Connect.",
        "check": lambda: shutil.which("firewall-cmd") is not None,
        "apply": apply_firewall,
        "default": True
    },
    {
        "id": "bluetooth",
        "name": "Bluetooth",
        "description": "Enable and start Bluetooth service.",
        "check": lambda: True, # Always offer if not explicitly checked
        "apply": apply_bluetooth,
        "default": True
    },
    {
        "id": "lm_sensors",
        "name": "LM Sensors",
        "description": "Run sensors-detect --auto.",
        "check": lambda: shutil.which("sensors-detect") is not None,
        "apply": apply_lm_sensors,
        "default": True
    }
]

class SystemConfig(Horizontal):
    def compose(self) -> ComposeResult:
        # Left Panel: Controls
        with Vertical(classes="left-panel"):
            selections = []
            for config in CONFIGS:
                is_applicable = True
                if config.get("check"):
                    is_applicable = config["check"]()
                
                if is_applicable:
                    selections.append(
                        (f"{config['name']} - {config['description']}", config['id'], config.get("default", False))
                    )
            
            if not selections:
                yield Label("No applicable system configurations found.")
            else:
                yield SelectionList(*selections, id="config_selection")
                yield Button("Apply Configurations", variant="primary", id="apply_config_btn")

        # Right Panel: Logs
        with Vertical(classes="right-panel"):
            yield Label("Task Execution Log")
            yield RichLog(id="task_log", markup=True, highlight=True)

    @on(Button.Pressed, "#apply_config_btn")
    def apply_selected(self):
        selection_list = self.query_one("#config_selection", SelectionList)
        selected_ids = selection_list.selected
        
        if not selected_ids:
            self.log_message("[yellow]No configurations selected.[/yellow]")
            return

        self.log_message(f"[bold]Starting batch application of {len(selected_ids)} tasks...[/bold]")
        self.log_message("-" * 40)

        for config in CONFIGS:
            if config['id'] in selected_ids:
                self.log_message(f"Applying: [cyan]{config['name']}[/cyan]...")
                try:
                    result = config['apply']()
                    # Escape the result to prevent accidental markup interpretation
                    self.log_message(escape(str(result)))
                except Exception as e:
                    self.log_message(f"[red]Error:[/red] {escape(str(e))}")
                self.log_message("-" * 20)
        
        self.log_message("[green]Batch application complete.[/green]")

    def log_message(self, message: str):
        # Log to local RichLog
        try:
            log = self.query_one("#task_log", RichLog)
            log.write(message)
        except Exception:
            pass

        # Also log to main app for history
        if hasattr(self.app, "log_message"):
            self.app.log_message(message)
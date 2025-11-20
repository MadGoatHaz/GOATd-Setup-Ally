import shutil
import subprocess
from textual.app import ComposeResult
from textual.widgets import SelectionList, Button, RichLog, Label, DataTable
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.screen import ModalScreen
from textual import on
from rich.markup import escape
from goatfetch_ui import GoatFetchScreen, TaskDescriptionScreen, FirewallSelectionScreen
from apps import get_flat_app_list

FIREWALL_SELECTIONS = {}

def detect_aur_helper():
    """Detects an available AUR helper."""
    helpers = ['paru', 'yay', 'trizen', 'pikaur', 'aura']
    for helper in helpers:
        if shutil.which(helper):
            return helper
    return None

def get_installed_packages_sync():
    try:
        res = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True)
        if res.returncode == 0:
            return set(res.stdout.splitlines())
    except Exception:
        pass
    return set()

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

def get_firewall_apps_data():
    """Returns a list of detected apps with port requirements."""
    installed_packages = get_installed_packages_sync()
    flat_apps = get_flat_app_list()
    
    detected_apps = []
    
    for app in flat_apps:
        if 'ports' in app and app['pkg'] in installed_packages:
            detected_apps.append(app)
            
    return detected_apps

def get_firewall_details():
    """Returns a string representation of firewall details for display."""
    installed_packages = get_installed_packages_sync()
    flat_apps = get_flat_app_list()
    
    details = []
    found_any = False
    
    details.append("[bold]Firewall Port Analysis:[/bold]")
    
    for app in flat_apps:
        if 'ports' in app:
            if app['pkg'] in installed_packages:
                found_any = True
                # Check if disabled by user
                is_enabled = FIREWALL_SELECTIONS.get(app['pkg'], True)
                status_color = "green" if is_enabled else "yellow"
                status_text = "Enabled" if is_enabled else "Disabled by User"
                
                ports_str = ", ".join(app['ports'])
                details.append(f"[{status_color}]Detected: {app['name']} ({status_text})[/{status_color}]")
                details.append(f"  - Ports: {ports_str}")
            else:
                details.append(f"[dim]Not Detected: {app['name']} (would open {', '.join(app['ports'])})[/dim]")
                
    if not found_any:
        details.append("\n[yellow]No apps detected that require special port configurations.[/yellow]")
        
    return "\n".join(details)

def apply_firewall():
    installed_packages = get_installed_packages_sync()
    flat_apps = get_flat_app_list()

    commands = []
    detected_msg = []
    
    for app in flat_apps:
        if app['pkg'] in installed_packages and 'ports' in app:
            # Check if user deselected this app in Firewall Selection Screen
            if not FIREWALL_SELECTIONS.get(app['pkg'], True):
                detected_msg.append(f"[dim]Skipping {app['name']} (User disabled)[/dim]")
                continue

            detected_msg.append(f"Detected {app['name']}. Opening ports: {', '.join(app['ports'])}")
            for port in app['ports']:
                commands.append(f"sudo firewall-cmd --permanent --zone=public --add-port={port}")

    if not commands:
        return "No installed applications found that require specific firewall ports."

    # Reload
    commands.append("sudo firewall-cmd --reload")

    output = []
    if detected_msg:
        output.append("\n".join(detected_msg))
        output.append("-" * 20)

    for cmd in commands:
        try:
            res = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            output.append(f"Executed: {cmd}")
        except subprocess.CalledProcessError as e:
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

def apply_system_update():
    try:
        res = subprocess.run(["sudo", "pacman", "-Syu", "--noconfirm"], check=True, capture_output=True, text=True)
        return f"System updated successfully.\n{res.stdout}"
    except Exception as e:
        return f"Error updating system: {e}"

def apply_printer_setup():
    try:
        # Install cups if not present (basic check)
        cmds = [
            "sudo pacman -S --noconfirm cups gutenprint",
            "sudo systemctl enable --now cups.service"
        ]
        output = []
        for cmd in cmds:
            res = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            output.append(f"Executed: {cmd}")
        return "\n".join(output)
    except Exception as e:
        return f"Error setting up printer: {e}"

CONFIGS = [
    {
        "id": "system_update",
        "name": "System Update",
        "description": "Updates all system packages.",
        "steps": ["Execute `sudo pacman -Syu`"],
        "check": lambda: True,
        "apply": apply_system_update,
        "default": True
    },
    {
        "id": "nvidia_power",
        "name": "Nvidia Power Limit",
        "description": "Creates systemd service to set power limit.",
        "steps": [
            "Detect Max Power Limit via `nvidia-smi -q -d POWER`",
            "Creates systemd service to set power limit",
            "Service file: /etc/systemd/system/nvidia-power-limit.service",
            "Enable and start the service"
        ],
        "check": check_nvidia,
        "apply": apply_nvidia,
        "default": False
    },
    {
        "id": "firewall_gaming",
        "name": "Firewall",
        "description": "Scans for installed apps and opens specific ports using `firewall-cmd`.",
        "steps": [
            "Scan installed applications for known ports",
            "Execute `sudo firewall-cmd --permanent --zone=public --add-port=[PORT]`",
            "Execute `sudo firewall-cmd --reload`"
        ],
        "check": lambda: shutil.which("firewall-cmd") is not None,
        "apply": apply_firewall,
        "default": True
    },
    {
        "id": "bluetooth",
        "name": "Bluetooth",
        "description": "Enable and start `bluetooth.service`.",
        "steps": ["Enable and start `bluetooth.service`"],
        "check": lambda: True, # Always offer if not explicitly checked
        "apply": apply_bluetooth,
        "default": True
    },
    {
        "id": "printer_setup",
        "name": "Printer Setup",
        "description": "Installs CUPS/Drivers and enables `cups.service`.",
        "steps": [
            "Install CUPS packages",
            "Enable and start `cups.service`"
        ],
        "check": lambda: True,
        "apply": apply_printer_setup,
        "default": True
    },
    {
        "id": "lm_sensors",
        "name": "LM Sensors",
        "description": "Execute `sudo sensors-detect --auto`",
        "steps": ["Execute `sudo sensors-detect --auto`"],
        "check": lambda: shutil.which("sensors-detect") is not None,
        "apply": apply_lm_sensors,
        "default": True
    },
    {
        "id": "goatfetch",
        "name": "GoatFetch Configuration",
        "description": "Interactive FastFetch theme manager.",
        "steps": ["Launch interactive theme manager"],
        "check": lambda: True,
        "apply": lambda: "GoatFetch Launched", # Dummy apply
        "default": False,
        "interactive": True
    }
]

# TaskDescriptionScreen and FirewallSelectionScreen moved to goatfetch_ui.py

class SystemConfig(Horizontal):
    def compose(self) -> ComposeResult:
        # Left Panel: Controls
        with Vertical(classes="left-panel"):
            yield Label("System Tasks", id="tasks_title")
            yield Label("Click checkbox to toggle. Click name for details.", classes="instruction_label")
            
            # Replaced SelectionList with DataTable
            with Horizontal(classes="selection-buttons"):
                yield Button("Select All", id="btn_config_select_all", variant="primary")
                yield Button("Deselect All", id="btn_config_deselect_all", variant="error")

            yield DataTable(id="config_table", cursor_type="cell")
            
            yield Button("Apply Selected Tasks", variant="primary", id="apply_config_btn")

        # Right Panel: Logs
        with Vertical(classes="right-panel"):
            yield Label("Task Execution Log")
            yield RichLog(id="task_log", markup=True, highlight=True)

    def on_mount(self):
        table = self.query_one("#config_table", DataTable)
        table.add_column("Select", key="Select")
        table.add_column("Task Name", key="Task Name")
        table.add_column("Description", key="Description")
        
        for config in CONFIGS:
            is_applicable = True
            if config.get("check"):
                is_applicable = config["check"]()
            
            if is_applicable:
                default_val = config.get("default", False)
                check_mark = r"\[x]" if default_val else r"\[ ]"
                
                table.add_row(
                    check_mark,
                    config['name'],
                    config['description'],
                    key=config['id']
                )

    @on(DataTable.CellSelected, "#config_table")
    def on_cell_selected(self, event: DataTable.CellSelected):
        row_key = event.cell_key.row_key.value
        
        if event.coordinate.column == 0:
            # Toggle selection
            table = event.data_table
            current_val = table.get_cell_at(event.coordinate)
            new_val = r"\[ ]" if r"\[x]" in str(current_val) else r"\[x]"
            table.update_cell_at(event.coordinate, new_val)
        else:
            # Show details
            config = next((c for c in CONFIGS if c['id'] == row_key), None)
            
            if row_key == "firewall_gaming":
                detected_apps = get_firewall_apps_data()
                self.app.push_screen(FirewallSelectionScreen(detected_apps, FIREWALL_SELECTIONS))
            elif config:
                self.app.push_screen(TaskDescriptionScreen(
                    config['name'],
                    config['description'],
                    steps=config.get('steps')
                ))

    @on(Button.Pressed, "#btn_config_select_all")
    def select_all_configs(self):
        table = self.query_one("#config_table", DataTable)
        for row_key in table.rows:
            table.update_cell(row_key, "Select", r"\[x]")

    @on(Button.Pressed, "#btn_config_deselect_all")
    def deselect_all_configs(self):
        table = self.query_one("#config_table", DataTable)
        for row_key in table.rows:
            table.update_cell(row_key, "Select", r"\[ ]")

    @on(Button.Pressed, "#apply_config_btn")
    def apply_selected(self):
        table = self.query_one("#config_table", DataTable)
        selected_ids = []
        
        for row_key in table.rows:
            # Column 0 is Select
            select_cell = table.get_cell(row_key, "Select")
            if r"\[x]" in str(select_cell):
                selected_ids.append(row_key.value)
        
        if not selected_ids:
            self.log_message("[yellow]No configurations selected.[/yellow]")
            return

        self.log_message(f"[bold]Starting batch application of {len(selected_ids)} tasks...[/bold]")
        self.log_message("-" * 40)

        for config in CONFIGS:
            if config['id'] in selected_ids:
                self.log_message(f"Applying: [cyan]{config['name']}[/cyan]...")
                
                if config.get("interactive"):
                    # Launch interactive screen
                    self.app.push_screen(GoatFetchScreen())
                    self.log_message("Launched interactive configuration.")
                else:
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
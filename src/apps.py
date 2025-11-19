import asyncio
import subprocess
from textual.app import ComposeResult
from textual.widgets import Static, SelectionList, Button, RichLog, ProgressBar, Label
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual import on, work

class SummaryScreen(Screen):
    def __init__(self, installed_items: list[str]):
        super().__init__()
        self.installed_items = installed_items

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Installation Summary", id="summary_title"),
            Static("\n".join(self.installed_items) if self.installed_items else "No packages installed.", id="summary_list"),
            Button("Close", variant="primary", id="close_summary_btn"),
            id="summary_container"
        )

    @on(Button.Pressed, "#close_summary_btn")
    def close_screen(self):
        self.dismiss()

# Application Definitions
APPLICATIONS = [
    # Pacman Apps
    {"id": "btrfs-progs", "name": "BTRFS Progs", "description": "BTRFS filesystem utilities", "command": "btrfs-progs", "manager": "pacman", "default": True},
    {"id": "code", "name": "VS Code", "description": "Visual Studio Code", "command": "code", "manager": "pacman", "default": True},
    {"id": "cpu-x", "name": "CPU-X", "description": "System profiling application", "command": "cpu-x", "manager": "pacman", "default": False},
    {"id": "fastfetch", "name": "Fastfetch", "description": "System information tool", "command": "fastfetch", "manager": "pacman", "default": True},
    {"id": "git", "name": "Git", "description": "Version control system", "command": "git", "manager": "pacman", "default": True},
    {"id": "github-cli", "name": "GitHub CLI", "description": "Command line interface for GitHub", "command": "github-cli", "manager": "pacman", "default": True},
    {"id": "kdiskmark", "name": "KDiskMark", "description": "HDD/SSD benchmarking tool", "command": "kdiskmark", "manager": "pacman", "default": False},
    {"id": "mission-center", "name": "Mission Center", "description": "System monitor", "command": "mission-center", "manager": "pacman", "default": False},
    {"id": "remmina", "name": "Remmina", "description": "Remote desktop client", "command": "remmina", "manager": "pacman", "default": False},
    {"id": "steam", "name": "Steam", "description": "Digital distribution platform", "command": "steam", "manager": "pacman", "default": False},
    {"id": "lm_sensors", "name": "lm_sensors", "description": "Hardware monitoring", "command": "lm_sensors", "manager": "pacman", "default": True},
    {"id": "kdeconnect", "name": "KDE Connect", "description": "Device integration", "command": "kdeconnect", "manager": "pacman", "default": False},
    {"id": "freecad", "name": "FreeCAD", "description": "Parametric 3D modeler", "command": "freecad", "manager": "pacman", "default": False},
    {"id": "openrgb", "name": "OpenRGB", "description": "RGB lighting control", "command": "openrgb", "manager": "pacman", "default": False},
    {"id": "partitionmanager", "name": "KDE Partition Manager", "description": "Partition editor", "command": "partitionmanager", "manager": "pacman", "default": False},
    {"id": "qbittorrent", "name": "qBittorrent", "description": "BitTorrent client", "command": "qbittorrent", "manager": "pacman", "default": True},
    {"id": "picard", "name": "MusicBrainz Picard", "description": "Music tagger", "command": "picard", "manager": "pacman", "default": False},
    {"id": "simple-scan", "name": "Simple Scan", "description": "Document scanner", "command": "simple-scan", "manager": "pacman", "default": True},
    
    # Yay Apps
    {"id": "brave-bin", "name": "Brave Browser", "description": "Privacy-focused browser", "command": "brave-bin", "manager": "yay", "default": True},
    {"id": "coolercontrol-bin", "name": "CoolerControl", "description": "Cooling device control", "command": "coolercontrol-bin", "manager": "yay", "default": False},
    {"id": "orca-slicer-bin", "name": "Orca Slicer", "description": "G-code generator for 3D printers", "command": "orca-slicer-bin", "manager": "yay", "default": False},
    {"id": "qdiskinfo-bin", "name": "QDiskInfo", "description": "Storage drive health monitoring", "command": "qdiskinfo-bin", "manager": "yay", "default": False},
    {"id": "proton-vpn-gtk-app", "name": "Proton VPN", "description": "VPN Client", "command": "proton-vpn-gtk-app", "manager": "yay", "default": False},
]

class AppInstaller(Vertical):
    def compose(self) -> ComposeResult:
        selections = [
            (f"{app['name']} ({app['manager']}) - {app['description']}", app['id'], app['default'])
            for app in APPLICATIONS
        ]
        yield SelectionList(*selections, id="app_selection")
        yield Label("", id="install_status")
        yield ProgressBar(total=100, show_eta=False, id="install_progress")
        yield Button("Install Selected", variant="primary", id="install_btn")

    def on_mount(self):
        self.query_one("#install_progress", ProgressBar).display = False

    @on(Button.Pressed, "#install_btn")
    def install_selected(self):
        selection_list = self.query_one("#app_selection", SelectionList)
        selected_ids = selection_list.selected
        
        if not selected_ids:
            self.log_message("No applications selected.")
            return

        self.query_one("#install_btn", Button).disabled = True
        self.query_one("#install_progress", ProgressBar).display = True
        self.run_installation(selected_ids)

    @work(exclusive=True)
    async def run_installation(self, selected_ids):
        progress_bar = self.query_one("#install_progress", ProgressBar)
        status_label = self.query_one("#install_status", Label)
        
        pacman_apps = []
        yay_apps = []

        for app in APPLICATIONS:
            if app['id'] in selected_ids:
                if app['manager'] == "pacman":
                    pacman_apps.append(app['command'])
                elif app['manager'] == "yay":
                    yay_apps.append(app['command'])

        total_steps = (1 if pacman_apps else 0) + (1 if yay_apps else 0)
        progress_bar.update(total=total_steps, progress=0)
        
        installed_log = []
        current_step = 0

        if pacman_apps:
            status_label.update("Installing Pacman packages...")
            success = await self.install_packages("pacman", pacman_apps)
            if success:
                installed_log.append(f"Pacman: {', '.join(pacman_apps)}")
            current_step += 1
            progress_bar.update(progress=current_step)
        
        if yay_apps:
            status_label.update("Installing Yay packages...")
            success = await self.install_packages("yay", yay_apps)
            if success:
                installed_log.append(f"Yay: {', '.join(yay_apps)}")
            current_step += 1
            progress_bar.update(progress=current_step)

        status_label.update("Installation complete.")
        self.query_one("#install_btn", Button).disabled = False
        progress_bar.display = False
        
        self.app.push_screen(SummaryScreen(installed_log))

    async def install_packages(self, manager: str, packages: list[str]) -> bool:
        cmd = []
        if manager == "pacman":
            cmd = ["sudo", "pacman", "-S", "--noconfirm"] + packages
        elif manager == "yay":
            cmd = ["yay", "-S", "--noconfirm"] + packages

        cmd_str = " ".join(cmd)
        self.log_message(f"Running: {cmd_str}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                self.log_message(stdout.decode())
            if stderr:
                self.log_message(f"Error/Warning: {stderr.decode()}")
                
            if process.returncode == 0:
                self.log_message(f"Successfully installed {manager} packages.")
                return True
            else:
                self.log_message(f"Failed to install {manager} packages. Return code: {process.returncode}")
                return False

        except Exception as e:
            self.log_message(f"Exception during installation: {str(e)}")
            return False

    def log_message(self, message: str):
        if hasattr(self.app, "log_message"):
            self.app.log_message(message)
        else:
            # Fallback for testing or if app doesn't have log_message
            try:
                rich_log = self.app.query_one("#main_log", RichLog)
                rich_log.write(message)
            except Exception:
                print(message)
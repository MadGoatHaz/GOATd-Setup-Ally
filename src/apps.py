import asyncio
import subprocess
from textual.app import ComposeResult
from textual.widgets import Static, SelectionList, Button, RichLog, ProgressBar, Label
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual import on, work

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

class AppInstaller(Horizontal):
    def compose(self) -> ComposeResult:
        # Left Panel: App List & Actions
        with Vertical(classes="left-panel"):
            yield Label("Select Applications", id="app_list_title")
            # We will populate options in on_mount after checking status
            yield SelectionList(id="app_selection")
            
            yield Label("", id="install_status")
            yield ProgressBar(total=100, show_eta=False, id="install_progress")
            
            with Horizontal(id="app_actions"):
                yield Button("Install Selected", variant="primary", id="install_btn")
                yield Button("Uninstall Selected", variant="error", id="uninstall_btn")

        # Right Panel: Logs
        with Vertical(classes="right-panel"):
            yield Label("Installation Log")
            yield RichLog(id="app_log", markup=True, highlight=True)

    def on_mount(self):
        self.query_one("#install_progress", ProgressBar).display = False
        self.run_worker(self.refresh_app_status(), exclusive=True)

    async def refresh_app_status(self):
        """Check installed status of all apps and populate the list."""
        self.log_message("Checking installed applications...")
        selection_list = self.query_one("#app_selection", SelectionList)
        selection_list.clear_options()
        
        installed_packages = await self.get_installed_packages()
        
        options = []
        for app in APPLICATIONS:
            is_installed = False
            # Check if the 'command' (package name) is in our installed list
            # Note: 'command' in APPLICATIONS dict seems to act as package name based on install logic
            if app['command'] in installed_packages:
                is_installed = True
            
            # Escape brackets to prevent Rich from interpreting as style tag
            status_prefix = r"\[Installed] " if is_installed else ""
            label = f"{status_prefix}{app['name']} ({app['manager']}) - {app['description']}"
            
            # Default selection: Select if Default AND Not Installed
            should_select = app['default'] and not is_installed
            
            options.append((label, app['id'], should_select))
            
        selection_list.add_options(options)
        self.log_message("[green]Application list updated.[/green]")

    async def get_installed_packages(self) -> set[str]:
        """Return a set of all installed packages (pacman + yay)."""
        # We can just run `pacman -Qq` to get all locally installed packages
        # yay wraps pacman, so `pacman -Qq` covers everything usually.
        try:
            proc = await asyncio.create_subprocess_exec(
                "pacman", "-Qq",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                return set(stdout.decode().splitlines())
        except Exception:
            pass
        return set()

    @on(Button.Pressed, "#install_btn")
    def install_selected(self):
        selection_list = self.query_one("#app_selection", SelectionList)
        selected_ids = selection_list.selected
        
        if not selected_ids:
            self.log_message("[yellow]No applications selected for installation.[/yellow]")
            return

        self.query_one("#install_btn", Button).disabled = True
        self.query_one("#uninstall_btn", Button).disabled = True
        self.query_one("#install_progress", ProgressBar).display = True
        
        self.run_worker(self.run_installation(selected_ids), exclusive=True)

    @on(Button.Pressed, "#uninstall_btn")
    def uninstall_selected(self):
        selection_list = self.query_one("#app_selection", SelectionList)
        selected_ids = selection_list.selected
        
        if not selected_ids:
            self.log_message("[yellow]No applications selected for uninstall.[/yellow]")
            return

        self.query_one("#install_btn", Button).disabled = True
        self.query_one("#uninstall_btn", Button).disabled = True
        self.query_one("#install_progress", ProgressBar).display = True
        
        self.run_worker(self.run_uninstallation(selected_ids), exclusive=True)

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
        
        current_step = 0

        if pacman_apps:
            status_label.update("Installing Pacman packages...")
            await self.install_packages("pacman", pacman_apps)
            current_step += 1
            progress_bar.update(progress=current_step)
        
        if yay_apps:
            status_label.update("Installing Yay packages...")
            await self.install_packages("yay", yay_apps)
            current_step += 1
            progress_bar.update(progress=current_step)

        status_label.update("Installation complete.")
        self.query_one("#install_btn", Button).disabled = False
        self.query_one("#uninstall_btn", Button).disabled = False
        progress_bar.display = False
        
        # Refresh list to update [Installed] tags
        await self.refresh_app_status()

    async def run_uninstallation(self, selected_ids):
        progress_bar = self.query_one("#install_progress", ProgressBar)
        status_label = self.query_one("#install_status", Label)
        
        # Group by manager for efficiency, though uninstall is usually just pacman -Rns
        apps_to_remove = []
        
        for app in APPLICATIONS:
            if app['id'] in selected_ids:
                apps_to_remove.append(app['command'])

        if not apps_to_remove:
            return

        progress_bar.update(total=1, progress=0)
        status_label.update("Uninstalling packages...")
        
        # Use yay for everything to be safe (it handles AUR uninstalls too)
        # -Rns: Remove recursive, nosave (cleaner uninstall)
        cmd = ["yay", "-Rns", "--noconfirm"] + apps_to_remove
        cmd_str = " ".join(cmd)
        self.log_message(f"Running: {cmd_str}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout: self.log_message(stdout.decode())
            if stderr: self.log_message(f"[yellow]{stderr.decode()}[/yellow]")
            
            if process.returncode == 0:
                self.log_message("[green]Successfully uninstalled packages.[/green]")
            else:
                self.log_message(f"[red]Failed to uninstall packages. Code: {process.returncode}[/red]")

        except Exception as e:
            self.log_message(f"[red]Error: {str(e)}[/red]")

        progress_bar.update(progress=1)
        status_label.update("Uninstallation complete.")
        self.query_one("#install_btn", Button).disabled = False
        self.query_one("#uninstall_btn", Button).disabled = False
        progress_bar.display = False
        
        await self.refresh_app_status()

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
        # Local log
        try:
            log = self.query_one("#app_log", RichLog)
            log.write(message)
        except Exception:
            pass

        # Global log
        if hasattr(self.app, "log_message"):
            self.app.log_message(message)
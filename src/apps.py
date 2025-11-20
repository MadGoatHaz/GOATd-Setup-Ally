import asyncio
import subprocess
from textual.app import ComposeResult
from textual.widgets import Static, SelectionList, Button, RichLog, ProgressBar, Label, DataTable
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.screen import ModalScreen
from textual import on, work
from textual.binding import Binding
from goatfetch_ui import UninstallConfirmationScreen, UninstallSafetyScreen

# Application Definitions (New Structure)
APPS_CATEGORIES = {
    "Terminal & Command Line": {
        "Kitty": {"pkg": "kitty", "source": "pacman", "tier": "God Tier", "description": "GPU-accelerated, scriptable terminal emulator. Supports images, ligatures, and tiling."},
        "Alacritty": {"pkg": "alacritty", "source": "pacman", "tier": "Top Tier", "description": "GPU-accelerated terminal emulator focused on performance and simplicity."},
        "Tilix": {"pkg": "tilix", "source": "pacman", "tier": "Standard", "description": "Tiling terminal emulator using GTK3. Supports splitting panes and adhering to system themes."},
        "Zellij": {"pkg": "zellij", "source": "pacman", "tier": "God Tier", "description": "Terminal multiplexer with a built-in layout system and user-friendly interface."},
        "Tmux": {"pkg": "tmux", "source": "pacman", "tier": "Classic", "description": "Terminal multiplexer for managing multiple terminal sessions. Useful for remote sessions."},
        "Starship": {"pkg": "starship", "source": "pacman", "tier": "Top Tier", "description": "Cross-shell prompt customizable via configuration file."},
        "FastFetch": {"pkg": "fastfetch", "source": "pacman", "tier": "Essential", "description": "System information tool, displays system logos and information."},
        "Fish Shell": {"pkg": "fish", "source": "pacman", "tier": "Magic", "description": "Command line shell with autosuggestions and syntax highlighting."},
    },
    "Modern Unix Tools (CLI)": {
        "Ripgrep (rg)": {"pkg": "ripgrep", "source": "pacman", "tier": "God Tier", "description": "Line-oriented search tool that recursively searches the current directory for a regex pattern."},
        "FZF": {"pkg": "fzf", "source": "pacman", "tier": "Magic", "description": "Command-line fuzzy finder for searching history, files, or processes."},
        "Bat": {"pkg": "bat", "source": "pacman", "tier": "Top Tier", "description": "Cat clone with syntax highlighting and Git integration."},
        "Eza": {"pkg": "eza", "source": "pacman", "tier": "Top Tier", "description": "Modern replacement for ls with color support and Git integration."},
        "Htop": {"pkg": "htop", "source": "pacman", "tier": "Classic", "description": "Interactive process viewer."},
        "Rsync": {"pkg": "rsync", "source": "pacman", "tier": "Core", "description": "Fast, versatile, remote (and local) file-copying tool."},
    },
    "Creative Studio": {
        "Blender": {"pkg": "blender", "source": "pacman", "tier": "God Tier", "description": "3D creation suite supporting modeling, rigging, animation, simulation, rendering, compositing, and motion tracking."},
        "Plasticity": {"pkg": "plasticity-bin", "source": "aur", "tier": "Top Tier", "description": "NURBS-based 3D modeling software optimized for artists."},
        "Krita": {"pkg": "krita", "source": "pacman", "tier": "God Tier", "description": "Digital painting and 2D animation application."},
        "MyPaint": {"pkg": "mypaint", "source": "pacman", "tier": "Painting", "description": "Raster graphics editor for digital painters."},
        "Inkscape": {"pkg": "inkscape", "source": "pacman", "tier": "Essential", "description": "Vector graphics editor for creating SVGs, logos, and illustrations."},
        "GIMP": {"pkg": "gimp", "source": "pacman", "tier": "Essential", "description": "Raster graphics editor for image manipulation and editing."},
        "Darktable": {"pkg": "darktable", "source": "pacman", "tier": "Photo", "description": "Photography workflow application and raw developer."},
        "FreeCAD": {"pkg": "freecad", "source": "pacman", "tier": "Pro", "description": "Parametric 3D modeler for designing real-life objects."},
        "Orca Slicer": {"pkg": "orca-slicer-bin", "source": "aur", "tier": "Top Tier", "description": "G-code generator for 3D printers, fork of Bambu Studio/PrusaSlicer."},
    },
    "Media Production": {
        "DaVinci Resolve": {"pkg": "davinci-resolve", "source": "aur", "tier": "God Tier", "description": "Video editing, color correction, visual effects, and audio post-production application."},
        "Kdenlive": {"pkg": "kdenlive", "source": "pacman", "tier": "Essential", "description": "Non-linear video editor based on MLT Framework and KDE Frameworks."},
        "Parabolic": {"pkg": "parabolic", "source": "aur", "tier": "Top Tier", "description": "Graphical frontend for yt-dlp to download video/audio."},
        "OBS Studio": {"pkg": "obs-studio", "source": "pacman", "tier": "God Tier", "description": "Software for video recording and live streaming.", "ports": ["4455/tcp"]},
        "Audacity": {"pkg": "audacity", "source": "pacman", "tier": "Essential", "description": "Digital audio editor and recording application."},
        "Ardour": {"pkg": "ardour", "source": "pacman", "tier": "Pro", "description": "Digital Audio Workstation (DAW) for recording, editing, and mixing."},
        "LMMS": {"pkg": "lmms", "source": "pacman", "tier": "Music", "description": "Digital Audio Workstation for producing music."},
        "HandBrake": {"pkg": "handbrake", "source": "pacman", "tier": "Utility", "description": "Video transcoder for converting video from nearly any format."},
        "Strawberry": {"pkg": "strawberry", "source": "pacman", "tier": "Music", "description": "Music player and music collection organizer."},
        "MusicBrainz Picard": {"pkg": "picard", "source": "pacman", "tier": "Magic", "description": "Music tagger using the MusicBrainz database."},
        "MPV": {"pkg": "mpv", "source": "pacman", "tier": "Top Tier", "description": "Command-line media player."},
        "VLC": {"pkg": "vlc", "source": "pacman", "tier": "Reliable", "description": "Multimedia player and framework that plays most multimedia files."},
    },
    "System Utilities": {
        "Mission Center": {"pkg": "mission-center", "source": "pacman", "tier": "Top Tier", "description": "System monitor showing CPU, Memory, Disk, and Network usage."},
        "OCCT": {"pkg": "occt", "source": "pacman", "tier": "Top Tier", "description": "Stability checking tool for CPU, GPU, and RAM."},
        "Btrfs Assistant": {"pkg": "btrfs-assistant", "source": "pacman", "tier": "God Tier", "description": "GUI for managing Btrfs filesystems and Snapper snapshots."},
        "Timeshift": {"pkg": "timeshift", "source": "pacman", "tier": "Savior", "description": "System restore utility using rsync or Btrfs snapshots."},
        "KDE Partition Manager": {"pkg": "partitionmanager", "source": "pacman", "tier": "Pro", "description": "Utility to manage disk devices, partitions, and file systems."},
        "GParted": {"pkg": "gparted", "source": "pacman", "tier": "Classic", "description": "Partition editor for graphically managing disk partitions."},
        "KDiskMark": {"pkg": "kdiskmark", "source": "pacman", "tier": "Bench", "description": "Disk benchmarking tool."},
        "QDiskInfo": {"pkg": "qdiskinfo-bin", "source": "aur", "tier": "Health", "description": "Storage drive health monitoring tool using S.M.A.R.T."},
        "BleachBit": {"pkg": "bleachbit", "source": "pacman", "tier": "Cleaner", "description": "System cleaner to free space and maintain privacy."},
        "PeaZip": {"pkg": "peazip-qt", "source": "pacman", "tier": "Utility", "description": "File manager and archiver supporting many formats."},
        "KeePassXC": {"pkg": "keepassxc", "source": "pacman", "tier": "Security", "description": "Offline password manager."},
        "Firejail": {"pkg": "firejail", "source": "pacman", "tier": "Security", "description": "SUID sandbox program to restrict the running environment of applications."},
    },
    "Hardware Control": {
        "CoolerControl": {"pkg": "coolercontrol-bin", "source": "aur", "tier": "Top Tier", "description": "GUI to view sensors and control fans/pumps with custom curves."},
        "CoreCtrl": {"pkg": "corectrl", "source": "pacman", "tier": "Pro", "description": "Application to control computer hardware settings (mainly AMD GPUs)."},
        "OpenRGB": {"pkg": "openrgb", "source": "pacman", "tier": "RGB", "description": "RGB lighting control software.", "ports": ["6742/tcp"]},
        "KDE Connect": {"pkg": "kdeconnect", "source": "pacman", "tier": "Magic", "description": "Integration tool for connecting devices to share clipboard, files, and notifications.", "ports": ["1714-1764/tcp", "1714-1764/udp"]},
        "Input Remapper": {"pkg": "input-remapper-git", "source": "aur", "tier": "Utility", "description": "Tool to remap input device buttons and keys."},
        "lm_sensors": {"pkg": "lm_sensors", "source": "pacman", "tier": "Core", "description": "Tools to read temperature, voltage, and fan sensors."},
        "CPU-X": {"pkg": "cpu-x", "source": "pacman", "tier": "Pro", "description": "System profiling and monitoring application."},
    },
    "Productivity & Office": {
        "Obsidian": {"pkg": "obsidian", "source": "aur", "tier": "God Tier", "description": "Markdown-based note-taking and knowledge base application."},
        "Joplin": {"pkg": "joplin", "source": "pacman", "tier": "Open", "description": "Note-taking and to-do application with synchronization capabilities."},
        "Xournal++": {"pkg": "xournalpp", "source": "pacman", "tier": "Ink", "description": "Handwriting note-taking software with PDF annotation support."},
        "OnlyOffice": {"pkg": "onlyoffice-bin", "source": "aur", "tier": "Top Tier", "description": "Office suite compatible with Microsoft Office formats."},
        "LibreOffice": {"pkg": "libreoffice-fresh", "source": "pacman", "tier": "Standard", "description": "Free and open-source office productivity suite."},
        "Thunderbird": {"pkg": "thunderbird", "source": "pacman", "tier": "Classic", "description": "Email, news, and chat client."},
        "Okular": {"pkg": "okular", "source": "pacman", "tier": "God Tier", "description": "Universal document viewer."},
        "Foliate": {"pkg": "foliate", "source": "pacman", "tier": "Reading", "description": "E-book reader supporting .epub, .mobi, .azw, and more."},
        "Zathura": {"pkg": "zathura", "source": "pacman", "tier": "Minimal", "description": "Document viewer with a minimalist interface."},
        "XMind": {"pkg": "xmind", "source": "aur", "tier": "MindMap", "description": "Mind mapping and brainstorming software."},
    },
    "Development": {
        "Code (OSS)": {"pkg": "code", "source": "pacman", "tier": "God Tier", "description": "Open source build of Visual Studio Code."},
        "PyCharm": {"pkg": "pycharm-community-edition", "source": "pacman", "tier": "Python", "description": "Python IDE."},
        "Git": {"pkg": "git", "source": "pacman", "tier": "Core", "description": "Distributed version control system."},
        "GitHub CLI": {"pkg": "github-cli", "source": "pacman", "tier": "Utility", "description": "Command line interface for GitHub."},
        "Docker": {"pkg": "docker", "source": "pacman", "tier": "Container", "description": "Platform for developing, shipping, and running applications in containers."},
        "Meld": {"pkg": "meld", "source": "pacman", "tier": "Visual", "description": "Visual diff and merge tool."},
    },
    "Virtualization": {
        "Virt-Manager": {"pkg": "virt-manager", "source": "pacman", "tier": "God Tier", "description": "Desktop user interface for managing virtual machines via libvirt.", "ports": ["5900-5905/tcp"]},
        "VirtualBox": {"pkg": "virtualbox", "source": "pacman", "tier": "Easy", "description": "General-purpose full virtualizer for x86 hardware."},
    },
    "Internet & Networking": {
        "Brave Browser": {"pkg": "brave-bin", "source": "aur", "tier": "Privacy", "description": "Privacy-focused web browser."},
        "Vivaldi": {"pkg": "vivaldi", "source": "pacman", "tier": "Power", "description": "Customizable web browser."},
        "Tor Browser": {"pkg": "tor-browser-bin", "source": "aur", "tier": "Anon", "description": "Web browser for accessing the Tor network."},
        "qBittorrent": {"pkg": "qbittorrent", "source": "pacman", "tier": "Essential", "description": "BitTorrent client.", "ports": ["8080/tcp"]},
        "Proton VPN": {"pkg": "proton-vpn-gtk-app", "source": "aur", "tier": "Security", "description": "VPN client."},
        "Remmina": {"pkg": "remmina", "source": "pacman", "tier": "Remote", "description": "Remote desktop client. Supports RDP, VNC, SSH, and SPICE protocols."},
    },
    "Gaming": {
        "Steam": {"pkg": "steam", "source": "pacman", "tier": "God Tier", "description": "Video game digital distribution service and storefront.", "ports": ["27031/udp", "27036/tcp", "27036/udp", "27037/tcp", "27015/tcp"]},
        "Heroic Launcher": {"pkg": "heroic-games-launcher-bin", "source": "aur", "tier": "Top Tier", "description": "Game launcher for Epic Games and GOG."},
        "Lutris": {"pkg": "lutris", "source": "pacman", "tier": "Utility", "description": "Open gaming platform."},
        "Prism Launcher": {"pkg": "prism-launcher", "source": "pacman", "tier": "Minecraft", "description": "Minecraft launcher with multiple instance support."},
    }
}

# Helper to flatten APPS_CATEGORIES for easier processing by installer
def get_flat_app_list():
    flat_list = []
    for category, apps in APPS_CATEGORIES.items():
        for app_name, app_details in apps.items():
            app_copy = app_details.copy()
            app_copy['name'] = app_name
            app_copy['category'] = category
            # Create a unique ID
            app_copy['id'] = app_details['pkg']
            flat_list.append(app_copy)
    return flat_list

class AppDescriptionScreen(ModalScreen):
    """Modal screen to show application details."""
    
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, app_data):
        super().__init__()
        self.app_data = app_data

    def compose(self) -> ComposeResult:
        with Vertical(id="app_desc_container"):
            yield Label(self.app_data['name'], id="app_desc_title")
            
            with Grid(id="app_desc_grid"):
                yield Label("Category:", classes="desc-label")
                yield Label(self.app_data.get('category', 'Unknown'), classes="desc-value")
                
                yield Label("Source:", classes="desc-label")
                yield Label(self.app_data['source'], classes="desc-value")
                
                yield Label("Tier:", classes="desc-label")
                yield Label(self.app_data.get('tier', 'Standard'), classes="desc-value")
                
                yield Label("Package:", classes="desc-label")
                yield Label(self.app_data['pkg'], classes="desc-value")
            
            yield Label("Description:", classes="desc-label-header")
            with ScrollableContainer(id="app_desc_text_container"):
                yield Label(self.app_data['description'], id="app_desc_text")
            
            with Horizontal(id="app_desc_actions"):
                yield Button("Close", variant="default", id="close_desc_btn")

    def on_mount(self):
        pass

    @on(Button.Pressed, "#close_desc_btn")
    def close_screen(self):
        self.dismiss()

class AppInstaller(Horizontal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Local import to avoid circular dependency as config imports apps
        from config import detect_aur_helper
        self.aur_helper = detect_aur_helper()

    def compose(self) -> ComposeResult:
        # Left Panel: App List & Actions
        with Vertical(classes="left-panel"):
            yield Label("Select Applications", id="app_list_title")
            yield Label("Click name for details. Click [x] to select.", id="app_list_instructions")
            
            # Replaced SelectionList with DataTable
            with Horizontal(classes="selection-buttons"):
                yield Button("Select All", id="btn_app_select_all", variant="primary")
                yield Button("Deselect All", id="btn_app_deselect_all", variant="error")

            yield DataTable(id="app_table", cursor_type="cell")
            
            yield Label("", id="install_status")
            yield ProgressBar(total=100, show_eta=False, id="install_progress")
            
            with Horizontal(id="app_actions"):
                yield Button("Install Selected", variant="primary", id="app_install_btn")
                yield Button("Uninstall Selected", variant="error", id="app_uninstall_btn")

        # Right Panel: Logs
        with Vertical(classes="right-panel"):
            yield Label("Installation Log")
            yield RichLog(id="app_log", markup=True, highlight=True)

    def on_mount(self):
        self.query_one("#install_progress", ProgressBar).display = False
        
        # Configure DataTable
        table = self.query_one("#app_table", DataTable)
        table.add_column("Select", key="Select")
        table.add_column("Name", key="Name")
        table.add_column("Category", key="Category")
        table.add_column("Source", key="Source")
        table.add_column("Tier", key="Tier")
        table.add_column("Status", key="Status")
        
        # Populate data
        self.run_worker(self.refresh_app_status(), exclusive=True)

    async def refresh_app_status(self):
        """Check installed status of all apps and populate the table."""
        self.log_message("Checking installed applications...")
        table = self.query_one("#app_table", DataTable)
        table.clear()
        
        installed_packages = await self.get_installed_packages()
        flat_apps = get_flat_app_list()
        
        for app in flat_apps:
            is_installed = app['pkg'] in installed_packages
            
            # Determine selection status
            # If installed: Checked (X)
            # If not installed but Default: Checked (X)
            # If not installed and not Default: Unchecked ( )
            # We use a simple text representation for checkbox for now inside DataTable
            
            # However, for the logic of "Install Selected", we usually want to select things TO BE installed.
            # But standard installers show installed state.
            # Let's follow the previous logic:
            # Selection means "I want this on my system".
            # If installed, it is selected. If user unselects, they might mean uninstall (if we support sync).
            # But current buttons are "Install Selected" and "Uninstall Selected".
            # So "Install Selected" should install checked items that ARE NOT installed.
            # "Uninstall Selected" should uninstall checked items that ARE installed.
            
            should_be_checked = is_installed or app.get('default', False)
            check_mark = r"\[x]" if should_be_checked else r"\[ ]"
            
            status_str = "[green]Installed[/green]" if is_installed else "[dim]Not Installed[/dim]"
            
            # Store the full app object in the row key or tag if possible, 
            # but DataTable stores data by row/col. We can map row_key to app data.
            row_key = app['pkg']
            
            table.add_row(
                check_mark, 
                app['name'], 
                app['category'], 
                app['source'], 
                app['tier'], 
                status_str,
                key=row_key
            )
            
        self.log_message("[green]Application list updated.[/green]")

    @on(DataTable.CellSelected)
    def on_cell_selected(self, event: DataTable.CellSelected):
        """
        Handle cell selection (Click or Enter).
        - Column 0 (Select): Toggle checkbox.
        - Other columns: Open description.
        """
        row_key = event.cell_key.row_key.value

        # Use coordinate.column (index) for reliability
        if event.coordinate.column == 0:
            table = event.data_table
            current_val = table.get_cell_at(event.coordinate)
            
            # Toggle
            new_val = r"\[ ]" if r"\[x]" in str(current_val) else r"\[x]"
            table.update_cell_at(event.coordinate, new_val)
        
        else:
            # Any other column -> Show Details
            flat_apps = get_flat_app_list()
            app_data = next((a for a in flat_apps if a['pkg'] == row_key), None)
            
            if app_data:
                 self.app.push_screen(AppDescriptionScreen(app_data))

    @on(Button.Pressed, "#btn_app_select_all")
    def select_all_apps(self):
        table = self.query_one("#app_table", DataTable)
        for row_key in table.rows:
            table.update_cell(row_key, "Select", r"\[x]")

    @on(Button.Pressed, "#btn_app_deselect_all")
    def deselect_all_apps(self):
        table = self.query_one("#app_table", DataTable)
        for row_key in table.rows:
            table.update_cell(row_key, "Select", r"\[ ]")

    async def get_installed_packages(self) -> set[str]:
        """Return a set of all installed packages (pacman + yay)."""
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

    @on(Button.Pressed, "#app_install_btn")
    def install_selected(self):
        table = self.query_one("#app_table", DataTable)
        selected_pkgs = []
        
        # Iterate over all rows to check the "Select" column
        for row_key in table.rows:
            # Column 0 is Select
            select_cell = table.get_cell(row_key, "Select")
            if r"\[x]" in str(select_cell):
                selected_pkgs.append(row_key.value) # row_key is the pkg name
        
        if not selected_pkgs:
            self.log_message("[yellow]No applications selected for installation.[/yellow]")
            return

        self.query_one("#app_install_btn", Button).disabled = True
        self.query_one("#app_uninstall_btn", Button).disabled = True
        self.query_one("#install_progress", ProgressBar).display = True
        
        self.run_worker(self.run_installation(selected_pkgs), exclusive=True)

    @on(Button.Pressed, "#app_uninstall_btn")
    def uninstall_selected(self):
        table = self.query_one("#app_table", DataTable)
        selected_pkgs = []
        
        for row_key in table.rows:
            select_cell = table.get_cell(row_key, "Select")
            if r"\[x]" in str(select_cell):
                selected_pkgs.append(row_key.value)
        
        if not selected_pkgs:
            self.log_message("[yellow]No applications selected for uninstall.[/yellow]")
            return

        # Push confirmation screen
        def check_confirm(confirmed):
            if confirmed:
                # Push safety screen
                def check_safety(safe):
                    if safe:
                        self.query_one("#app_install_btn", Button).disabled = True
                        self.query_one("#app_uninstall_btn", Button).disabled = True
                        self.query_one("#install_progress", ProgressBar).display = True
                        self.run_worker(self.run_uninstallation(selected_pkgs), exclusive=True)
                
                self.app.push_screen(UninstallSafetyScreen(), check_safety)

        self.app.push_screen(UninstallConfirmationScreen(len(selected_pkgs)), check_confirm)

    async def run_installation(self, selected_pkgs):
        progress_bar = self.query_one("#install_progress", ProgressBar)
        status_label = self.query_one("#install_status", Label)
        
        flat_apps = get_flat_app_list()
        pacman_apps = []
        yay_apps = []

        for pkg in selected_pkgs:
            # Find app definition to know manager
            app = next((a for a in flat_apps if a['pkg'] == pkg), None)
            if app:
                if app['source'] == "pacman":
                    pacman_apps.append(pkg)
                elif app['source'] == "yay" or app['source'] == "aur":
                    yay_apps.append(pkg)

        total_steps = (1 if pacman_apps else 0) + (1 if yay_apps else 0)
        progress_bar.update(total=total_steps, progress=0)
        
        current_step = 0

        if pacman_apps:
            status_label.update("Installing Pacman packages...")
            await self.install_packages("pacman", pacman_apps)
            current_step += 1
            progress_bar.update(progress=current_step)
        
        if yay_apps:
            if self.aur_helper:
                status_label.update(f"Installing {self.aur_helper} packages...")
                await self.install_packages(self.aur_helper, yay_apps)
            else:
                self.log_message("[red]No AUR helper found (yay/paru/etc). Cannot install AUR packages.[/red]")
            
            current_step += 1
            progress_bar.update(progress=current_step)

        status_label.update("Installation complete.")
        self.query_one("#app_install_btn", Button).disabled = False
        self.query_one("#app_uninstall_btn", Button).disabled = False
        progress_bar.display = False
        
        # Refresh list to update status
        await self.refresh_app_status()

    async def run_uninstallation(self, selected_pkgs):
        progress_bar = self.query_one("#install_progress", ProgressBar)
        status_label = self.query_one("#install_status", Label)
        
        if not selected_pkgs:
            return

        progress_bar.update(total=1, progress=0)
        status_label.update("Uninstalling packages...")
        
        # Use detected AUR helper if available
        if self.aur_helper:
            cmd = [self.aur_helper, "-Rns", "--noconfirm"] + selected_pkgs
        else:
            self.log_message("[yellow]No AUR helper found. Falling back to sudo pacman -Rns.[/yellow]")
            cmd = ["sudo", "pacman", "-Rns", "--noconfirm"] + selected_pkgs

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
        self.query_one("#app_install_btn", Button).disabled = False
        self.query_one("#app_uninstall_btn", Button).disabled = False
        progress_bar.display = False
        
        await self.refresh_app_status()

    async def install_packages(self, manager: str, packages: list[str]) -> bool:
        cmd = []
        if manager == "pacman":
            cmd = ["sudo", "pacman", "-S", "--noconfirm"] + packages
        else:
            # Assuming AUR helper (yay, paru, etc.)
            cmd = [manager, "-S", "--noconfirm"] + packages

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
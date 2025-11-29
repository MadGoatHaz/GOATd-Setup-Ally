import asyncio
import subprocess
import re
from textual.app import ComposeResult
from textual.widgets import Static, SelectionList, Button, RichLog, ProgressBar, Label, DataTable, TabbedContent, TabPane, ListView, ListItem
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer, VerticalScroll
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
        "LACT": {"pkg": "lact", "source": "aur", "tier": "Top Tier", "description": "Rust-based GPU control. Post-install: sudo systemctl enable --now lactd"},
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
        "MangoHud": {"pkg": "mangohud", "source": "pacman", "tier": "Top Tier", "description": "Vulkan and OpenGL overlay for monitoring FPS, temperatures, CPU/GPU load."},
        "Steam": {"pkg": "steam", "source": "pacman", "tier": "God Tier", "description": "Video game digital distribution service and storefront.", "ports": ["27031/udp", "27036/tcp", "27036/udp", "27037/tcp", "27015/tcp"]},
        "Heroic Launcher": {"pkg": "heroic-games-launcher-bin", "source": "aur", "tier": "Top Tier", "description": "Game launcher for Epic Games and GOG."},
        "Lutris": {"pkg": "lutris", "source": "pacman", "tier": "Utility", "description": "Open gaming platform."},
        "Prism Launcher": {"pkg": "prism-launcher", "source": "pacman", "tier": "Minecraft", "description": "Minecraft launcher with multiple instance support."},
    },
    "AI & Creative": {
        "LM Studio": {"pkg": "lm-studio-appimage", "source": "aur", "tier": "God Tier", "description": "Easy-to-use desktop application for running local LLMs."},
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

def get_table_id(category):
    # Strictly sanitize: replace non-alphanumeric chars with _, collapse duplicates, strip ends
    clean = re.sub(r'[^a-z0-9]', '_', category.lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return f"table_{clean}"

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
        super().__init__(id="apps_container", *args, **kwargs)
        # Local import to avoid circular dependency as config imports apps
        from config import detect_aur_helper
        self.aur_helper = detect_aur_helper()
        self.selected_apps = set() # Stores pkg_ids of selected apps

    def compose(self) -> ComposeResult:
        # Left Panel: Tabbed Interface
        with Vertical(id="apps_left_pane"):
            yield Label("Select Applications", id="app_list_title")
            yield Label("Navigate tabs to find apps. Click [x] to select.", id="app_list_instructions")
            
            with Horizontal(id="app_toolbar"):
                yield Button("<", id="tab_prev", classes="compact")
                yield Button(">", id="tab_next", classes="compact")
                yield Label("  ")
                yield Button("All", id="select_all", classes="compact")
                yield Button("None", id="deselect_all", classes="compact")

            with TabbedContent(id="apps_tabs"):
                for category in APPS_CATEGORIES.keys():
                    with TabPane(category, id=f"tab_{get_table_id(category)}"):
                        # Unique ID for each table
                        table_id = get_table_id(category)
                        yield DataTable(id=table_id, cursor_type="cell")
            
            yield Label("", id="install_status")
            yield ProgressBar(total=100, show_eta=False, id="install_progress")
            
            with Horizontal(id="app_actions"):
                yield Button("Install Selected", variant="primary", id="app_install_btn", classes="compact")
                yield Button("Uninstall Selected", variant="error", id="app_uninstall_btn", classes="compact")

        # Right Panel: Cart & Logs
        with Vertical(id="apps_right_pane"):
            # Cart Section
            with Vertical(id="cart_section"):
                yield Label("Selected Apps", id="cart_header")
                yield ListView(id="cart_list")

            # Log Section
            with Vertical(id="log_section"):
                yield Label("Logs")
                yield RichLog(id="app_log", markup=True, highlight=True)

    def on_mount(self):
        self.query_one("#install_progress", ProgressBar).display = False
        
        # Configure all DataTables
        for category in APPS_CATEGORIES.keys():
            table_id = get_table_id(category)
            try:
                table = self.query_one(f"#{table_id}", DataTable)
                table.add_column("Select", key="Select")
                table.add_column("Name", key="Name")
                table.add_column("Source", key="Source")
                table.add_column("Tier", key="Tier")
                table.add_column("Status", key="Status")
            except Exception:
                pass
        
        # Populate data
        self.run_worker(self.refresh_app_status(), exclusive=True)

    async def refresh_app_status(self):
        """Check installed status of all apps and populate the tables."""
        self.log_message("Checking installed applications...")
        
        installed_packages = await self.get_installed_packages()
        
        # Populate local set with installed apps initially (optional, but good for UX)
        # Or keep selection separate from installed status?
        # "Selection means I want this". If it's installed, it's already "selected" in a way.
        # Let's auto-select installed apps.
        for pkg in installed_packages:
             # Only add if it's one of our known apps
             flat = get_flat_app_list()
             if any(a['pkg'] == pkg for a in flat):
                 self.selected_apps.add(pkg)

        self.update_cart_view()

        # Iterate categories to populate each table
        for category, apps in APPS_CATEGORIES.items():
            table_id = get_table_id(category)
            try:
                table = self.query_one(f"#{table_id}", DataTable)
                table.clear()
                
                for app_name, app_details in apps.items():
                    pkg = app_details['pkg']
                    is_installed = pkg in installed_packages
                    is_selected = pkg in self.selected_apps
                    
                    check_mark = r"\[x]" if is_selected else r"\[ ]"
                    status_str = "[green]Installed[/green]" if is_installed else "[dim]Not Installed[/dim]"
                    
                    table.add_row(
                        check_mark,
                        app_name,
                        app_details['source'],
                        app_details.get('tier', ''),
                        status_str,
                        key=pkg
                    )
            except Exception:
                continue
            
        self.log_message("[green]Application list updated.[/green]")

    def update_cart_view(self):
        """Refresh the Cart ListView based on self.selected_apps."""
        cart_list = self.query_one("#cart_list", ListView)
        cart_list.clear()
        
        if not self.selected_apps:
            cart_list.append(ListItem(Label("[dim]No apps selected[/dim]")))
            return

        # Sort for display
        sorted_apps = sorted(list(self.selected_apps))
        
        flat_apps = get_flat_app_list()
        
        for pkg in sorted_apps:
            # Find readable name
            app_data = next((a for a in flat_apps if a['pkg'] == pkg), None)
            name = app_data['name'] if app_data else pkg
            
            item_layout = Horizontal(
                Label(f"{name} ({pkg})"),
                Button("x", id=f"remove_{pkg}", classes="compact remove-btn"),
                classes="cart-item"
            )
            cart_list.append(ListItem(item_layout))

    @on(DataTable.CellSelected)
    def on_cell_selected(self, event: DataTable.CellSelected):
        """
        Handle cell selection across any table.
        """
        row_key = event.cell_key.row_key.value # This is the pkg ID

        # Use coordinate.column (index) for reliability
        if event.coordinate.column == 0:
            table = event.data_table
            current_val = table.get_cell_at(event.coordinate)
            
            # Toggle logic
            if r"\[x]" in str(current_val):
                # Deselect
                new_val = r"\[ ]"
                if row_key in self.selected_apps:
                    self.selected_apps.remove(row_key)
            else:
                # Select
                new_val = r"\[x]"
                self.selected_apps.add(row_key)
            
            table.update_cell_at(event.coordinate, new_val)
            self.update_cart_view()
        
        else:
            # Any other column -> Show Details
            flat_apps = get_flat_app_list()
            app_data = next((a for a in flat_apps if a['pkg'] == row_key), None)
            
            if app_data:
                 self.app.push_screen(AppDescriptionScreen(app_data))

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
        # Filter selected apps that are NOT installed?
        # Or just reinstall everything selected?
        # Usually "Install" implies installing missing things.
        # But let's just pass the list to the installer logic, which usually handles existing things gracefully (reinstall/skip).
        
        if not self.selected_apps:
            self.log_message("[yellow]No applications selected.[/yellow]")
            return

        self.query_one("#app_install_btn", Button).disabled = True
        self.query_one("#app_uninstall_btn", Button).disabled = True
        self.query_one("#install_progress", ProgressBar).display = True
        
        self.run_worker(self.run_installation(list(self.selected_apps)), exclusive=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if not btn_id:
            return
            
        if btn_id == "tab_prev":
            self.action_prev_tab()
        elif btn_id == "tab_next":
            self.action_next_tab()
        elif btn_id == "select_all":
            self.action_select_all_tab()
        elif btn_id == "deselect_all":
            self.action_deselect_all_tab()
        elif btn_id.startswith("remove_"):
            pkg_to_remove = btn_id.replace("remove_", "")
            if pkg_to_remove in self.selected_apps:
                self.selected_apps.remove(pkg_to_remove)
                self.update_cart_view()
                self.refresh_tables_checkmarks()

    def action_prev_tab(self):
        tabs = self.query_one("#apps_tabs", TabbedContent)
        if not tabs.active: return
        
        panes = [c.id for c in tabs.query(TabPane)]
        if not panes: return
        
        try:
            curr_idx = panes.index(tabs.active)
            new_idx = (curr_idx - 1) % len(panes)
            tabs.active = panes[new_idx]
        except ValueError:
            pass

    def action_next_tab(self):
        tabs = self.query_one("#apps_tabs", TabbedContent)
        if not tabs.active: return
        
        panes = [c.id for c in tabs.query(TabPane)]
        if not panes: return
        
        try:
            curr_idx = panes.index(tabs.active)
            new_idx = (curr_idx + 1) % len(panes)
            tabs.active = panes[new_idx]
        except ValueError:
            pass

    def action_select_all_tab(self):
        self._toggle_tab_selection(select=True)

    def action_deselect_all_tab(self):
        self._toggle_tab_selection(select=False)

    def _toggle_tab_selection(self, select: bool):
        tabs = self.query_one("#apps_tabs", TabbedContent)
        if not tabs.active: return
        
        # TabPane ID is "tab_table_xxx", table ID is "table_xxx"
        # We constructed TabPane ID as f"tab_{table_id}"
        # So we can derive table ID from TabPane ID
        active_pane_id = tabs.active
        if not active_pane_id.startswith("tab_"): return
        
        table_id = active_pane_id[4:] # remove "tab_" prefix
        
        try:
            table = self.query_one(f"#{table_id}", DataTable)
        except Exception:
            return

        # Iterate rows
        # row_key in table is the pkg ID
        # But table.rows is a dict of row_key -> Row
        # We need to iterate over keys
        
        # Textual DataTable API: table.rows is different in versions.
        # Safer to use coordinate iteration or just iterate over list of data if we have it.
        # But we used APPS_CATEGORIES to build it.
        
        # Reverse lookup category from table_id? Or just iterate all rows in table.
        # table.coordinate_to_cell_key map exists?
        
        # Let's use the fact that row keys are pkg names
        # We can just scan the table's rows.
        
        # In modern Textual, table.rows is a dict.
        for row_key in table.rows:
             pkg = row_key.value
             if select:
                 self.selected_apps.add(pkg)
             else:
                 if pkg in self.selected_apps:
                     self.selected_apps.remove(pkg)
        
        self.update_cart_view()
        self.refresh_tables_checkmarks()

    def refresh_tables_checkmarks(self):
        """Update checkmarks in all tables based on current selection."""
        for category in APPS_CATEGORIES.keys():
            table_id = get_table_id(category)
            try:
                table = self.query_one(f"#{table_id}", DataTable)
                for row_key in table.rows:
                    pkg = row_key.value
                    is_selected = pkg in self.selected_apps
                    check_mark = r"\[x]" if is_selected else r"\[ ]"
                    # Update column 0 ("Select")
                    table.update_cell(row_key, "Select", check_mark)
            except Exception:
                pass

    @on(Button.Pressed, "#app_uninstall_btn")
    def uninstall_selected(self):
        if not self.selected_apps:
            self.log_message("[yellow]No applications selected.[/yellow]")
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
                        self.run_worker(self.run_uninstallation(list(self.selected_apps)), exclusive=True)
                
                self.app.push_screen(UninstallSafetyScreen(), check_safety)

        self.app.push_screen(UninstallConfirmationScreen(len(self.selected_apps)), check_confirm)

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
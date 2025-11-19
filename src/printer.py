import asyncio
import subprocess
import shutil
import re
from textual import on
from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, SelectionList, Label, RichLog, Checkbox
from textual.worker import Worker, WorkerState

class PrinterSetup(Horizontal):
    def compose(self) -> ComposeResult:
        # Left Panel: Managed configured printers
        with Vertical(id="left_panel"):
            yield Label("My Configured Printers", id="printers_title")
            yield SelectionList(id="installed_printers_list")
            yield Button("Print Test Page", id="test_page_btn", disabled=True)
            yield Button("Remove Selected Printer", id="remove_printer_btn", disabled=True)
            yield Label("System Log:")
            yield RichLog(id="printer_log", highlight=True, markup=True)

        # Right Panel: Driver Management
        with Vertical(id="right_panel"):
            yield Label("Driver Management", id="drivers_title")
            yield Input(placeholder="Enter Printer Make/Model (e.g., Brother DCP-L2550DW)", id="printer_input")
            yield Button("Search Drivers", id="search_btn")
            yield Label("Select Driver:")
            yield SelectionList(id="driver_list")
            
            with Vertical(id="driver_actions"):
                yield Button("Scan & Register Printer", id="scan_btn", variant="primary")
                
                # Manual Entry Section
                yield Label("— OR —", classes="section-label")
                with Horizontal(classes="manual-row"):
                    yield Input(placeholder="Enter IP (e.g. 192.168.1.5) or URI", id="manual_ip")
                    yield Button("Register Manual", id="manual_add_btn", variant="primary")

                yield Label("— Driver Install Options —", classes="section-label")
                yield Input(placeholder="Printer IP (Optional, for Scanner)", id="ip_input")
                yield Checkbox("Force Overwrite Files (Fix Conflicts)", id="force_overwrite_chk")
                yield Button("Install / Update Selected", id="install_btn", disabled=True)
                yield Button("Uninstall Selected Driver", id="uninstall_driver_btn", disabled=True)

    def on_mount(self):
        self.driver_mode = "search"
        self.refresh_status()

    def refresh_status(self):
        """Check for configured printers and update the list."""
        printers_list = self.query_one("#installed_printers_list", SelectionList)
        printers_list.clear_options()
        
        # Check configured printers
        printers = self.get_configured_printers()
        if printers:
            for p in printers:
                # p is like "HL-L2350DW (Idle)"
                # We want the value to be just the name "HL-L2350DW"
                name = p.split('(')[0].strip()
                printers_list.add_option((p, name))
        
        # Disable buttons
        self.query_one("#test_page_btn", Button).disabled = True
        self.query_one("#remove_printer_btn", Button).disabled = True

    def get_configured_printers(self) -> list[str]:
        """Get a list of configured printers using lpstat."""
        try:
            # lpstat -p lists printers. Output format: "printer PrinterName is idle. enabled since..."
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
            if result.returncode != 0:
                return []
            
            printers = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "printer":
                    name = parts[1]
                    status_raw = " ".join(parts[2:])
                    status = "Unknown"
                    
                    if "is idle" in status_raw:
                        status = "Idle"
                    elif "disabled" in status_raw:
                        status = "Disabled"
                    elif "now printing" in status_raw:
                        status = "Printing"
                    else:
                        status = status_raw.split('.')[0]
                        
                    printers.append(f"{name} ({status})")
            return printers
        except FileNotFoundError:
            return []
        except Exception:
            return []

    def is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed using pacman."""
        try:
            subprocess.run(
                ["pacman", "-Qi", package_name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def log_message(self, message: str):
        """Log a message to the local RichLog and the main app's RichLog if available."""
        try:
            log = self.query_one("#printer_log", RichLog)
            log.write(message)
        except Exception:
            pass

        if hasattr(self.app, "log_message"):
            self.app.log_message(message)
        else:
            # Fallback for testing or if app doesn't have log_message
            try:
                main_log = self.app.query_one("#main_log", RichLog)
                main_log.write(message)
            except Exception:
                pass

    @on(Button.Pressed, "#search_btn")
    def on_search_btn(self):
        query = self.query_one("#printer_input", Input).value
        if not query:
            self.log_message("[red]Please enter a printer make/model.[/red]")
            return
        
        self.driver_mode = "search"
        self.query_one("#drivers_title", Label).update("Driver Results")
        self.query_one("#search_btn", Button).disabled = True
        self.query_one("#search_btn", Button).label = "Searching..."
        # Only log errors or "No drivers found"
        self.run_worker(self.search_drivers(query), exclusive=True)

    @on(Button.Pressed, "#scan_btn")
    def on_scan_btn(self):
        """Scan for local printers."""
        self.query_one("#scan_btn", Button).disabled = True
        self.query_one("#scan_btn", Button).label = "Scanning..."
        self.driver_mode = "scan"
        self.query_one("#drivers_title", Label).update("Discovered Devices")
        self.run_worker(self.scan_devices(), exclusive=True)

    @on(Button.Pressed, "#manual_add_btn")
    def on_manual_add_btn(self):
        """Handle manual printer registration."""
        raw_input = self.query_one("#manual_ip", Input).value.strip()
        if not raw_input:
            self.log_message("[red]Please enter an IP address or URI.[/red]")
            return
            
        # Determine URI
        uri = raw_input
        if "://" not in raw_input:
            # Assume IP address, default to ipp://
            # Validate weak IP pattern
            import re
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', raw_input):
                uri = f"ipp://{raw_input}"
                self.log_message(f"Assuming ipp protocol for IP: {raw_input}")
            else:
                 # Treat as hostname or potential partial URI
                 uri = f"ipp://{raw_input}"

        self.log_message(f"[yellow]Starting manual registration for: {uri}[/yellow]")
        
        # Use the search input as model hint
        model_hint = self.query_one("#printer_input", Input).value
        self.run_worker(self.auto_register_printer(uri, model_hint), exclusive=True)

    async def scan_devices(self):
        try:
            self.log_message("Scanning for devices (lpinfo -v)...")
            # Run lpinfo -v
            cmd = ["lpinfo", "-v"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.log_message(f"[red]Scan failed: {escape(stderr.decode())}[/red]")
                return

            output = stdout.decode()
            devices = []
            
            # Regex to find URIs: matching class://uri
            # We filter out lines that are just backends (no ://)
            # And parse friendly names
            lines = output.splitlines()
            for line in lines:
                if "://" in line:
                    # It's likely a device
                    # Format usually: class uri
                    parts = line.split(" ", 1)
                    if len(parts) < 2: continue
                    
                    dev_class = parts[0]
                    uri = parts[1]
                    
                    # Generate Friendly Name
                    friendly_name = uri
                    if uri.startswith("usb://"):
                        # usb://Brother/DCP-L2550DW?serial=...
                        # Extract Make/Model
                        match = re.search(r'usb://([^?]+)', uri)
                        if match:
                            model_part = match.group(1).replace('/', ' ')
                            friendly_name = f"{model_part} (USB)"
                    elif uri.startswith("dnssd://"):
                        # dnssd://Brother%20DCP-L2550DW%20series._ipp._tcp.local/
                        friendly_name = "Network Printer (Bonjour/AirPrint)"
                        # Try to decode better name
                        try:
                            import urllib.parse
                            decoded = urllib.parse.unquote(uri)
                            match = re.search(r'dnssd://([^/]+)', decoded)
                            if match:
                                friendly_name = f"{match.group(1)} (Network)"
                        except: pass
                    elif uri.startswith("ipp://") or uri.startswith("socket://"):
                         friendly_name = f"Network Printer ({uri})"

                    # Escape content to prevent markup issues
                    # Use parens instead of brackets to avoid markup confusion if escaping fails or behavior is weird
                    label = f"{escape(friendly_name)}  ({escape(dev_class)})"
                    devices.append((label, uri))

            driver_list = self.query_one("#driver_list", SelectionList)
            driver_list.clear_options()
            
            if devices:
                for label, value in devices:
                    driver_list.add_option((label, value))
                self.log_message(f"[green]Found {len(devices)} devices.[/green]")
                # Re-purpose the install button for registration
                self.query_one("#install_btn", Button).label = "Register Selected Printer"
                self.query_one("#install_btn", Button).disabled = True # Wait for selection
            else:
                self.log_message("[yellow]No devices found via lpinfo -v.[/yellow]")
                self.log_message("Check USB connection or ensure printer is on network.")

        except Exception as e:
            self.log_message(f"[red]Error scanning devices: {escape(str(e))}[/red]")
        finally:
            self.query_one("#scan_btn", Button).disabled = False
            self.query_one("#scan_btn", Button).label = "Scan & Register Printer"

    async def search_drivers(self, query: str):
        try:
            # yay -Ss {query} output format is typically:
            # repo/package-name version (votes) [installed]
            #     Description
            cmd = ["yay", "-Ss", "--color=never", query]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.log_message(f"[red]Error searching drivers: {escape(stderr.decode().strip())}[/red]")
                return

            output = stdout.decode()
            lines = output.strip().split('\n')
            
            drivers = []
            current_package = None
            package_pattern = re.compile(r'^([^/\s]+)/([^\s]+)\s+([^\s]+)')
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            for line in lines:
                # Remove OSC sequences (hyperlinks) first
                line = re.sub(r'\x1b\].*?\x1b\\', '', line)
                # Remove ANSI escape codes
                line = ansi_escape.sub('', line)
                
                match = package_pattern.match(line)
                if match:
                    current_package = match.group(2)
                elif current_package and line.startswith("    "):
                    description = line.strip()
                    
                    # Check if installed
                    is_installed = self.is_package_installed(current_package)
                    status_mark = "[Installed] " if is_installed else ""
                    display_label = f"{status_mark}{current_package} - {description}"
                    
                    drivers.append((display_label, current_package))
                    current_package = None

            driver_list = self.query_one("#driver_list", SelectionList)
            driver_list.clear_options()
            
            if drivers:
                for label, value in drivers:
                    driver_list.add_option((label, value))
                self.query_one("#install_btn", Button).disabled = False
                self.query_one("#install_btn", Button).label = "Install / Update Selected"
            else:
                self.log_message("[yellow]No drivers found.[/yellow]")
                # Escaping output to prevent markup errors from raw text
                self.log_message(f"Raw Output:\n{escape(output)}")
                self.query_one("#install_btn", Button).disabled = True

        except Exception as e:
            self.log_message(f"[red]Exception during search: {escape(str(e))}[/red]")
        
        finally:
            self.query_one("#search_btn", Button).disabled = False
            self.query_one("#search_btn", Button).label = "Search Drivers"

    @on(SelectionList.SelectedChanged, "#installed_printers_list")
    def on_printer_selected(self):
        selected = self.query_one("#installed_printers_list", SelectionList).selected
        has_selection = bool(selected)
        self.query_one("#test_page_btn", Button).disabled = not has_selection
        self.query_one("#remove_printer_btn", Button).disabled = not has_selection

    @on(Button.Pressed, "#test_page_btn")
    def on_test_page_btn(self):
        selected = self.query_one("#installed_printers_list", SelectionList).selected
        for printer in selected:
            self.log_message(f"Sending test page to {printer}...")
            # /usr/share/cups/data/testprint is standard on Arch cups package
            self.run_worker(self._print_test_page(printer))

    async def _print_test_page(self, printer_name):
        try:
            cmd = ["lp", "-d", printer_name, "/usr/share/cups/data/testprint"]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                self.log_message(f"[green]Test page sent to {printer_name}[/green]")
            else:
                self.log_message(f"[red]Failed to print test page: {escape(stderr.decode())}[/red]")
        except Exception as e:
            self.log_message(f"[red]Error: {escape(str(e))}[/red]")

    @on(Button.Pressed, "#remove_printer_btn")
    @on(Button.Pressed, "#remove_printer_btn")
    def on_remove_printer_btn(self):
        selected = self.query_one("#installed_printers_list", SelectionList).selected
        if not selected: return
        
        self.run_worker(self.remove_printers(selected), exclusive=True)

    async def remove_printers(self, printers):
        try:
            for printer in printers:
                self.log_message(f"Removing printer queue: {printer}...")
                await self._run_command(["sudo", "lpadmin", "-x", printer])
            
            self.log_message("[green]Printer(s) removed.[/green]")
            self.refresh_status()
        except Exception as e:
            self.log_message(f"[red]Error removing printers: {escape(str(e))}[/red]")

    @on(SelectionList.SelectedChanged, "#driver_list")
    def on_driver_selected(self):
        driver_list = self.query_one("#driver_list", SelectionList)
        selected = driver_list.selected
        install_btn = self.query_one("#install_btn", Button)
        uninstall_btn = self.query_one("#uninstall_driver_btn", Button)

        if not selected:
            install_btn.disabled = True
            uninstall_btn.disabled = True
            if self.driver_mode == "scan":
                 install_btn.label = "Register Selected Printer"
            else:
                 install_btn.label = "Install / Update Selected"
            return

        install_btn.disabled = False
        
        if self.driver_mode == "scan":
            # We are in Register Mode
            install_btn.label = "[bold green]Auto-Config & Register[/]"
            uninstall_btn.disabled = True
        else:
            # We are in Driver Mode
            # Check if package is installed to enable Uninstall
            any_installed = False
            for pkg in selected:
                # Check if it looks like a package name (no ://)
                if "://" not in pkg and self.is_package_installed(pkg):
                    any_installed = True
                    break
            
            uninstall_btn.disabled = not any_installed
            
            if any_installed:
                install_btn.label = "Reinstall / Update Selected"
            else:
                install_btn.label = "Install Selected"

    @on(Button.Pressed, "#uninstall_driver_btn")
    def on_uninstall_driver_btn(self):
        selected = self.query_one("#driver_list", SelectionList).selected
        if not selected: return
        
        self.log_message(f"[yellow]Uninstalling drivers: {', '.join(selected)}[/yellow]")
        self.run_worker(self.uninstall_drivers(selected), exclusive=True)

    async def uninstall_drivers(self, drivers):
        try:
            for driver in drivers:
                self.log_message(f"Removing package {driver}...")
                await self._run_command(["yay", "-Rns", "--noconfirm", driver])
            self.log_message("[green]Drivers uninstalled successfully.[/green]")
            
            # Re-search to update status tags
            current_query = self.query_one("#printer_input", Input).value
            if current_query:
                await self.search_drivers(current_query)
                
        except Exception as e:
            self.log_message(f"[red]Uninstall failed: {escape(str(e))}[/red]")

    @on(Button.Pressed, "#install_btn")
    def on_install_btn(self):
        driver_list = self.query_one("#driver_list", SelectionList)
        selected = driver_list.selected

        if not selected:
            self.log_message("[red]Please select an item.[/red]")
            return

        # Check if we are registering a printer or installing a driver
        if self.driver_mode == "scan":
            # Register Mode
            device_uri = selected[0] # Single selection expected usually
            self.log_message(f"[yellow]Starting auto-configuration for device: {device_uri}[/yellow]")
            # Use the text input as a model hint if provided
            model_hint = self.query_one("#printer_input", Input).value
            self.run_worker(self.auto_register_printer(device_uri, model_hint), exclusive=True)
        else:
            # Driver Install Mode
            ip_address = self.query_one("#ip_input", Input).value
            force = self.query_one("#force_overwrite_chk", Checkbox).value
            
            self.log_message(f"[yellow]Starting installation for: {', '.join(selected)}[/yellow]")
            if force:
                self.log_message("[yellow]FORCE OVERWRITE ENABLED[/yellow]")
            
            self.run_worker(self.install_printer(selected, ip_address, force), exclusive=True)

    async def auto_register_printer(self, uri: str, model_hint: str = ""):
        try:
            self.log_message("Step 1: Finding best driver PPD...")
            
            # If no hint, verify if we can extract from URI
            if not model_hint:
                if "brother" in uri.lower():
                    model_hint = "brother"
                    # Try to look deeper in URI for numbers
                    match = re.search(r'([A-Za-z0-9]+-[A-Za-z0-9]+)', uri.split('/')[-1])
                    if match:
                        model_hint = match.group(1)

            # If still no model hint, we cannot proceed with auto-registration
            if not model_hint.strip():
                 self.log_message("[red]Could not identify printer model from URI. Please enter the Printer Model in the search box above and try again.[/red]")
                 return

            # lpinfo -m
            cmd = ["lpinfo", "-m"]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.log_message(f"[red]lpinfo -m failed: {escape(stderr.decode())}[/red]")
                return
                
            lines = stdout.decode().splitlines()
            
            candidates = []
            
            # Helper for normalization
            def normalize(s):
                return re.sub(r'[^a-z0-9]', '', s.lower())

            norm_hint = normalize(model_hint) if model_hint else ""
            
            # Strategy 1: Broad match (normalized hint in normalized description)
            for line in lines:
                parts = line.split(" ", 1)
                if len(parts) < 2: continue
                ppd = parts[0]
                desc = parts[1]
                norm_desc = normalize(desc)
                
                if norm_hint and norm_hint in norm_desc:
                    candidates.append((ppd, desc))
            
            # Strategy 2: Core Number Matching (if no candidates)
            # e.g. "2550" from "DCP-L2550DW"
            if not candidates and model_hint:
                core_nums = "".join(re.findall(r'\d+', model_hint))
                if len(core_nums) >= 3: # Avoid matching "10", "20" etc.
                    self.log_message(f"No exact match, trying core numbers: {core_nums}...")
                    for line in lines:
                        parts = line.split(" ", 1)
                        if len(parts) < 2: continue
                        ppd = parts[0]
                        desc = parts[1]
                        norm_desc = normalize(desc)
                        
                        if core_nums in norm_desc:
                            candidates.append((ppd, desc))

            if not candidates:
                 self.log_message(f"[red]No drivers found matching '{model_hint}'. Search/Install driver first.[/red]")
                 return
            
            # Pick best candidate
            # prioritizing 'recommended' (case insensitive), then standard paths
            candidates.sort(key=lambda x: (
                "recommended" not in x[1].lower(),
                "english" not in x[1].lower(), # Prefer English if marked
                "lsb/usr" not in x[0]
            ))
            
            best_ppd = candidates[0][0]
            best_desc = candidates[0][1]
            
            self.log_message(f"[green]Selected Driver: {best_desc}[/green]")
            self.log_message(f"PPD: {best_ppd}")
            
            # Step 2: Register Queue
            # Generate name
            # Clean up URI or Description to make a short name
            import random
            name_suffix = random.randint(1000,9999)
            printer_name = f"Auto_Printer_{name_suffix}"
            
            # Try to make a better name from hint
            if model_hint:
                clean_hint = re.sub(r'[^a-zA-Z0-9]', '_', model_hint)
                printer_name = f"{clean_hint}_{name_suffix}"

            self.log_message(f"Step 2: Registering queue '{printer_name}'...")
            
            # lpadmin -p [name] -v [uri] -P [ppd] -E
            lpadmin_cmd = ["sudo", "lpadmin", "-p", printer_name, "-v", uri, "-m", best_ppd, "-E"]
            await self._run_command(lpadmin_cmd)
            
            self.log_message(f"[green]Printer '{printer_name}' successfully configured![/green]")
            self.refresh_status()
            
        except Exception as e:
            self.log_message(f"[red]Auto-config failed: {escape(str(e))}[/red]")

    async def install_printer(self, drivers: list[str], ip_address: str, force: bool = False):
        try:
            # Step 1: Core Setup
            self.log_message("Step 1: Installing core packages (cups, system-config-printer, avahi, simple-scan)...")
            await self._run_command(["yay", "-S", "--noconfirm", "cups", "system-config-printer", "avahi", "simple-scan"])
            
            self.log_message("Enabling services...")
            await self._run_command(["sudo", "systemctl", "enable", "--now", "cups.service"])
            await self._run_command(["sudo", "systemctl", "enable", "--now", "avahi-daemon.service"])

            # Step 2: Driver Install
            self.log_message("Step 2: Installing selected drivers...")
            for driver in drivers:
                self.log_message(f"Installing {escape(driver)}...")
                cmd = ["yay", "-S", "--noconfirm"]
                if force:
                    cmd.extend(["--overwrite", "*"])
                cmd.append(driver)
                await self._run_command(cmd)

            # Step 3: Config
            self.log_message("Step 3: Configuring system...")
            # Modify /etc/nsswitch.conf
            sed_cmd = [
                "sudo", "sed", "-i",
                "s/hosts: files mymachines/hosts: files mymachines mdns_minimal [NOTFOUND=return]/",
                "/etc/nsswitch.conf"
            ]
            await self._run_command(sed_cmd)

            # Add user to cups/lp and scanner groups
            # Use create_subprocess_exec for whoami as well, or just os.getlogin() / os.environ['USER']
            # But for compatibility with the original approach:
            proc = await asyncio.create_subprocess_exec("whoami", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            user = stdout.decode().strip()
            
            self.log_message(f"Adding user {user} to cups and scanner groups...")
            await self._run_command(["sudo", "usermod", "-aG", "lp", user])
            await self._run_command(["sudo", "usermod", "-aG", "scanner", user])

            # Step 4: Scanner IP
            if ip_address:
                self.log_message(f"Step 4: Configuring scanner with IP {ip_address}...")
                if shutil.which("brsaneconfig4"):
                    model_name = drivers[0]
                    friendly_name = "NetworkScanner"
                    await self._run_command(["sudo", "brsaneconfig4", "-a", f"name={friendly_name}", f"model={model_name}", f"ip={ip_address}"])
                else:
                    self.log_message("[yellow]brsaneconfig4 not found. Skipping specific scanner configuration.[/yellow]")

            self.log_message("[green]Printer setup completed successfully![/green]")
            self.log_message("[yellow]You may need to restart your session for group changes to take effect.[/yellow]")
            
            # Refresh status to show new printer
            self.refresh_status()

            # Check for pending manual registration or selected device
            manual_val = self.query_one("#manual_ip", Input).value.strip()
            
            # Also check if a device was selected in the list (even if we are in driver mode now)
            # Note: driver_list stores both drivers and devices depending on mode, but here we might
            # be installing a driver for a device we know.
            # For now, relying on manual_val as primary intent indicator for immediate registration.
            
            if manual_val:
                self.log_message("Attempting to auto-register printer...")
                # Simple protocol fix-up if needed
                uri = manual_val
                if "://" not in uri:
                    uri = f"ipp://{uri}"
                
                # Use the search term that found the driver as the model hint
                hint = self.query_one("#printer_input", Input).value
                await self.auto_register_printer(uri, hint)

        except subprocess.CalledProcessError as e:
            self.log_message(f"[red]Command failed: {escape(str(e))}[/red]")
        except Exception as e:
            self.log_message(f"[red]An error occurred: {escape(str(e))}[/red]")

    async def _run_command(self, cmd):
        cmd_str = " ".join(cmd)
        self.log_message(f"Executing: {escape(cmd_str)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.log_message(f"[red]Command failed with return code {process.returncode}[/red]")
                if stdout:
                    self.log_message(f"STDOUT:\n{escape(stdout.decode())}")
                if stderr:
                    self.log_message(f"STDERR:\n{escape(stderr.decode())}")
                raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)
                
        except Exception as e:
            raise e

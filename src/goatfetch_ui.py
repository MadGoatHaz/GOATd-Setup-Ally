import shutil
import subprocess
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Select, Checkbox, Input, Label, RichLog, DataTable
from textual.app import ComposeResult
from textual import on
from rich.text import Text
from goatfetch_logic import GoatFetchManager

class FastFetchMissingScreen(ModalScreen):
    """Screen shown when FastFetch is missing."""
    def compose(self) -> ComposeResult:
        with Vertical(id="fastfetch_missing_container"):
            yield Label("FastFetch is missing!", id="ff_missing_title")
            yield Label("GoatFetch requires FastFetch to be installed.\nWould you like to install it now?", id="ff_missing_text")
            
            with Horizontal(id="ff_missing_actions"):
                yield Button("Install FastFetch", variant="success", id="btn_ff_install")
                yield Button("Cancel", variant="error", id="btn_ff_cancel")

    @on(Button.Pressed, "#btn_ff_install")
    def install_fastfetch(self):
        self.dismiss(True)

    @on(Button.Pressed, "#btn_ff_cancel")
    def cancel(self):
        self.dismiss(False)

class GoatFetchScreen(Screen):
    """Screen for GoatFetch configuration."""
    
    # Link to the main stylesheet to access variables
    CSS_PATH = "styles.tcss"
    
    def compose(self):
        self.manager = GoatFetchManager()
        
        yield Header()
        with Horizontal(id="goatfetch-container"):
            # Left Panel: Controls
            with Vertical(classes="left-panel"):
                yield Label("GoatFetch Configuration", id="goatfetch-title")
                
                yield Label("Select Variant:")
                variants = self.manager.list_variants()
                options = [(v[1], v[0]) for v in variants]
                yield Select(options, id="variant-select", prompt="Choose a variant...")
                
                yield Checkbox("Use Custom GoatFetch Logo", value=False, id="custom-logo-chk")
                
                yield Label("Weather Location (City):")
                yield Input(placeholder="Leave empty for auto-detect", id="weather-input")
                
                yield Label("Preview:")
                yield Button("Preview Configuration", id="preview-btn", variant="primary")

                with Horizontal(id="action-bar"):
                    yield Button("Install", id="install-btn", variant="success")
                    yield Button("Revert", id="revert-btn", variant="error")
                
                yield Button("Close", id="close-btn")

            # Right Panel: Output Log
            with Vertical(classes="right-panel"):
                yield Label("Activity Log / Preview Output")
                yield RichLog(id="preview-log", wrap=True, highlight=False, markup=True)
            
        yield Footer()

    def on_mount(self):
        # Check if light mode is active on app and apply class
        if getattr(self.app, "dark", True) is False:
             self.add_class("light-mode")
        
        # Check for FastFetch dependency
        if not shutil.which("fastfetch"):
            def check_install(should_install):
                if should_install:
                    self.install_fastfetch_dependency()
                else:
                    self.log_message("[yellow]FastFetch missing. Some features may not work.[/yellow]")
            
            self.app.push_screen(FastFetchMissingScreen(), check_install)

        # Initial log message
        self.log_message("GoatFetch Configurator Ready.")

    def install_fastfetch_dependency(self):
        self.log_message("Installing FastFetch...")
        try:
            # Using subprocess.Popen to not block main thread entirely if we were async,
            # but here we are in a sync callback. For a quick install it's okay,
            # but ideally should be a worker. For simplicity in this context:
            cmd = ["sudo", "pacman", "-S", "fastfetch", "--noconfirm"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if res.returncode == 0:
                self.log_message("[green]FastFetch installed successfully.[/green]")
            else:
                self.log_message(f"[red]Failed to install FastFetch: {res.stderr}[/red]")
        except Exception as e:
            self.log_message(f"[red]Error installing FastFetch: {e}[/red]")

    def log_message(self, message):
        """Writes a message to the RichLog."""
        log_widget = self.query_one("#preview-log", RichLog)
        log_widget.write(message)

    @on(Button.Pressed, "#preview-btn")
    def preview_config(self):
        variant_select = self.query_one("#variant-select", Select)
        if variant_select.value == Select.BLANK:
            self.notify("Please select a variant.", severity="error")
            self.log_message("[bold red]Error:[/bold red] No variant selected.")
            return

        variant = variant_select.value
        use_custom_logo = self.query_one("#custom-logo-chk", Checkbox).value
        weather = self.query_one("#weather-input", Input).value

        self.log_message(f"[bold blue]Generating preview for {variant}...[/bold blue]")
        
        try:
            config_path = self.manager.generate_preview_config(variant, use_custom_logo, weather)
            output = self.manager.run_fastfetch_preview(config_path)
            
            # DEBUG: Log raw output details
            self.log_message(f"[dim]Debug: Output length: {len(output)} chars[/dim]")
            
            text_output = Text.from_ansi(output)
            # Ensure no style leaks from parent by explicitly setting 'end' style to empty if needed,
            # but Text.from_ansi usually handles this.
            # We rely on the CSS !important rules to handle the widget container.
            
            self.log_message(text_output)
            self.log_message("[bold green]Preview complete.[/bold green]")
        except Exception as e:
            self.notify(f"Error generating preview: {e}", severity="error")
            self.log_message(f"[bold red]Error:[/bold red] {e}")

    @on(Button.Pressed, "#install-btn")
    def install(self):
        variant_select = self.query_one("#variant-select", Select)
        if variant_select.value == Select.BLANK:
            self.notify("Please select a variant.", severity="error")
            return

        variant = variant_select.value
        use_custom_logo = self.query_one("#custom-logo-chk", Checkbox).value
        weather = self.query_one("#weather-input", Input).value
        
        try:
            # Pass a lambda that calls our log_message method
            self.manager.install(variant, use_custom_logo, weather, log_callback=lambda msg: self.log_message(f"[green]{msg}[/green]"))
            self.notify("GoatFetch installed successfully!")
        except Exception as e:
            self.notify(f"Error installing GoatFetch: {e}", severity="error")
            self.log_message(f"[bold red]Error installing:[/bold red] {e}")

    @on(Button.Pressed, "#revert-btn")
    def revert(self):
        try:
            if self.manager.reset_to_stock(log_callback=lambda msg: self.log_message(f"[yellow]{msg}[/yellow]")):
                 self.notify("Reverted to stock configuration.")
                 self.log_message("[green]Reverted to stock configuration.[/green]")
            else:
                 self.notify("Could not revert (no stock backup found).", severity="warning")
                 self.log_message("[bold red]Failed to revert: No stock backup found.[/bold red]")
        except Exception as e:
             self.notify(f"Error reverting: {e}", severity="error")
             self.log_message(f"[bold red]Error reverting:[/bold red] {e}")

    @on(Button.Pressed, "#close-btn")
    def close_screen(self):
        self.app.pop_screen()

class TaskDescriptionScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, title, content, steps=None):
        super().__init__()
        self.task_title = title
        self.task_content = content
        self.task_steps = steps or []

    def compose(self) -> ComposeResult:
        with Vertical(id="task_desc_container"):
            yield Label(self.task_title, id="task_desc_title")
            with ScrollableContainer(id="task_desc_text_container"):
                yield Label(self.task_content, id="task_desc_text")
                
                if self.task_steps:
                    yield Label("\n[bold]Actions to be executed:[/bold]", classes="desc-label-header")
                    for i, step in enumerate(self.task_steps, 1):
                        yield Label(f"{i}. {step}", classes="desc-value")
                        
            with Horizontal(id="app_desc_actions"):
                yield Button("Close", variant="default", id="close_desc_btn")

    @on(Button.Pressed, "#close_desc_btn")
    def close_screen(self):
        self.dismiss()

class FirewallSelectionScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, detected_apps, selections_dict):
        super().__init__()
        self.detected_apps = detected_apps
        self.selections_dict = selections_dict

    def compose(self) -> ComposeResult:
        with Vertical(id="task_desc_container"): # Reuse existing styling
            yield Label("Firewall Configuration", id="task_desc_title")
            yield Label("Select which applications should have their ports opened.", classes="instruction_label")
            
            yield DataTable(id="firewall_table", cursor_type="cell")
            
            with Horizontal(id="app_desc_actions"):
                yield Button("Save & Close", variant="primary", id="close_fw_btn")

    def on_mount(self):
        table = self.query_one("#firewall_table", DataTable)
        table.add_columns("Select", "App Name", "Ports")
        
        found_any = False
        for app in self.detected_apps:
            found_any = True
            # Default to True (checked) if not in global dict yet
            is_selected = self.selections_dict.get(app['pkg'], True)
            check_mark = r"\[x]" if is_selected else r"\[ ]"
            
            table.add_row(
                check_mark,
                app['name'],
                ", ".join(app['ports']),
                key=app['pkg']
            )
        
        if not found_any:
            self.query_one(".instruction_label", Label).update("No applications with port requirements detected.")

    @on(DataTable.CellSelected, "#firewall_table")
    def on_cell_selected(self, event: DataTable.CellSelected):
        if event.coordinate.column == 0:
            table = event.data_table
            current_val = table.get_cell_at(event.coordinate)
            new_val = r"\[ ]" if r"\[x]" in str(current_val) else r"\[x]"
            table.update_cell_at(event.coordinate, new_val)
            
            # Update dict immediately
            row_key = event.cell_key.row_key.value
            is_checked = r"\[x]" in new_val
            self.selections_dict[row_key] = is_checked

    @on(Button.Pressed, "#close_fw_btn")
    def close_screen(self):
        self.dismiss()

class UninstallConfirmationScreen(ModalScreen):
    """Modal screen to confirm uninstallation."""
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, count):
        super().__init__()
        self.count = count

    def compose(self) -> ComposeResult:
        with Vertical(id="uninstall_confirm_container"):
            yield Label(f"Are you sure you want to uninstall {self.count} applications?", id="uninstall_confirm_title")
            with Horizontal(id="uninstall_confirm_actions"):
                yield Button("Cancel", variant="primary", id="cancel_btn")
                yield Button("Proceed", variant="error", id="proceed_btn")

    @on(Button.Pressed, "#cancel_btn")
    def cancel(self):
        self.dismiss(False)

    @on(Button.Pressed, "#proceed_btn")
    def proceed(self):
        self.dismiss(True)

class UninstallSafetyScreen(ModalScreen):
    """Safety screen for uninstallation (irreversible action)."""
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="uninstall_safety_container"):
            yield Label("DANGER: This action is irreversible.", classes="danger-title")
            
            warning_text = (
                "You are about to remove selected applications. This will delete application files "
                "and may remove personal configuration data.\n\n"
                "To use these applications again, you will need to reinstall them.\n\n"
                "Type 'UNINSTALL' to confirm."
            )
            yield Label(warning_text, classes="danger-instruction")
            
            yield Input(placeholder="UNINSTALL", id="safety_input")
            with Horizontal(id="uninstall_safety_actions"):
                yield Button("Cancel", variant="primary", id="cancel_safety_btn")
                yield Button("Confirm Uninstall", variant="error", id="confirm_uninstall_btn", disabled=True)
    @on(Input.Changed, "#safety_input")
    def on_input_changed(self, event: Input.Changed):
        confirm_btn = self.query_one("#confirm_uninstall_btn", Button)
        if event.value == "UNINSTALL":
            confirm_btn.disabled = False
        else:
            confirm_btn.disabled = True

    @on(Button.Pressed, "#cancel_safety_btn")
    def cancel(self):
        self.dismiss(False)

    @on(Button.Pressed, "#confirm_uninstall_btn")
    def confirm(self):
        self.dismiss(True)
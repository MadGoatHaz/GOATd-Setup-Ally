from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static, RadioSet, RadioButton, RichLog, Input, Checkbox, DataTable
from textual.containers import Grid, Vertical, Horizontal, Container
from textual import on, work
import asyncio
import shlex
import subprocess
import pyperclip
from gpu import get_system_gpu_info
from gpu_installer import get_installation_plan, generate_installation_command
from rich.markup import escape

class GSPManagerScreen(ModalScreen):
    """Screen for Nvidia GSP Firmware Management."""
    
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Vertical(id="gsp_manager_container"):
            yield Label("Nvidia GSP Firmware Manager", id="gsp_title")
            
            # Status Section
            with Container(classes="info-box"):
                yield Label("Status: Checking...", id="gsp_status_label")
                yield Label(
                    "Disabling GSP Firmware can fix stuttering and frame drops on Turing/Ampere/Ada (RTX 20/30/40) cards on Linux.\n"
                    "It reverts the driver to using the CPU for initialization tasks instead of the GPU's GSP processor.",
                    classes="info-text"
                )
            
            yield Label("Operation Log:", classes="section-title")
            yield RichLog(id="gsp_log", markup=True, wrap=True)
            
            with Horizontal(id="gsp_actions"):
                yield Button("Apply Fix (Disable GSP)", variant="warning", id="btn_gsp_disable", disabled=True)
                yield Button("Revert to Stock (Enable GSP)", variant="success", id="btn_gsp_enable", disabled=True)
                yield Button("Close", variant="default", id="btn_gsp_close")

    def on_mount(self):
        self.check_status()

    def check_status(self):
        """Checks current GSP status via the script."""
        self.log_message("[dim]Checking GSP status...[/dim]")
        try:
            # First try without sudo (works if files are readable)
            # If that fails, we might need to prompt, but for 'check' we want to avoid full suspend if possible.
            # src/gsp_manager.py --check prints ENABLED or DISABLED and exits 0 usually.
            
            cmd = ["python3", "src/gsp_manager.py", "--check"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if res.returncode == 0:
                status = res.stdout.strip()
                if "INCOMPATIBLE_BLACKWELL" in status:
                    self.update_status("INCOMPATIBLE_BLACKWELL")
                elif "INCOMPATIBLE_OPEN" in status:
                    self.update_status("INCOMPATIBLE_OPEN")
                elif "INCOMPATIBLE_NO_DRIVER" in status:
                    self.update_status("INCOMPATIBLE_NO_DRIVER")
                elif "DISABLED" in status:
                    self.update_status("DISABLED")
                else:
                    self.update_status("ENABLED")
            else:
                 # Attempt with sudo if failed (might prompt in terminal if we didn't suspend?
                 # actually capturing output with sudo without suspend will fail if password needed)
                 self.log_message("[yellow]Could not read config without sudo. Assuming ENABLED or blocked.[/yellow]")
                 self.log_message(f"[dim]Error: {escape(res.stderr)}[/dim]")
        except Exception as e:
            self.log_message(f"[red]Exception checking status: {escape(str(e))}[/red]")

    def update_status(self, status):
        status_lbl = self.query_one("#gsp_status_label", Label)
        btn_disable = self.query_one("#btn_gsp_disable", Button)
        btn_enable = self.query_one("#btn_gsp_enable", Button)
        
        if status == "INCOMPATIBLE_BLACKWELL":
            status_lbl.update("GSP Firmware: [bold red]UNSUPPORTED: RTX 5000 (Blackwell) Detected[/bold red]")
            btn_disable.disabled = True
            btn_enable.disabled = True
        elif status == "INCOMPATIBLE_OPEN":
            status_lbl.update(
                "GSP Firmware: [bold red]Not Supported (Open Source Driver)[/bold red]\n"
                "[dim]You must switch to 'nvidia-dkms' (Proprietary) to disable GSP.\n"
                "(Note: RTX 5000 series requires Open Modules and cannot disable GSP).[/dim]"
            )
            btn_disable.disabled = True
            btn_enable.disabled = True
        elif status == "INCOMPATIBLE_NO_DRIVER":
            status_lbl.update("GSP Firmware: [bold red]ERROR: No Proprietary Nvidia Driver Found[/bold red]")
            btn_disable.disabled = True
            btn_enable.disabled = True
        elif status == "ENABLED":
            status_lbl.update("GSP Firmware: [bold green]Enabled (Default)[/bold green]")
            btn_disable.disabled = False
            btn_enable.disabled = True
        else: # DISABLED
            status_lbl.update("GSP Firmware: [bold yellow]Disabled (Fix Applied)[/bold yellow]")
            btn_disable.disabled = True
            btn_enable.disabled = False
            
    def log_message(self, message):
        log = self.query_one("#gsp_log", RichLog)
        log.write(message)

    def run_gsp_operation(self, action):
        """Runs enable/disable operation using ExecutionModal."""
        arg = "--disable" if action == "disable" else "--enable"
        cmd = f"sudo python3 src/gsp_manager.py {arg}"
        
        self.log_message(f"[bold blue]Launching: {escape(cmd)}[/bold blue]")
        self.app.push_screen(ExecutionModal(cmd), self.on_gsp_finished)

    def on_gsp_finished(self, result=None):
        self.log_message("[bold]Operation finished. Re-checking status...[/bold]")
        self.check_status()

    @on(Button.Pressed, "#btn_gsp_disable")
    def disable_gsp(self):
        self.run_gsp_operation("disable")

    @on(Button.Pressed, "#btn_gsp_enable")
    def enable_gsp(self):
        self.run_gsp_operation("enable")

    @on(Button.Pressed, "#btn_gsp_close")
    def close_screen(self):
        self.dismiss()

class ExecutionModal(ModalScreen):
    """
    Modal to execute a command and show output.
    """
    CSS = """
    ExecutionModal {
        align: center middle;
        background: $background 80%;
    }
    ExecutionModal #exec-dialog {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        layout: vertical;
        padding: 1;
    }
    ExecutionModal #exec-output {
        height: 1fr;
        border: solid $secondary;
        background: $surface-darken-1;
        margin-top: 1;
        margin-bottom: 1;
    }
    ExecutionModal #exec-controls {
        height: auto;
        align: center middle;
    }
    ExecutionModal Button {
        margin: 0 1;
    }
    """

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        with Container(id="exec-dialog"):
            yield Label(f"Executing Command", classes="section-title")
            yield Label(f"[dim]{self.command}[/dim]")
            yield RichLog(id="exec-output", markup=True)
            with Horizontal(id="exec-controls"):
                yield Button("Copy Logs", id="btn_copy_logs", variant="primary", disabled=True)
                yield Button("Close", id="btn_close_exec", variant="error", disabled=True)

    def on_mount(self):
        self.run_process()

    @work(exclusive=True)
    async def run_process(self):
        log = self.query_one("#exec-output", RichLog)
        log.write(f"[bold blue]Command:[/bold blue] {escape(self.command)}\n")
        
        try:
            # Use shell execution to properly handle chained commands (&&) and bashisms
            process = await asyncio.create_subprocess_shell(
                self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                executable='/bin/bash'
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                log.write(escape(line.decode().strip()))
            
            await process.wait()
            
            if process.returncode == 0:
                log.write("\n[green]Process finished successfully.[/green]")
            else:
                log.write(f"\n[red]Process exited with error code {process.returncode}[/red]")
                
        except Exception as e:
            log.write(f"\n[red]Failed to start process: {escape(str(e))}[/red]")
            
        self.query_one("#btn_close_exec", Button).disabled = False
        self.query_one("#btn_copy_logs", Button).disabled = False

    @on(Button.Pressed, "#btn_copy_logs")
    def copy_logs(self):
        log = self.query_one("#exec-output", RichLog)
        content = "\n".join([strip.text for strip in log.lines])
        pyperclip.copy(content)
        self.notify("Logs copied to clipboard")

    @on(Button.Pressed, "#btn_close_exec")
    def close(self):
        self.dismiss()

class PowerLimitModal(ModalScreen):
    """
    Modal to ask for Power Limit wattage.
    """
    CSS = """
    PowerLimitModal {
        align: center middle;
        background: $background 80%;
    }
    PowerLimitModal #pl-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    PowerLimitModal .section-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    PowerLimitModal Input {
        margin: 1 0;
    }
    PowerLimitModal #pl-controls {
        margin-top: 1;
        align: center middle;
        height: auto;
    }
    PowerLimitModal Button {
        margin: 0 1;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="pl-dialog"):
            yield Label("Configure Nvidia Power Limit", classes="section-title")
            yield Label("Enter the desired power limit in Watts (e.g. 250):")
            yield Input(placeholder="Watts", id="input_watts", type="number")
            with Horizontal(id="pl-controls"):
                yield Button("Cancel", id="btn_pl_cancel", variant="error")
                yield Button("Apply", id="btn_pl_apply", variant="success")

    @on(Button.Pressed, "#btn_pl_cancel")
    def cancel(self):
        self.dismiss(None)

    @on(Button.Pressed, "#btn_pl_apply")
    def apply(self):
        inp = self.query_one("#input_watts", Input)
        if inp.value and inp.value.isdigit():
            self.dismiss(inp.value)
        else:
            self.notify("Please enter a valid number.", severity="error")

class DriverInstallModal(ModalScreen):
    """
    Compact, efficient modal for driver selection.
    Replaces the inline wizard.
    """
    CSS = """
    DriverInstallModal {
        align: center middle;
        background: $background 80%;
    }
    DriverInstallModal #driver-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    DriverInstallModal .section-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }
    DriverInstallModal .option-group {
        border: solid $secondary;
        margin-bottom: 1;
        padding: 0 1;
        height: auto;
    }
    DriverInstallModal Label {
        margin-top: 1;
        margin-bottom: 0;
    }
    DriverInstallModal #dialog-controls {
        align: center middle;
        height: auto;
        margin-top: 2;
    }
    DriverInstallModal Button {
        min-width: 14;
        margin: 0 1;
    }
    """

    def __init__(self, vendor_id: str):
        super().__init__()
        self.vendor_id = vendor_id

    def compose(self) -> ComposeResult:
        with Container(id="driver-dialog"):
            yield Label(f"Configure {str(self.vendor_id).upper()} Drivers", classes="section-title")
            
            yield Label("Select Workloads:")
            with Vertical(id="chk_container", classes="option-group"):
                if self.vendor_id == "nvidia":
                    yield Checkbox("Gaming (Standard)", value=True, id="chk_gaming")
                    yield Checkbox("AI / Compute Stack", id="chk_ai")
                elif self.vendor_id == "amd":
                    yield Checkbox("Standard (Gaming/Desktop)", value=True, id="chk_gaming")
                    yield Checkbox("Workstation / AI (ROCm)", id="chk_ai")
                elif self.vendor_id == "intel":
                    yield Checkbox("Standard (Gaming)", value=True, id="chk_gaming")
                    yield Checkbox("Compute (OpenCL/Level Zero)", id="chk_ai")
                else:
                    yield Checkbox("Standard", value=True, id="chk_gaming")

            yield Label("Select Driver Type:")
            with RadioSet(id="type_radio", classes="option-group"):
                if self.vendor_id == "nvidia":
                    yield RadioButton("Open Source (Recommended)", value=True, id="type_open")
                    yield RadioButton("Proprietary (Closed Source)", id="type_prop")
                    yield RadioButton("Beta (AUR/Newest)", id="type_beta")
                elif self.vendor_id == "amd":
                    yield RadioButton("Open Source (Mesa/RADV) - Recommended", value=True, id="type_open")
                    yield RadioButton("Proprietary (AMDGPU-PRO)", id="type_prop")
                elif self.vendor_id == "intel":
                    yield RadioButton("Open Source (Mesa)", value=True, id="type_open")
                else:
                    yield RadioButton("Standard", value=True, id="type_open")

            with Horizontal(id="dialog-controls"):
                yield Button("Cancel", id="btn_cancel", variant="error")
                yield Button("Review Plan", id="btn_next", variant="success")

    @on(Button.Pressed, "#btn_cancel")
    def cancel(self):
        self.dismiss()

    @on(Button.Pressed, "#btn_next")
    def next_step(self):
        # Gather selections
        chk_gaming = self.query_one("#chk_gaming", Checkbox)
        chk_ai = self.query("#chk_ai").first() if self.query("#chk_ai") else None
        type_radio = self.query_one("#type_radio", RadioSet)
        
        selected_workloads = set()
        if chk_gaming and chk_gaming.value:
            selected_workloads.add("gaming")
        if chk_ai and chk_ai.value:
            selected_workloads.add("ai")
            
        type_id = None
        if type_radio.pressed_button:
            type_id = type_radio.pressed_button.id
                
        if not selected_workloads:
             self.notify("Please select at least one workload", severity="error")
             return
        
        # Generate Plan
        plan = get_installation_plan(self.vendor_id, selected_workloads, type_id)
        
        self.dismiss(plan)


class PlanReviewModal(ModalScreen):
    """
    Modal to review the installation plan before execution.
    """
    CSS = """
    PlanReviewModal {
        align: center middle;
        background: $background 80%;
    }
    PlanReviewModal #plan-dialog {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        layout: vertical;
        padding: 1;
    }
    PlanReviewModal #plan-preview {
        height: 1fr;
        border: solid $secondary;
        background: $surface-darken-1;
        margin-top: 1;
        margin-bottom: 1;
    }
    PlanReviewModal #plan-controls {
        height: auto;
        align: center middle;
    }
    PlanReviewModal Button {
        margin: 0 1;
        width: 1fr;
    }
    """

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        with Container(id="plan-dialog"):
            yield Label("Review Installation Plan", classes="section-title")
            yield Label("The following command will be executed:", classes="info-text")
            yield RichLog(id="plan-preview", markup=True, wrap=True)
            with Horizontal(id="plan-controls"):
                yield Button("Cancel", id="btn_cancel_plan", variant="error")
                yield Button("Begin Install", id="btn_confirm_plan", variant="success")

    def on_mount(self):
        log = self.query_one("#plan-preview", RichLog)
        log.write(escape(self.command))

    @on(Button.Pressed, "#btn_cancel_plan")
    def cancel(self):
        self.dismiss(False)

    @on(Button.Pressed, "#btn_confirm_plan")
    def confirm(self):
        self.dismiss(True)


class GPUConfigWidget(Container):
    """
    Standalone Widget for GPU Configuration.
    Suitable for use in a main application tab.
    """
    CSS = """
    GPUConfigWidget {
        layout: vertical;
        padding: 0 1;
        height: 100%;
        width: 100%;
        overflow: hidden;
    }
    
    GPUConfigWidget #gpu-header {
        text-align: center;
        text-style: bold;
        height: 1;
        margin-bottom: 0;
        color: $accent;
    }

    GPUConfigWidget #discovery-panel {
        height: auto;
        border: solid $secondary;
        margin-bottom: 0;
        padding: 0 1;
        background: $surface-lighten-1;
    }

    GPUConfigWidget #main-layout {
        height: 1fr;
        layout: horizontal;
        margin-top: 1;
    }

    GPUConfigWidget #action-sidebar {
        width: 25;
        height: 100%;
        padding-right: 1;
        border-right: solid $secondary;
        overflow-y: auto;
    }

    GPUConfigWidget #content-area {
        width: 1fr;
        height: 100%;
        padding-left: 1;
        layout: vertical;
    }

    GPUConfigWidget #action-grid {
        grid-size: 1;
        grid-gutter: 0;
        width: 100%;
        height: auto;
    }
    
    GPUConfigWidget #action-grid Button {
        width: 100%;
        margin-bottom: 1;
    }

    GPUConfigWidget .section-title {
        text-style: bold;
        color: $text-muted;
        margin-bottom: 0;
        margin-top: 0;
        padding-bottom: 1;
    }

    
    GPUConfigWidget #gpu_log {
        height: 25%;
        min-height: 3;
        border: solid $secondary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("GPU Management", id="gpu-header")
        
        # Info Panel
        yield Label("System Status", classes="section-title")
        with Container(id="discovery-panel"):
            yield DataTable(id="gpu_info_table")

        # Main Layout
        with Horizontal(id="main-layout"):
            # Left Sidebar (Actions)
            with Vertical(id="action-sidebar"):
                yield Label("Actions", classes="section-title")
                with Grid(id="action-grid"):
                    yield Button("Install/Update Drivers", id="btn_drivers", variant="primary")
                    yield Button("Manage GSP Firmware", id="btn_gsp", variant="primary")
                    yield Button("Auto-Tune Power Limits", id="btn_power", variant="warning")

            # Right Content Area (Log Only)
            with Vertical(id="content-area"):
                # Local Log
                yield Label("Log", classes="section-title")
                yield RichLog(id="gpu_log", markup=True)

    def on_mount(self):
        table = self.query_one("#gpu_info_table", DataTable)
        table.add_columns("Device", "Driver Version", "Driver Type", "GSP Firmware")
        self.refresh_gpu_info()

    def refresh_gpu_info(self):
        table = self.query_one("#gpu_info_table", DataTable)
        table.clear()

        data = get_system_gpu_info()
        
        gpus = data.get("gpus", [])
        gsp_status = data.get("gsp_status", "Unknown")
        
        # Reset vendor_id
        self.vendor_id = None
        
        if not gpus:
            # Handle no GPUs case if needed, possibly add a row stating so
            pass
        else:
            for gpu in gpus:
                if not self.vendor_id and "vendor_id" in gpu:
                    self.vendor_id = gpu["vendor_id"]
                    
                vendor = gpu.get('vendor', 'Unknown')
                model = gpu.get('model', 'Unknown')
                driver = gpu.get('driver', 'Unknown')
                driver_type = gpu.get('driver_type', 'Unknown')
                
                device_str = f"{vendor} {model}"
                
                # Style Driver Type
                dt_styled = driver_type
                if "Open Source" in driver_type:
                    dt_styled = f"[green]{driver_type}[/green]"
                elif "Beta" in driver_type:
                    dt_styled = f"[yellow]{driver_type}[/yellow]"
                elif "Proprietary" in driver_type:
                    dt_styled = f"[red]{driver_type}[/red]"
                
                # Style GSP Firmware
                gsp_styled = gsp_status
                if "Enabled" in gsp_status:
                    gsp_styled = f"[green]{gsp_status}[/green]"
                elif "Disabled" in gsp_status:
                    gsp_styled = f"[red]{gsp_status}[/red]"

                table.add_row(device_str, driver, dt_styled, gsp_styled)

    def log_msg(self, msg):
        self.query_one("#gpu_log", RichLog).write(msg)

    @on(Button.Pressed, "#btn_drivers")
    def start_driver_install(self):
        self.log_msg("Starting driver configuration...")
        self.app.push_screen(DriverInstallModal(self.vendor_id), self.on_plan_ready)

    def on_plan_ready(self, plan):
        if not plan:
            return
        
        # Construct the full shell command string
        self.pending_command = generate_installation_command(plan)
        
        # Show review modal
        self.app.push_screen(PlanReviewModal(self.pending_command), self.handle_plan_confirmation)

    def handle_plan_confirmation(self, confirmed: bool):
        if confirmed:
            self.app.push_screen(ExecutionModal(self.pending_command))
        else:
            self.log_msg("Installation cancelled by user.")

    @on(Button.Pressed, "#btn_gsp")
    def open_gsp_manager(self):
        self.log_msg("Opening GSP Manager...")
        self.app.push_screen(GSPManagerScreen())

    @on(Button.Pressed, "#btn_power")
    def apply_power_limits(self):
        self.app.push_screen(PowerLimitModal(), self.configure_power_limit)

    def configure_power_limit(self, wattage: str | None):
        """
        Creates the systemd service for the specified wattage.
        """
        if not wattage:
            return

        self.log_msg(f"[blue]Configuring Nvidia Power Limit to {wattage}W...[/blue]")

        service_content = f"""[Unit]
Description=Set NVIDIA Power Limit
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pl {wattage}

[Install]
WantedBy=multi-user.target
"""
        # We use bash -c to handle the pipe to sudo tee within the execution modal's context
        cmd = f"""bash -c "echo '{service_content}' | sudo tee /etc/systemd/system/nvidia-power-limit.service && sudo systemctl daemon-reload && sudo systemctl enable --now nvidia-power-limit.service" """
        
        self.app.push_screen(ExecutionModal(cmd))

class GPUConfigScreen(ModalScreen):
    """
    Wrapper class to display GPUConfigWidget as a modal.
    Preserves backward compatibility for existing callers.
    """
    CSS = """
    GPUConfigScreen {
        align: center middle;
        background: $background 80%;
    }
    
    GPUConfigScreen #gpu-dialog-wrapper {
        width: 85%;
        height: 85%;
        background: $surface;
        border: thick $primary;
        layout: vertical;
    }
    
    GPUConfigScreen #modal-footer-container {
        height: auto;
        dock: bottom;
        padding: 1;
        align: center middle;
        background: $surface-darken-1;
    }
    
    """
    def compose(self) -> ComposeResult:
        with Container(id="gpu-dialog-wrapper"):
            yield GPUConfigWidget()
            with Container(id="modal-footer-container"):
                 yield Button("Close", id="btn_modal_close", variant="error")

    @on(Button.Pressed, "#btn_modal_close")
    def close_modal(self):
        self.dismiss()

if __name__ == "__main__":
    # Simple test app to run the screen directly
    class GPUApp(App):
        CSS = "Screen { align: center middle; }"
        def on_mount(self):
            # Testing the Widget in a main screen context
            self.mount(GPUConfigWidget())

    app = GPUApp()
    app.run()
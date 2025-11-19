# Design: Printer Auto-Configuration Logic

## Overview
This feature bridges the gap between installing a driver package and actually printing. It allows users to scan for connected printers and register them with CUPS using the installed drivers.

## UI Changes
**File:** `GOATd/src/printer.py`

1.  **New Button**: Add a "Scan & Register Printer" button to the "Driver Management" panel (Right Panel).
2.  **Interaction Flow**:
    *   **Click "Scan & Register"**: Triggers `lpinfo -v`.
    *   **Display Results**: Show a list of discovered devices (URI + Description). We can reuse the `driver_list` widget for this temporarily or use a lightweight Modal.
        *   *Decision*: Reuse `driver_list` area but change the header label to "Discovered Devices". Add a "Cancel / Back" button.
    *   **Select Device**: User selects a printer from the list.
    *   **Auto-Match Driver**: The system attempts to find a matching PPD using `lpinfo -m`.
        *   *Feedback*: Show "Found matching driver: [Driver Name]" or "No match found - Select manually".
    *   **Confirm Registration**: User clicks "Register Printer".

## Logic Flow

### 1. Discovery (`lpinfo -v`)
**Command**: `lpinfo -v`
**Parsing**:
*   Output format: `class uri`
*   **Crucial Filtering**: The command lists *backends* (e.g., `network http`) AND *devices* (e.g., `network ipp://192.168.1.5`).
*   **Filter Rule**: We must ignore lines where the URI is just a scheme without a separator (no `://`).
    *   Keep: `direct usb://...`, `network ipp://...`, `network dnssd://...`
    *   Ignore: `network http`, `network lpd` (unless they have a full URI).
*   **Regex approach**: `^(?P<class>network|direct|dnssd)\s+(?P<uri>[a-z]+://\S+)`
    *   This enforces strict URI format `scheme://...`.

*   **Friendly Name Extraction**:
    *   **USB**: Parse `usb://Make/Model?serial=...` -> Format as "Make Model (USB)".
    *   **Network**: Parse `ipp://IP/path` -> "Network Printer (IPP) at [IP]".
    *   **DNSSD**: `dnssd://...` -> "Bonjour/AirPrint Printer". 

### 2. Driver Matching (`lpinfo -m`)
**Command**: `lpinfo -m`
**Strategy**:
1.  **Get Device Model**: Extract "Model" from the selected URI or ask user to type it if generic.
    *   *Better*: Use the "Search Term" field from the existing UI as the "Model Hint".
2.  **Search PPDs**: Run `lpinfo -m` and filter for the model name.
    *   Example: If user installed `brother-dcpl2550dw`, search for "2550".
3.  **Ranking**:
    *   Prioritize drivers containing "recommended".
    *   Prioritize drivers matching the exact installed package name if known.
    *   Prioritize `lsb/usr/...` or common vendor paths.

### 3. Registration (`lpadmin`)
**Command**: `lpadmin -p [PRINTER_NAME] -v [DEVICE_URI] -P [PPD_PATH] -E`
*   **PRINTER_NAME**: Sanitize the model name (replace spaces with underscores, remove special chars).
*   **PPD_PATH**: The first field from `lpinfo -m` output (e.g., `lsb/usr/brother/...`).
*   `-E`: Enable the printer immediately.

## Implementation Details

### Helper Methods (in `PrinterSetup` class)

#### `get_discovered_devices() -> list[tuple[str, str]]`
*   Executes `lpinfo -v`.
*   Iterates line by line.
*   Applies regex `^(?P<class>network|direct|dnssd)\s+(?P<uri>[a-z]+://\S+)`.
*   If matched, generate friendly name from URI.
*   Returns list of `(Friendly Label, URI)`.

#### `find_best_driver(model_query: str) -> str | None`
*   Executes `lpinfo -m`.
*   Iterates through lines.
*   Checks if `model_query` (case-insensitive) is in the description part.
*   Returns the PPD name (first column).

#### `register_queue(name: str, uri: str, ppd: str)`
*   Executes `lpadmin -p name -v uri -P ppd -E`.

### Async Integration
*   Use `self.run_worker(...)` for all these blocking subprocess calls.
*   Ensure UI updates (disabling buttons, showing spinners) happen on the main thread before/after the worker runs.

# GOAT'd - Setup Ally: Development Documentation

## Architecture

GOAT'd is built using **Python** and the **Textual** TUI (Terminal User Interface) framework. It leverages the power of Python for system operations while providing a rich, interactive console interface.

-   **Core Framework**: Textual (CSS-driven TUI).
-   **Language**: Python 3.
-   **Package Management**: Uses `pacman` and automatically detects AUR helpers (`yay`, `paru`, etc.).
-   **Structure**:
    -   `src/main.py`: Entry point and main application logic.
    -   `src/styles.tcss`: Textual CSS definitions for theming and layout.
    -   `src/apps.py`: Application definitions and installation logic.
    -   `src/printer.py`: Printer setup and driver management.
    -   `src/config.py`: Configuration handling and system tasks.
    -   `src/goatfetch_ui.py`: UI components for GoatFetch and specific configuration screens.

## Implemented Features

1.  **Smart App Installer**:
    -   **UI Refactor**: Replaced simple `SelectionList` with a robust `DataTable`. This allows for multi-column display showing Name, Category, Source, Tier, and Installation Status in a single view.
    -   **Batch Operations**: Install or Uninstall multiple applications at once.
    -   **State Sync**: Real-time updates of installation status.

2.  **System Tasks & Firewall**:
    -   **Granular Firewall Control**: The `FIREWALL_SELECTIONS` state dictionary tracks user preferences for which apps should have ports opened.
    -   **Auto-Detection**: Scans `apps.py` definitions against installed packages to suggest port rules.
    -   **One-Click Configs**: Nvidia Power Limit, Bluetooth, LM Sensors.

3.  **Intelligent Printer Setup**:
    -   Automated installation of CUPS and printer drivers.
    -   Real-time AUR query for driver availability.

4.  **GoatFetch**:
    -   Interactive FastFetch configuration tool.

## Technical Implementation Details

### AUR Helper Detection
The `detect_aur_helper()` function in `src/config.py` iterates through a prioritized list of common AUR helpers (`paru`, `yay`, `trizen`, `pikaur`, `aura`). It uses `shutil.which` to find the first available executable on the user's system. This allows the tool to be agnostic to the user's specific AUR preference.

### Firewall State Management
Firewall configuration uses a global dictionary `FIREWALL_SELECTIONS` (imported from `config.py`) to maintain state between the detection screen and the application phase.
-   **Detection**: `get_firewall_apps_data()` identifies installed apps with port definitions.
-   **Selection**: The `FirewallSelectionScreen` allows users to toggle specific apps. These toggles update `FIREWALL_SELECTIONS`.
-   **Application**: `apply_firewall()` reads this dictionary to generate `firewall-cmd` commands only for the enabled applications.

### UI Components
-   **DataTable Integration**: Both `AppInstaller` and `SystemConfig` now utilize `DataTable` widgets. This provides a structured grid view compared to standard lists, enabling richer metadata display (e.g., showing "Source: AUR" vs "Source: Pacman" inline).
-   **Cell Selection**: Custom event handlers manage checkbox toggling within the table cells, creating a seamless hybrid between a data grid and a checklist.

## Known Issues

### "Green X" Issue (Light Mode)
**Severity**: Cosmetic / Minor
**Description**: In Light Mode, checkboxes in `DataTable` or other custom widgets may retain default styling that conflicts with the light theme contrast.
**Status**: ongoing monitoring.

## Future Roadmap

-   **Expand App Catalog**: Add more developer tools, flatpak support, and snap support.
-   **Dependency Management**: Add a more robust check for system dependencies (git, base-devel) on startup.
-   **Network Integration**: Advanced network management tools.
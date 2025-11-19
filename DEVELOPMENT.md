# GOAT'd - Setup Ally: Development Documentation

## Architecture

GOAT'd is built using **Python** and the **Textual** TUI (Terminal User Interface) framework. It leverages the power of Python for system operations while providing a rich, interactive console interface.

-   **Core Framework**: Textual (CSS-driven TUI).
-   **Language**: Python 3.
-   **Package Management**: Uses `pacman` and `yay` (AUR helper) for application management.
-   **Structure**:
    -   `src/main.py`: Entry point and main application logic.
    -   `src/styles.tcss`: Textual CSS definitions for theming and layout.
    -   `src/apps.py`: Application definitions and installation logic.
    -   `src/printer.py`: Printer setup and driver management.
    -   `src/config.py`: Configuration handling.

## Implemented Features

1.  **Smart App Installer**:
    -   Categorized list of applications (Browsers, Development, Gaming, etc.).
    -   Automatic detection of installed status.
    -   Batch installation using `pacman` or `yay`.

2.  **System Tasks**:
    -   One-click execution of common post-install tasks.
    -   Includes Nvidia driver installation, Firewall setup (UFW), and system updates.

3.  **Intelligent Printer Setup**:
    -   Automated installation of CUPS and printer drivers.
    -   Specific support for Brother printers (e.g., DCP-L2550DW).

4.  **Logs & Diagnostics**:
    -   Integrated logging tab to view operation history and errors.

5.  **Theme System**:
    -   Dynamic theme switching (Light/Dark mode).
    -   Persistent user preferences via `config.json`.

## Known Issues

### The "Green X" Issue (Light Mode)
**Severity**: Cosmetic / Minor
**Description**: In Light Mode, when a `SelectionList` item is highlighted or selected, the checkmark (or "X" mark) retains the default green styling instead of adapting to the light theme's contrast requirements or the specific override styles.
**Technical Detail**: This behavior persists despite extensive CSS overrides in `styles.tcss`. It appears to be tied to the internal widget structure of Textual's `SelectionList` and how it handles state-based styling for the indicator specifically.
**Recommendation**: Resolving this likely requires:
-   A deeper investigation into the `SelectionList` internal renderables.
-   Waiting for an upstream fix or better styling API in Textual.
-   Implementing a custom widget that mimics `SelectionList` but offers granular control over the indicator's rendering.

## Future Roadmap

-   **Fix Styling**: Resolve the "Green X" issue and refine high-contrast modes.
-   **Expand App Catalog**: Add more developer tools, flatpak support, and snap support.
-   **Refine Printer Search & Selection UX**:
    -   Currently, search results are displaying in the 'Installation Log' area instead of correctly populating the 'Select Driver' list. This needs to be fixed so results appear in the SelectionList for easy user interaction.
    -   Optimize the driver selection logic. Ensure that selecting a driver from the list correctly captures the package name and passes it to the installation routine.
-   **Dependency Management**: Add a more robust check for system dependencies (git, base-devel) on startup.
# GOAT'd - Setup Ally

**The ultimate post-install setup tool for Arch and EndeavourOS.**

GOAT'd - Setup Ally is a powerful, terminal-based utility designed to streamline the process of setting up a fresh Arch Linux or EndeavourOS installation. Built with Python and Textual, it offers a modern, keyboard-centric interface to manage applications, system configurations, and hardware setup.

> **Note**: This project is currently in **Beta** and under active development.

## Key Features

*   **Smart App Installer**: browse and batch install essential applications. Automatically detects installed status and handles dependencies via `pacman` and `yay`.
*   **One-Click System Tasks**: Quickly perform critical system operations such as:
    *   Nvidia Driver Installation
    *   Firewall Configuration (UFW)
    *   System Updates
*   **Intelligent Printer Setup**: A guided wizard for setting up CUPS and installing printer drivers (featuring specific support for Brother printers).
*   **Modern TUI**: A responsive, theme-able terminal interface with light and dark mode support.

## Usage

To run GOAT'd - Setup Ally, simply execute the wrapper script from the terminal:

```bash
chmod +x goatd.sh
./goatd.sh
```

## Requirements

*   Arch Linux or EndeavourOS
*   Python 3
*   `pacman`
*   `yay` (recommended for full functionality)
*   Terminal with True Color support (recommended)

## License

[MIT License](LICENSE)
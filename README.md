# GOAT'd - Setup Ally

**The ultimate post-install setup tool for Arch and EndeavourOS.**

GOAT'd - Setup Ally is a powerful, terminal-based utility designed to streamline the process of setting up a fresh Arch Linux or EndeavourOS installation. Built with Python and Textual, it offers a modern, keyboard-centric interface to manage applications, system configurations, and hardware setup.

> **Note**: This project is currently in **Beta** and under active development.

## Key Features

*   **Smart App Installer**: Browse and batch install essential applications. Automatically detects installed status and handles dependencies via `pacman` and `yay`.
*   **One-Click System Tasks**: Quickly perform critical system operations:
    *   Nvidia Driver Installation
    *   Firewall Configuration (UFW)
    *   System Updates
    *   Bluetooth Setup
*   **Intelligent Printer Setup**: A comprehensive wizard for CUPS and printer management.
    *   **Automated Discovery**: Auto-detects network printers (IPP/DNSSD).
    *   **Universal Driver Search**: Real-time AUR query to find and install drivers (e.g., Brother, Epson).
    *   **Manual Configuration**: Register printers by IP/URI if discovery fails.
    *   **Conflict Resolution**: Smart handling of existing printer queues.
*   **Modern TUI**: A responsive, theme-able terminal interface with **Dark** and **Light** mode support.

## Usage

To run GOAT'd - Setup Ally, execute the wrapper script from the terminal:

```bash
chmod +x goatd.sh
./goatd.sh
```

## Requirements

*   Arch Linux or EndeavourOS
*   Python 3
*   `pacman`
*   `yay` (recommended for full functionality)
*   `cups` (for printer management)
*   Terminal with True Color support (recommended)

## Support the Project

If you find GOAT'd useful, consider supporting its development!

*   [**GitHub Sponsors**](https://github.com/sponsors/MadGoatHaz)
*   [**PayPal**](https://www.paypal.com/paypalme/garretthazlett)

## Roadmap

*   **Snap & Flatpak Support**: Expand the app installer to support universal package formats.
*   **Network Integration**: Advanced network management tools.
*   **Enhanced Theming**: More color schemes and customization options.
*   **Dependency Management**: Robust startup checks for system tools.

## License

[MIT License](LICENSE)
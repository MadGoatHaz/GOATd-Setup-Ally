# GOAT'd - Setup Ally

**Transparency and Control for your Arch System.**

GOAT'd - Setup Ally is a unified, portable post-install tool designed for Arch Linux and EndeavourOS. This is a personal project sharing my personal scripts. Unlike opaque "magic scripts" that hide what they're doing, GOAT'd is built on a "Glass Box" philosophy. It empowers you to manage applications, system configurations, and hardware setup with full visibility into every command being executed.

> **Note**: This project is currently in **Beta** and under active development. Feedback is welcome!

## Key Features

*   **Smart Firewall Management**:
    *   **Auto-Detection**: Intelligently scans your installed applications to identify required ports (e.g., Steam, KDE Connect, OBS).
    *   **Granular Control**: Review detected rules and toggle them individually before applying. You decide exactly what opens up.
*   **Transparency First**:
    *   **"Glass Box" Design**: Every operation is previewed. Whether installing a package or writing a config file, you see the exact command or file content before execution.
    *   **Real-time Logging**: Watch operations happen step-by-step in the integrated log viewer.
*   **Intelligent Package Handling**:
    *   **AUR Auto-Detection**: Automatically detects and uses your preferred AUR helper (`paru`, `yay`, `trizen`, `pikaur`, or `aura`).
    *   **Smart App Installer**: Browse categories, see what's already installed, and batch install/uninstall with ease.
*   **GoatFetch**:
    *   A built-in, interactive configuration tool for FastFetch. Browse themes, customize layouts, and make your terminal your own.
*   **Printer Wizard**:
    *   Automated discovery (IPP/DNSSD) and universal driver search (AUR query) to get your printer working without the headache.

## Usage

To run GOAT'd - Setup Ally, simply execute the wrapper script from the terminal:

```bash
chmod +x goatd.sh
./goatd.sh
```

## Disclaimer & Feedback

This tool is a work in progress. While I strive for stability and safety, always review the commands shown in the transparency logs before proceeding.

If you encounter issues or have suggestions, please open an issue on GitHub.
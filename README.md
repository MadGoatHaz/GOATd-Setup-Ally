# GOAT'd - Setup Ally

**Transparency and Control for your Arch System.**

GOAT'd - Setup Ally is a unified, portable post-install tool designed for Arch Linux. This is a personal project sharing my personal scripts. Unlike opaque "magic scripts" that hide what they're doing, GOAT'd is built on a "Glass Box" philosophy. It empowers you to manage applications, system configurations, and hardware setup with full visibility into every command being executed.

> **Note**: This project is currently in **Beta** and under active development. Feedback is welcome!

## Key Features

*   **Apps Management**:
    *   **Smart App Installer**: Browse categories, see what's already installed, and batch install/uninstall with ease.
    *   **Select/Deselect All**: Quickly manage bulk selections for efficient package handling.
    *   **Safe Uninstall**: The "Uninstall Selected" feature includes built-in safety checks to prevent accidental removal of critical system components.
    ![Apps Screenshot](docs/Img/Apps%20Screenshot.png)

*   **System Tasks**:
    *   **Smart Firewall Management**: Auto-detect required ports for installed apps (Steam, KDE Connect, etc.) and review rules before applying.
    *   **Glass Box Transparency**: Every operation is previewed. Click any task to see the exact command or configuration details before execution.
    *   **Granular Control**: Use "Select/Deselect All" or toggle individual tasks to decide exactly what runs on your system.
    ![Tasks Screenshot](docs/Img/Tasks%20Screenshot.png)

*   **Printers**:
    *   **Automated Discovery**: Scans for IPP/DNSSD printers on your network.
    *   **Universal Driver Search**: Automatically queries the AUR for compatible drivers to get your printer setup without the headache.
    ![Printers Screenshot](docs/Img/Printers%20Screenshot.png)

*   **GoatFetch**:
    *   **Auto-Detection**: Automatically checks for `fastfetch` and prompts for installation if missing.
    *   **Interactive Config**: Browse themes, customize layouts, and make your terminal your own with a built-in configuration tool.

*   **Transparency First**:
    *   **Real-time Logging**: Watch operations happen step-by-step in the integrated log viewer.

## Usage

To run GOAT'd - Setup Ally, simply execute the wrapper script from the terminal:

```bash
chmod +x goatd.sh
./goatd.sh
```

## Support the Project

If you find this tool useful, consider supporting its development!

*   [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github)](https://github.com/sponsors/MadGoatHaz)
*   [![PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal)](https://www.paypal.com/paypalme/garretthazlett)

**Policy**: Donations support development. If you donate to the app, any feature requests you have will be pushed to the top of the request list based upon the donation amount.

## Disclaimer & Feedback

This tool is a work in progress. While I strive for stability and safety, always review the commands shown in the transparency logs before proceeding.

If you encounter issues or have suggestions, please open an issue on GitHub.

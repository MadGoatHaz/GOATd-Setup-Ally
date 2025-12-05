# GOAT'd - Setup Ally

**Transparency and Control for your Arch System.**

GOAT'd - Setup Ally is a unified, portable post-install tool designed for Arch Linux. This is a personal project sharing my personal scripts. Unlike opaque "magic scripts" that hide what they're doing, GOAT'd is built on a "Glass Box" philosophy. It empowers you to manage applications, system configurations, and hardware setup with full visibility into every command being executed.

> **Note**: This project is currently in **Beta** and under active development. Feedback is welcome!

## Key Features

### Application Management

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**Smart App Installer**</sub> | <sub>v1.0</sub> | <sub>Browse categories, see what's already installed, and batch install/uninstall with ease.</sub> |
| <sub>**Select/Deselect All**</sub> | <sub>v1.0</sub> | <sub>Quickly manage bulk selections for efficient package handling.</sub> |
| <sub>**Safe Uninstall**</sub> | <sub>v1.0</sub> | <sub>Includes built-in safety checks to prevent accidental removal of critical system components.</sub> |

![Apps Screenshot](docs/Img/Apps%20Screenshot.png)

### System Tasks

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**Smart Firewall Management**</sub> | <sub>v1.0</sub> | <sub>Auto-detect required ports for installed apps (Steam, KDE Connect, etc.) and review rules before applying.</sub> |
| <sub>**Glass Box Transparency**</sub> | <sub>v1.0</sub> | <sub>Every operation is previewed. Click any task to see the exact command or configuration details before execution.</sub> |
| <sub>**Granular Control**</sub> | <sub>v1.0</sub> | <sub>Use "Select/Deselect All" or toggle individual tasks to decide exactly what runs on your system.</sub> |

![Tasks Screenshot](docs/Img/Tasks%20Screenshot.png)

### Printer Management

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**Automated Discovery**</sub> | <sub>v1.0</sub> | <sub>Scans for IPP/DNSSD printers on your network.</sub> |
| <sub>**Universal Driver Search**</sub> | <sub>v1.0</sub> | <sub>Automatically queries the AUR for compatible drivers to get your printer setup without the headache.</sub> |

![Printers Screenshot](docs/Img/Printers%20Screenshot.png)

### GPU Management

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**OS-Aware Installer**</sub> | <sub>v1.1</sub> | <sub>Automatically detects your distro (Arch/EndeavourOS) and hardware to build the perfect driver installation plan.</sub> |
| <sub>**GSP Manager**</sub> | <sub>v1.1</sub> | <sub>Fix stuttering on RTX 20/30/40 series cards by managing Nvidia's GSP firmware safely.</sub> |
| <sub>**Review Plan**</sub> | <sub>v1.1</sub> | <sub>See exactly what packages will be installed and what commands will be run *before* you click confirm.</sub> |
| <sub>***Beta Driver Support***</sub> | <sub>v1.2</sub> | <sub>Optionally install the latest Beta drivers from AUR for cutting-edge performance.</sub> |
| <sub>***Conflict Resolution***</sub> | <sub>v1.2</sub> | <sub>Automatically handles removal of conflicting drivers to ensure a clean install.</sub> |

### GoatFetch

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**Auto-Detection**</sub> | <sub>v1.0</sub> | <sub>Automatically checks for `fastfetch` and prompts for installation if missing.</sub> |
| <sub>**Interactive Config**</sub> | <sub>v1.0</sub> | <sub>Browse themes, customize layouts, and make your terminal your own with a built-in configuration tool.</sub> |

### Transparency & Logging

| Feature | Version | Description |
| :--- | :--- | :--- |
| <sub>**Real-time Logging**</sub> | <sub>v1.0</sub> | <sub>Watch operations happen step-by-step in the integrated log viewer.</sub> |
| <sub>**Copy Logs**</sub> | <sub>v1.0</sub> | <sub>Easily copy execution logs to your clipboard with a single click for sharing or debugging.</sub> |

## Usage

To run GOAT'd - Setup Ally, simply execute the wrapper script from the terminal. The script will automatically check for and install necessary dependencies (like python, pip, and system clipboard tools).

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

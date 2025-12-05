# GOAT'd - Setup Ally

**Transparency and Control for your Arch System.**

GOAT'd - Setup Ally is a unified, portable post-install tool designed for Arch Linux. This is a personal project sharing my personal scripts. Unlike opaque "magic scripts" that hide what they're doing, GOAT'd is built on a "Glass Box" philosophy. It empowers you to manage applications, system configurations, and hardware setup with full visibility into every command being executed.

> **Note**: This project is currently in **Beta** and under active development. Feedback is welcome!

## Key Features

*   **Apps Management**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **Smart App Installer** | v1.0 | Browse categories, see what's already installed, and batch install/uninstall with ease. |
    | **Select/Deselect All** | v1.0 | Quickly manage bulk selections for efficient package handling. |
    | **Safe Uninstall** | v1.0 | Includes built-in safety checks to prevent accidental removal of critical system components. |

    ![Apps Screenshot](docs/Img/Apps%20Screenshot.png)

*   **System Tasks**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **Smart Firewall Management** | v1.0 | Auto-detect required ports for installed apps (Steam, KDE Connect, etc.) and review rules before applying. |
    | **Glass Box Transparency** | v1.0 | Every operation is previewed. Click any task to see the exact command or configuration details before execution. |
    | **Granular Control** | v1.0 | Use "Select/Deselect All" or toggle individual tasks to decide exactly what runs on your system. |

    ![Tasks Screenshot](docs/Img/Tasks%20Screenshot.png)

*   **Printers**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **Automated Discovery** | v1.0 | Scans for IPP/DNSSD printers on your network. |
    | **Universal Driver Search** | v1.0 | Automatically queries the AUR for compatible drivers to get your printer setup without the headache. |

    ![Printers Screenshot](docs/Img/Printers%20Screenshot.png)

*   **GPU Management**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **OS-Aware Installer** | v1.1 | Automatically detects your distro (Arch/EndeavourOS) and hardware to build the perfect driver installation plan. |
    | **GSP Manager** | v1.1 | Fix stuttering on RTX 20/30/40 series cards by managing Nvidia's GSP firmware safely. |
    | **Review Plan** | v1.1 | See exactly what packages will be installed and what commands will be run *before* you click confirm. |
    | ***Beta Driver Support*** | v1.2 | Optionally install the latest Beta drivers from AUR for cutting-edge performance. |
    | ***Conflict Resolution*** | v1.2 | Automatically handles removal of conflicting drivers to ensure a clean install. |

*   **GoatFetch**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **Auto-Detection** | v1.0 | Automatically checks for `fastfetch` and prompts for installation if missing. |
    | **Interactive Config** | v1.0 | Browse themes, customize layouts, and make your terminal your own with a built-in configuration tool. |

*   **Transparency First**:

    | Feature | Version | Description |
    | :--- | :--- | :--- |
    | **Real-time Logging** | v1.0 | Watch operations happen step-by-step in the integrated log viewer. |
    | **Copy Logs** | v1.0 | Easily copy execution logs to your clipboard with a single click for sharing or debugging. |

## Usage

To run GOAT'd - Setup Ally, simply execute the wrapper script from the terminal. The script will automatically check for and install necessary dependencies (like python, pip, and system clipboard tools).

```bash
chmod +x goatd.sh
./goatd.sh
```

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

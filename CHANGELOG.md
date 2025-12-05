# Changelog

## [1.2.0] - 2025-12-05

### Added
- **Nvidia Beta Driver Support:** Added optional support for Nvidia Beta drivers via AUR. This allows users to test the absolute latest features and fixes before they reach the stable repositories.
- **Advanced Conflict Resolution:** Implemented a bidirectional conflict resolution system for Nvidia drivers. The installer now intelligently identifies conflicting packages (e.g., `nvidia-dkms` vs `nvidia-beta-dkms`) and uses `pacman -Rdd` to remove the old driver stack without breaking dependencies or triggering cascading removals. This ensures a clean slate for the new driver installation.
- **Reliable Initramfs Regeneration:** The system now automatically detects the active initramfs generator (`mkinitcpio` or `dracut`) and triggers the appropriate rebuild command after driver changes, preventing unbootable states.

### Changed
- **GPU UI Refactor:** The GPU Status Interface has been completely redesigned using a colored `DataTable` for better readability and status-at-a-glance.
- **Default Driver Policy:** Switched the default recommended driver for compatible cards to the Open Source kernel modules (`nvidia-open`), aligning with modern Arch Linux recommendations.

### Community Feedback
- **`goatd.sh` Fix (Thanks @MorbidShell):** Addressed GitHub issue regarding `yay` installation logic. Previously, `goatd.sh` would incorrectly attempt to use `pacman` to install `yay` in certain edge cases. The logic has been patched to correctly clone and build `yay` from the AUR if no helper is detected, or respect an existing installation of `paru`.

### Fixed
- **UI Stability:** Fixed a crash that occurred when log output contained specific bracketed sequences interpreted as markup tags.

## [1.1.0] - 2025-11-29

### Added
- OS-Aware GPU Installer (EndeavourOS support).
- "Review Plan" modal.
- "Copy Logs" button.
- Auto-installation of clipboard tools in `goatd.sh`.

### Changed
- Integrated GSP Manager into the app (no more shell drop).
- Moved GSP UI code to `src/gpu_ui.py`.
- Hardened `goatd.sh` for directory independence.

### Fixed
- `usermod` command crash.
- GSP compatibility check for Open Source modules.
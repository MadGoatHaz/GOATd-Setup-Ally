# Changelog

## [1.2.0] - 2025-12-05

### Added
- Nvidia Beta driver support (AUR).
- Automatic driver conflict resolution (bidirectional removal of old drivers).
- Reliable initramfs regeneration (detects `mkinitcpio`/`dracut`).

### Changed
- GPU Status UI refactored into a colored DataTable.
- Default Nvidia driver is now Open Source.

### Fixed
- `goatd.sh` AUR helper detection (`paru` support) and installation logic.
- UI crash on bracketed log output.

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
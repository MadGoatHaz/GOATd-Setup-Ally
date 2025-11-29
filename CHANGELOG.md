# Changelog

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
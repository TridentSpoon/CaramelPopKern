# CaramelPopKern
Sugar coating the kernel.

A native Linux desktop application for selective kernel and gaming management.
**Version 0.1 is an early functional foundation, not a finished kernel switcher.**

## AppImage releases

AppImage is the release format for all supported distributions. Download the x86_64 `.AppImage`, mark it executable using your file manager's Properties → Permissions, and open it. Python, Tcl/Tk and their runtime libraries are bundled. No installer script or system Python/Tk installation is required for the AppImage.

If FUSE is unavailable, launch with `APPIMAGE_EXTRACT_AND_RUN=1 ./CaramelPopKern-0.1-x86_64.AppImage`. Administrative gaming package operations still use the host package manager, polkit and an available terminal.

This first artifact bundles the current CachyOS runtime. Cross-distro/CPU compatibility has not been verified; release qualification on Ubuntu, Fedora and Omarchy is still required. It is not yet a universal or production-ready release.

## Build an AppImage

Requires local Python/Tk, `appimagetool`, and `desktop-file-validate`:

```sh
python3 packaging/build_appimage.py /path/to/fresh/CaramelPopKern.AppDir /path/to/CaramelPopKern-x86_64.AppImage
```

Set `APPIMAGE_RUNTIME_FILE` to a trusted type-2 runtime if automatic download is unavailable. The builder currently targets x86_64 and uses its build host's runtime. Build artifacts stay outside the source repository.

## Run from source

```sh
./launch.sh
```

Source development requires Python 3 and Tkinter. Ubuntu: `python3-tk`; Fedora: `python3-tkinter`; Arch/CachyOS/Omarchy: `tk` with Python.

## About and upgrades

Version 0.1.1 adds **Help → About & Upgrade**. When running an AppImage, select a downloaded CaramelPopKern AppImage to replace the current file atomically, keeping a separate backup. Close and reopen to use the update. No downloaded update is executed automatically. The app checks file format and x86_64 architecture, but does not verify publisher, version or signatures: choose only trusted project releases. Online release checks remain unavailable until a publishing repository is configured.

## Working now
- Live OS, kernel, GPU, NVIDIA driver and Secure Boot discovery.
- Installed kernel module trees and repository kernel browsing (Arch family; limited Fedora discovery).
- Individually selectable Steam, Lutris, MangoHud, Gamescope, GOverlay, GameMode and Proton-CachyOS when available in configured repositories.
- Heroic appears as unavailable until a supported installation source is integrated.
- Reviewed gaming package installation through the native package manager in an authenticated terminal. Dependencies and conflicts remain visible in its confirmation prompt.
- Persistent requested-package transaction history in `$XDG_STATE_HOME/caramelpopkern` (normally `~/.local/state/caramelpopkern`).
- Rejects arbitrary package names and kernel/driver installation through the gaming path. Does not add repositories automatically.

## Not implemented yet
- Kernel installation, default boot selection and rollback.
- NVIDIA driver switching and driver/kernel compatibility transactions.
- Per-game launcher integrations and automatic performance profiles.
- DLSS/FSR upgrades, HDR/VRR controls and benchmarks.
- Automatic package or settings rollback. History is not a system snapshot.
- OptiScaler installation/activation: OFF and unavailable in this build.

Installing GameMode or a Proton runtime does not automatically configure games to use it. The first build does not change your running kernel, driver, boot configuration or game files. Fedora repositories are queried from cached metadata; refresh them separately if packages appear unavailable.

## Required next milestones
1. Boot adapters for GRUB, systemd-boot and Omarchy's actual boot configuration, with verified fallback entries and recovery instructions.
2. Per-distro kernel sources, headers, DKMS/akmods validation, Secure Boot signing checks and interrupted-transaction handling. Ubuntu CachyOS kernels need a maintained source before enabling installation.
3. NVIDIA adapters using distro-managed packages; coordinated driver/kernel recovery and appropriate open/proprietary module choices for detected hardware.
4. Per-game profiles with exact prior-state backups and conflict-aware restores. Preserve existing software and user modifications.
5. Verified graphics capability catalog. Separate DLSS super resolution, ray reconstruction, frame generation and DLSS 5. Never equate a DLL upgrade with universal feature support.
6. OptiScaler: explicit opt-in per game; no global activation; block known anti-cheat games; unknown status warning; restore only app-managed files with collision checks. No guarantee against bans.
7. Test installs, reboot selection and recovery on disposable VMs for each supported distro before shipping elevated kernel/driver actions.

## Tests
```sh
python3 -m unittest discover -s tests -v
```

No root credentials are stored. Elevated operations use fixed argument lists without a shell. Repository dependencies can change between review and execution, so the native package manager's final prompt must be reviewed. No NVIDIA `.run` installers, overclocking, security-mitigation changes or anti-cheat bypasses.

#!/usr/bin/env bash
# CaramelPopKern user installer. Elevation is limited to fixed dependency commands.
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mode=zenity
if ! command -v zenity >/dev/null 2>&1; then
    if command -v kdialog >/dev/null 2>&1; then mode=kdialog
    else printf '%s\n' 'A graphical installer requires Zenity or KDialog. Install either with your software manager, then reopen this installer.'; exit 1; fi
fi
info() { if [[ $mode == zenity ]]; then zenity --info --title='CaramelPopKern Installer' --width=520 --text="$1"; else kdialog --title 'CaramelPopKern Installer' --msgbox "$1"; fi; }
error() { if [[ $mode == zenity ]]; then zenity --error --title='CaramelPopKern Installer' --width=520 --text="$1"; else kdialog --title 'CaramelPopKern Installer' --error "$1"; fi; }
ask() { if [[ $mode == zenity ]]; then zenity --question --title='CaramelPopKern Installer' --width=540 --text="$1"; else kdialog --title 'CaramelPopKern Installer' --yesno "$1"; fi; }
if [[ ${EUID} == 0 ]]; then error 'Run this installer as your regular user. Administrator authentication is requested only for missing dependencies.'; exit 1; fi
for file in app.py backend.py launch.sh; do
    if [[ ! -f "$source_dir/$file" ]]; then error "Missing application file: $file. Extract the complete archive first."; exit 1; fi
done
install_root="${XDG_DATA_HOME:-$HOME/.local/share}"
app_dir="$install_root/caramelpopkern"
menu_dir="$install_root/applications"
if [[ "$install_root" != /* || "$install_root" == *$'\n'* || "$install_root" == *$'\r'* ]]; then error 'The application data directory must be an absolute path without line breaks.'; exit 1; fi
ask "Install CaramelPopKern for your user account?\n\nFiles: $app_dir\nA launcher will be added to your application menu.\n\nThis early version offers system discovery and reviewed gaming installs. Kernel/driver switching and automatic rollback are not implemented. No gaming tweaks are applied by installation." || exit 0
if ! python3 -c 'import tkinter; import _tkinter' >/dev/null 2>&1; then
    command -v pkexec >/dev/null 2>&1 || { error 'Polkit (pkexec) is needed to install missing Python/Tk dependencies. Install Python and Tkinter using your software manager, then retry.'; exit 1; }
    if command -v pacman >/dev/null 2>&1; then deps=(pacman -S --needed --noconfirm python tk)
    elif command -v apt-get >/dev/null 2>&1; then deps=(apt-get install -y python3 python3-tk)
    elif command -v dnf >/dev/null 2>&1; then deps=(dnf install -y python3 python3-tkinter)
    else error 'Unsupported package manager. Install Python 3 and Tkinter using your software manager.'; exit 1; fi
    ask "Python/Tk GUI dependencies are missing. Install them using administrator authentication?\n\nCommand: ${deps[*]}\n\nYour package manager will also install required dependencies." || exit 0
    dependency_log="$(mktemp)"
    if ! pkexec "${deps[@]}" >"$dependency_log" 2>&1; then
        error "Dependency installation failed or was cancelled.\n\n$(tail -c 1800 "$dependency_log")"; rm -f -- "$dependency_log"; exit 1
    fi
    rm -f -- "$dependency_log"
    python3 -c 'import tkinter; import _tkinter' >/dev/null 2>&1 || { error 'Python/Tk is still unavailable. Installation stopped.'; exit 1; }
fi
if [[ -L "$app_dir" ]]; then error 'The application folder is a symbolic link. Installation stopped to avoid overwriting another location.'; exit 1; fi
if [[ -e "$app_dir" && ! -f "$app_dir/.caramelpopkern-install" ]]; then error 'The destination already exists and is not managed by this installer. Installation stopped.'; exit 1; fi
mkdir -p -- "$install_root" "$menu_dir"
staging="$(mktemp -d "$install_root/.caramelpopkern-stage.XXXXXX")"
trap 'if [[ -n ${staging:-} && -d $staging ]]; then rm -rf -- "$staging"; fi' EXIT
cp -- "$source_dir/app.py" "$source_dir/backend.py" "$source_dir/launch.sh" "$source_dir/README.md" "$staging/"
cp -- "$source_dir/caramelpopkern.svg" "$staging/"
chmod +x "$staging/launch.sh"
printf '%s\n' 'CaramelPopKern user installation v0.1' > "$staging/.caramelpopkern-install"
if [[ -d "$app_dir" ]]; then
    backup="$install_root/caramelpopkern-backup-$(date +%Y%m%d-%H%M%S)-$$"
    mv -- "$app_dir" "$backup"
fi
mv -- "$staging" "$app_dir"; staging=''
# Desktop Entry quoting (no shell interpolation at launch).
exec_path="$app_dir/launch.sh"
exec_path="${exec_path//\\/\\\\}"; exec_path="${exec_path//\"/\\\"}"; exec_path="${exec_path//\$/\\\$}"; exec_path="${exec_path//\`/\\\`}"; exec_path="${exec_path//%/%%}"
cat > "$menu_dir/caramelpopkern.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=CaramelPopKern
Comment=Sugar coating the kernel — selective Linux gaming management
Exec="$exec_path"
Icon=$app_dir/caramelpopkern.svg
Terminal=false
Categories=System;Settings;Game;
StartupNotify=true
EOF
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$menu_dir" >/dev/null 2>&1 || true; fi
info 'CaramelPopKern is installed. Find it in your application menu.\n\nExisting application files were preserved in a backup folder if this was an update. Your change history is untouched.'
if ask 'Open CaramelPopKern now?'; then "$app_dir/launch.sh" >/dev/null 2>&1 & fi

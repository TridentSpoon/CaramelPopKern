#!/bin/sh
cd "$(dirname "$0")" || exit 1
if ! python3 -c 'import tkinter' 2>/dev/null; then
    printf '%s\n' 'CaramelPopKern requires Python 3 and Tkinter.' 'CachyOS/Arch/Omarchy: sudo pacman -S tk' 'Ubuntu: sudo apt install python3-tk' 'Fedora: sudo dnf install python3-tkinter'
    exit 1
fi
exec python3 app.py

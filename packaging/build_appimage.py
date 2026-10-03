#!/usr/bin/env python3
"""Build an x86_64 AppImage from the local Python/Tk runtime; validate on target distros."""
from pathlib import Path
import os, shutil, subprocess, sys
source=Path(__file__).resolve().parents[1]
stage=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve()
if stage.exists(): raise SystemExit('Use a fresh staging directory')
lib=stage/'usr/lib'; lib.mkdir(parents=True); (stage/'usr/bin').mkdir()
shutil.copy2(sys.executable,stage/'usr/bin/python3')
stdlib=Path(sys.base_prefix)/'lib'/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))
shutil.copytree(stdlib,lib/stdlib.name,ignore=shutil.ignore_patterns('site-packages','__pycache__','test','tests','idlelib','ensurepip','turtledemo'))
for name in ['tcl8.6','tk8.6']: shutil.copytree(Path('/usr/lib')/name,lib/name)
app=stage/'usr/share/caramelpopkern'; app.mkdir(parents=True)
for name in ['app.py','backend.py','caramelpopkern.svg','README.md']: shutil.copy2(source/name,app/name)
# ldd reports transitive dependencies. Include the loader and runtime without
# LD_LIBRARY_PATH, so distro package-manager children use their host libraries.
elves=[stage/'usr/bin/python3']+list((lib/stdlib.name/'lib-dynload').glob('*.so'))
for elf in elves:
 p=subprocess.run(['ldd',str(elf)],capture_output=True,text=True)
 for line in p.stdout.splitlines():
  for token in line.split():
   if token.startswith('/') and Path(token).is_file():
    target=lib/Path(token).name
    if not target.exists(): shutil.copy2(Path(token).resolve(),target)
shutil.copy2(source/'caramelpopkern.svg',stage/'caramelpopkern.svg')
(stage/'caramelpopkern.desktop').write_text('[Desktop Entry]\nType=Application\nName=CaramelPopKern\nComment=Sugar coating the kernel\nExec=caramelpopkern\nIcon=caramelpopkern\nTerminal=false\nCategories=System;Settings;Game;\n')
(stage/'AppRun').write_text('''#!/bin/sh
APPDIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PYTHONHOME="$APPDIR/usr"
export PYTHONNOUSERSITE=1
export TCL_LIBRARY="$APPDIR/usr/lib/tcl8.6"
export TK_LIBRARY="$APPDIR/usr/lib/tk8.6"
exec "$APPDIR/usr/lib/ld-linux-x86-64.so.2" --library-path "$APPDIR/usr/lib" "$APPDIR/usr/bin/python3" "$APPDIR/usr/share/caramelpopkern/app.py" "$@"
'''); (stage/'AppRun').chmod(0o755)
subprocess.run(['desktop-file-validate',str(stage/'caramelpopkern.desktop')],check=True)
output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['appimagetool','--no-appstream',*(['--runtime-file',os.environ['APPIMAGE_RUNTIME_FILE']] if os.environ.get('APPIMAGE_RUNTIME_FILE') else []),str(stage),str(output)],env=dict(os.environ,ARCH='x86_64'),check=True)

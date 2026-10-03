"""User-selected AppImage replacement. Never downloads or executes update files."""
import os, shutil, tempfile
from pathlib import Path
VERSION='0.1.1'
def validate_appimage(path):
 path=Path(path)
 if not path.is_file(): raise ValueError('Select an existing AppImage file.')
 with path.open('rb') as f: header=f.read(20)
 if len(header)<20 or header[:4]!=b'\x7fELF' or header[8:11]!=b'AI\x02':
  raise ValueError('The selected file is not a type-2 AppImage.')
 if header[4]!=2 or header[5]!=1 or header[18:20]!=b'\x3e\x00':
  raise ValueError('This build requires an x86_64 AppImage.')
 return path

def replace_appimage(current, candidate):
 current=Path(current); candidate=validate_appimage(candidate)
 if current.is_symlink(): raise ValueError('Launch the original AppImage file, not a symbolic link, to update.')
 current=current.resolve(); candidate=candidate.resolve()
 if current==candidate: raise ValueError('Choose a different, newer downloaded AppImage.')
 validate_appimage(current)
 if not os.access(current.parent,os.W_OK): raise ValueError('The AppImage folder is not writable. Move it to a folder you own.')
 # Preserve each previous release rather than overwriting a single backup.
 fd,backup_name=tempfile.mkstemp(prefix=current.name+'.previous-',suffix='.AppImage',dir=current.parent)
 os.close(fd); backup=Path(backup_name)
 fd,stage_name=tempfile.mkstemp(prefix='.'+current.name+'.update-',dir=current.parent); os.close(fd); stage=Path(stage_name)
 try:
  shutil.copy2(current,backup)
  shutil.copyfile(candidate,stage); validate_appimage(stage)
  stage.chmod(current.stat().st_mode & 0o777 | 0o100)
  with stage.open('rb') as f: os.fsync(f.fileno())
  os.replace(stage,current)
 except Exception:
  stage.unlink(missing_ok=True)
  # A completed backup is deliberately retained if replacement fails.
  raise
 return backup

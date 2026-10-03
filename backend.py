"""Read-only discovery and reviewed, additive package transactions. No shell execution."""
import json, os, platform, re, shutil, subprocess, time
from pathlib import Path

PACKAGE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9+_.:-]*$')
CATALOG = [
 ('steam', 'Steam', 'Game store and launcher', {'arch':'steam','ubuntu':'steam-installer','fedora':'steam'}),
 ('heroic', 'Heroic', 'Epic, GOG and Amazon launcher', {}),
 ('lutris', 'Lutris', 'Manage games and Wine runners', {'arch':'lutris','ubuntu':'lutris','fedora':'lutris'}),
 ('mangohud', 'MangoHud', 'FPS, frame times and hardware overlay', {'arch':'mangohud','ubuntu':'mangohud','fedora':'mangohud'}),
 ('gamescope', 'Gamescope', 'Game compositor and scaling controls', {'arch':'gamescope','ubuntu':'gamescope','fedora':'gamescope'}),
 ('goverlay', 'GOverlay', 'Configure performance overlays', {'arch':'goverlay','ubuntu':'goverlay','fedora':'goverlay'}),
 ('gamemode', 'GameMode', 'Performance adjustments while games run; configure per game', {'arch':'gamemode','ubuntu':'gamemode','fedora':'gamemode'}),
 ('proton', 'Proton-CachyOS', 'Optional per-game compatibility runtime', {'arch':'proton-cachyos-slr'}),
]

def host_env():
 return {k:v for k,v in os.environ.items() if k not in {"PYTHONHOME","PYTHONPATH","TCL_LIBRARY","TK_LIBRARY","LD_LIBRARY_PATH","LD_PRELOAD"}}

def run(args, timeout=30):
 try:
  p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=host_env())
  return p.returncode, p.stdout.strip(), p.stderr.strip()
 except (OSError, subprocess.TimeoutExpired) as e: return 1, '', str(e)

def os_info(path='/etc/os-release'):
 info={}
 try:
  for line in Path(path).read_text().splitlines():
   if '=' in line:
    k,v=line.split('=',1); info[k]=v.strip('"')
 except OSError: pass
 return info

class Backend:
 def __init__(self, state_dir=None):
  self.os=os_info(); ids=self.os.get('ID','')+' '+self.os.get('ID_LIKE','')
  self.family='arch' if 'arch' in ids or 'cachyos' in ids else 'ubuntu' if 'ubuntu' in ids or 'debian' in ids else 'fedora' if 'fedora' in ids else 'unsupported'
  self.manager={'arch':'pacman','ubuntu':'apt-get','fedora':'dnf'}.get(self.family)
  self.state_dir=Path(state_dir or Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'caramelpopkern')
 def installed(self, package):
  if self.family=='arch': return run(['pacman','-Q',package])[0]==0
  if self.family=='ubuntu':
   c,o,_=run(['dpkg-query','-W','-f=${Status}',package]); return c==0 and o=='install ok installed'
  if self.family=='fedora': return run(['rpm','-q',package])[0]==0
  return False
 def available(self, package):
  if not PACKAGE.fullmatch(package): return False
  if self.family=='arch': return run(['pacman','-Si',package])[0]==0
  if self.family=='ubuntu':
   c,o,_=run(['apt-cache','policy',package]); return c==0 and bool(re.search(r'Candidate:\s+(?!\(none\))\S+',o))
  if self.family=='fedora': return run(['dnf','--cacheonly','info','--available',package])[0]==0
  return False
 def packages(self):
  rows=[]
  for key,title,desc,mapping in CATALOG:
   pkg=mapping.get(self.family)
   installed=bool(pkg and self.installed(pkg)); available=bool(pkg and (installed or self.available(pkg)))
   rows.append(dict(key=key,title=title,description=desc,package=pkg,installed=installed,available=available))
  return rows
 def summary(self):
  _,gpu,_=run(['lspci']); gpu='\n'.join(l for l in gpu.splitlines() if any(x in l for x in ['VGA','3D controller','Display controller']))
  _,nv,_=run(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'])
  _,sb,_=run(['mokutil','--sb-state'])
  return {'System':self.os.get('PRETTY_NAME','Unknown Linux'),'Running kernel':platform.release(),'Architecture':platform.machine(),'Graphics':gpu or 'Not detected (lspci unavailable)','NVIDIA running driver':nv or 'Not detected','Secure Boot':sb or 'Unknown','Boot configuration':'GRUB detected' if Path('/boot/grub/grub.cfg').exists() else 'Other / not readable'}
 def kernels(self):
  rows=[]
  try:
   for p in sorted(Path('/usr/lib/modules').iterdir()):
    if p.is_dir(): rows.append({'name':p.name,'state':'Running' if p.name==platform.release() else 'Installed module tree','package':None})
  except OSError: pass
  if self.family=='arch':
   _,o,_=run(['pacman','-Sl'])
   for line in o.splitlines():
    a=line.split()
    if len(a)>2 and re.fullmatch(r'linux(?:-lts|-zen|-hardened|-cachyos(?:-[a-z0-9-]+)?)?',a[1]) and not any(x in a[1] for x in ['headers','nvidia','zfs']):
     rows.append({'name':a[1]+'  '+a[2], 'state':'Package installed' if self.installed(a[1]) else 'Available in '+a[0], 'package':a[1]})
  elif self.family=='fedora':
   for pkg in ['kernel','kernel-cachyos','kernel-cachyos-lts']:
    if self.available(pkg): rows.append({'name':pkg,'state':'Package installed' if self.installed(pkg) else 'Available in configured repositories','package':pkg})
  return rows
 def drivers(self):
  if self.family=='ubuntu':
   _,o,_=run(['ubuntu-drivers','devices']); return o or 'ubuntu-drivers is unavailable or detected no supported devices.'
  if self.family=='arch':
   _,o,_=run(['pacman','-Sl']); return '\n'.join(l for l in o.splitlines() if len(l.split())>1 and re.fullmatch(r'nvidia(?:-open)?(?:-dkms|-lts)?|nvidia-utils',l.split()[1])) or 'No NVIDIA packages found.'
  return 'Fedora driver selection requires RPM Fusion and akmods integration. Switching is not enabled in this build.'
 def plan(self, packages):
  packages=sorted(set(packages))
  if not packages or any(not PACKAGE.fullmatch(p) for p in packages): raise ValueError('Invalid or empty package selection')
  if not self.manager or not shutil.which(self.manager): raise ValueError('Supported package manager not found')
  if any(not self.available(p) for p in packages): raise ValueError('A selected package is unavailable in configured repositories')
  if 'gamemode' in packages and self.installed('ananicy-cpp'): raise ValueError('GameMode conflicts with installed ananicy-cpp. Resolve the conflict before proceeding.')
  # Additive gaming packages only. Kernel/driver operations need dedicated boot/module validation.
  allowed={m.get(self.family) for _,_,_,m in CATALOG}
  if any(p not in allowed for p in packages): raise ValueError('Kernel and driver installation is preview-only until boot and module validation is implemented.')
  packages=[p for p in packages if not self.installed(p)]
  if not packages: raise ValueError('Selected packages are already installed')
  cmd={'arch':['pacman','-S','--needed'],'ubuntu':['apt-get','install'],'fedora':['dnf','install']}[self.family]+packages
  return {'packages':packages,'command':cmd,'created':time.time(),'family':self.family,'status':'planned'}
 def save(self, transaction):
  self.state_dir.mkdir(parents=True,exist_ok=True)
  path=self.state_dir/(str(time.time_ns())+'.json'); path.write_text(json.dumps(transaction,indent=2)); return path
 def history(self):
  if not self.state_dir.exists(): return []
  result=[]
  for p in sorted(self.state_dir.glob('*.json'),reverse=True):
   try: result.append(json.loads(p.read_text()))
   except (OSError,ValueError): pass
  return result

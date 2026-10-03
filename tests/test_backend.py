import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import Backend
class Planning(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.b=Backend(self.temp.name); self.b.family='arch'; self.b.manager='pacman'
 def tearDown(self): self.temp.cleanup()
 def plan(self,packages,installed=()):
  with patch('backend.shutil.which',return_value='/usr/bin/pacman'),patch.object(self.b,'available',return_value=True),patch.object(self.b,'installed',side_effect=lambda p:p in installed): return self.b.plan(packages)
 def test_exact_argv_and_deduplication(self):
  self.assertEqual(self.plan(['lutris','mangohud','lutris'])['command'],['pacman','-S','--needed','lutris','mangohud'])
 def test_injection_rejected(self):
  for p in ['steam;id','--overwrite','$(id)','steam\nreboot']:
   with self.assertRaises(ValueError): self.plan([p])
 def test_kernel_and_driver_changes_blocked(self):
  for p in ['linux-cachyos','nvidia-dkms']:
   with self.assertRaisesRegex(ValueError,'preview-only'): self.plan([p])
 def test_existing_packages_preserved(self):
  self.assertEqual(self.plan(['lutris','steam'],['steam'])['packages'],['lutris'])
 def test_priority_conflict(self):
  with self.assertRaisesRegex(ValueError,'conflicts'): self.plan(['gamemode'],['ananicy-cpp'])
 def test_missing_repository(self):
  with patch('backend.shutil.which',return_value='/usr/bin/pacman'),patch.object(self.b,'available',return_value=False):
   with self.assertRaisesRegex(ValueError,'unavailable'): self.b.plan(['steam'])
 def test_history_roundtrip(self):
  transaction=self.plan(['lutris']); self.b.save(transaction); self.assertEqual(self.b.history(),[transaction])
 def test_other_distro_commands(self):
  for family,manager in [('ubuntu','apt-get'),('fedora','dnf')]:
   self.b.family=family; self.b.manager=manager
   self.assertEqual(self.plan(['lutris'])['command'],[manager,'install','lutris'])
if __name__=='__main__': unittest.main()

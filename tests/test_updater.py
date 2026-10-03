import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from updater import replace_appimage,validate_appimage
HEADER=b'\x7fELF\x02\x01\x01\x00AI\x02'+b'\x00'*7+b'\x3e\x00'
class Updates(unittest.TestCase):
 def test_replacement_retains_backup(self):
  with tempfile.TemporaryDirectory() as d:
   current=Path(d)/'current.AppImage'; new=Path(d)/'new.AppImage'
   current.write_bytes(HEADER+b'old'); new.write_bytes(HEADER+b'new')
   backup=replace_appimage(current,new)
   self.assertEqual(current.read_bytes(),HEADER+b'new'); self.assertEqual(backup.read_bytes(),HEADER+b'old')
 def test_invalid_update_preserves_current(self):
  with tempfile.TemporaryDirectory() as d:
   current=Path(d)/'current.AppImage'; new=Path(d)/'new.AppImage'
   current.write_bytes(HEADER+b'old'); new.write_bytes(b'not an AppImage')
   with self.assertRaises(ValueError): replace_appimage(current,new)
   self.assertEqual(current.read_bytes(),HEADER+b'old')
 def test_same_path_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'a.AppImage'; path.write_bytes(HEADER)
   with self.assertRaises(ValueError): replace_appimage(path,path)
 def test_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d); original=p/'a.AppImage'; new=p/'b.AppImage'; link=p/'link.AppImage'
   original.write_bytes(HEADER); new.write_bytes(HEADER); link.symlink_to(original)
   with self.assertRaises(ValueError): replace_appimage(link,new)

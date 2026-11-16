import sys,unittest,tempfile,shutil,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'src'))
import integrity,adb_runtime,readonly,resources,memory_reader
class SecurityTests(unittest.TestCase):
 def test_bundled_adb_matches_pins(self):integrity.verify_adb(resources.BASE/'adb')
 def test_modified_adb_and_dll_rejected(self):
  for name in integrity.ADB_SHA256:
   with tempfile.TemporaryDirectory() as t:
    for n in integrity.ADB_SHA256:shutil.copyfile(resources.BASE/'adb'/n,Path(t)/n)
    with (Path(t)/name).open('ab') as f:f.write(b'tampered')
    with self.assertRaises(RuntimeError):integrity.verify_adb(t)
 def test_shutdown_never_executes_unverified_adb(self):
  with patch.object(adb_runtime,'verify_adb',side_effect=RuntimeError('tampered')),patch.object(adb_runtime.subprocess,'run') as run:
   adb_runtime.shutdown('untrusted/adb.exe');run.assert_not_called()
 def test_invalid_serials_and_arguments_blocked(self):
  for args in [['-s','-H','devices'],['-s','x\nreboot','shell','id'],['devices\x00'],['-s'],[],['devices',None]]:
   with self.assertRaises(readonly.Blocked):readonly.check(args)
 def test_oversized_transfers_rejected_before_launch(self):
  r=memory_reader.FastReader()
  with patch.object(memory_reader.subprocess,'Popen') as launch:
   for n in [-1,0,16*1024*1024+1]:
    with self.assertRaises(ValueError):r.transfer('dd if=/proc/42/mem bs=4096 skip=1 count=1 status=none',n)
   launch.assert_not_called()
 def test_oversized_and_malformed_json_use_default(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'settings.json'
   for data in [b'['*2000,b' '* (8*1024*1024+1),b'\xff']:
    p.write_bytes(data);self.assertEqual(resources.load_json(p,{}),{})
 def test_atomic_save_does_not_touch_predictable_temp(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'settings.json';decoy=Path(str(p)+'.tmp');decoy.write_text('keep')
   resources.save_json(p,{'a':1});self.assertEqual(json.loads(p.read_text()),{'a':1});self.assertEqual(decoy.read_text(),'keep')
if __name__=='__main__':unittest.main()

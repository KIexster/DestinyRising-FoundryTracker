import unittest,json,sys,os,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'src'))
import tracker,adb_runtime
class DetectionTests(unittest.TestCase):
 def test_no_game_is_actionable(self):
  with patch.object(tracker,'command',return_value='List of devices attached\n'):
   with self.assertRaisesRegex(tracker.TrackerError,'GLOBAL abierto'):tracker.discover('adb','com.netease.g108na')
 def test_multiple_sessions_not_silently_selected(self):
  def fake(adb,args,**kw):return 'List of devices attached\na device\nb device' if args==['devices'] else f'B:boot-{args[1]} P:42'
  with patch.object(tracker,'command',side_effect=fake):
   with self.assertRaisesRegex(tracker.TrackerError,'varias sesiones'):tracker.discover('adb','com.netease.g108na')
 def test_same_instance_listed_twice_is_one_session(self):
  def fake(adb,args,**kw):return 'List of devices attached\n127.0.0.1:16384\tdevice\nemulator-5554\tdevice' if args==['devices'] else 'B:e76ef978 P:2912'
  with patch.object(tracker,'command',side_effect=fake):
   self.assertEqual(tracker.discover('adb','com.netease.g108na'),('127.0.0.1:16384','2912'))
 def test_missing_boot_id_keeps_serials_apart(self):
  def fake(adb,args,**kw):return 'List of devices attached\na device\nb device' if args==['devices'] else 'B: P:42'
  with patch.object(tracker,'command',side_effect=fake):
   with self.assertRaisesRegex(tracker.TrackerError,'varias sesiones'):tracker.discover('adb','com.netease.g108na')
 def test_incompatible_engine_rejected_before_interpreter_read(self):
  def fake(adb,args,**kw):return 'uid=0(root)' if args[-1]=='id' else '1000-3000 r--p 00000000 00:00 0 /x/libGame.so'
  with patch.object(tracker,'command',side_effect=fake),patch.object(tracker.Session,'read',return_value=b'X'*4096),patch.object(tracker.Session,'close'):
   with self.assertRaisesRegex(tracker.TrackerError,'Motor no compatible'):tracker.Session('adb','a','42',{'engine_header_sha256':'wrong'})
 def test_cyclic_map_is_rejected(self):
  r=object.__new__(tracker.Session);values={0x120:0x200,0x210:0x300,0x310:0x400,0x318:0,0x428:1,0x420:0x500,0x510:0x600,0x500:0x500}
  r.q=lambda a:values[a];r.read=lambda a,n: b'\0' if n==1 else (123).to_bytes(8,'little');r.cppstr=lambda a:'aw01a01'
  with self.assertRaisesRegex(tracker.TrackerError,'Mapa inconsistente'):r.int_map(0x100)
class AdbRuntimeTests(unittest.TestCase):
 def test_source_run_uses_bundled_adb_on_private_port(self):
  with patch.dict(os.environ),patch.object(adb_runtime,'BASE',Path('src_dir')):
   self.assertEqual(adb_runtime.prepare(),Path('src_dir')/'adb'/'adb.exe');self.assertEqual(os.environ['ANDROID_ADB_SERVER_PORT'],'5041')
 def test_frozen_run_copies_adb_out_of_temp_folder(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp)/'mei';local=Path(tmp)/'local';(base/'adb').mkdir(parents=True)
   for name in adb_runtime.FILES:(base/'adb'/name).write_bytes(name.encode())
   with patch.dict(os.environ),patch.object(adb_runtime,'BASE',base),patch.object(adb_runtime,'LOCAL',local),patch.object(sys,'_MEIPASS',str(base),create=True),patch.object(adb_runtime,'shutdown') as stop:
    self.assertEqual(adb_runtime.prepare(),local/'adb.exe');stop.assert_not_called()
    self.assertTrue(all((local/n).read_bytes()==n.encode() for n in adb_runtime.FILES))
    adb_runtime.prepare();stop.assert_not_called()
    (base/'adb'/'adb.exe').write_bytes(b'new build');adb_runtime.prepare()
    stop.assert_called_once_with(local/'adb.exe');self.assertEqual((local/'adb.exe').read_bytes(),b'new build')
if __name__=='__main__':unittest.main()

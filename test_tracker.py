import unittest,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'src'))
import tracker
class DetectionTests(unittest.TestCase):
 def test_no_game_is_actionable(self):
  with patch.object(tracker,'command',return_value='List of devices attached\n'):
   with self.assertRaisesRegex(tracker.TrackerError,'GLOBAL abierto'):tracker.discover('adb','com.netease.g108na')
 def test_multiple_sessions_not_silently_selected(self):
  def fake(adb,args,**kw):return 'List of devices attached\na device\nb device' if args==['devices'] else '42'
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
if __name__=='__main__':unittest.main()

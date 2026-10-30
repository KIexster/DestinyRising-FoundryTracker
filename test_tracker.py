import unittest,json,sys,os,tempfile,struct,re
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'src'))
import tracker,adb_runtime,resources
# gallery.UPDATE_BUILD: the reader messages that the window turns into "download the new version".
UPDATE_BUILD=re.compile(r'Build (\S+) no validada\. Esta versión admite (\S+)\.')
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
 def test_unknown_engine_is_read_as_unverified(self):
  maps='1000-3000 r-xp 00000000 00:00 0 /x/libGame.so\n3000-5000 rw-p 00002000 00:00 0 /x/libGame.so\n5000-9000 rw-p 00000000 00:00 0 [anon:.bss]\n9000-a000 rw-p 00000000 00:00 0'
  def fake(adb,args,**kw):return 'uid=0(root)' if args[-1]=='id' else maps
  with patch.object(tracker,'command',side_effect=fake),patch.object(tracker.Session,'read',return_value=b'X'*4096):
   s=tracker.Session('adb','a','42',{'engine_header_sha256':'wrong'})
  self.assertFalse(s.verified_engine);self.assertEqual(s.base,0x1000);self.assertEqual(s.data_ranges,[(0x3000,0x5000),(0x5000,0x9000)])
 def test_cyclic_map_is_rejected(self):
  r=object.__new__(tracker.Session);values={0x120:0x200,0x210:0x300,0x310:0x400,0x318:0,0x428:1,0x420:0x500,0x510:0x600,0x500:0x500}
  r.q=lambda a:values[a];r.read=lambda a,n: b'\0' if n==1 else (123).to_bytes(8,'little');r.cppstr=lambda a:'aw01a01'
  with self.assertRaisesRegex(tracker.TrackerError,'Mapa inconsistente'):r.int_map(0x100)
def fake_memory(runtime=None,size=0x80000,decoy=None):
 """A Session over 'size' bytes of libGame data at 0x200000, with _PyRuntime at 'runtime' (offset into that data)."""
 data=0x200000;mem=bytearray(size);modules=0x900000
 def header(at,interp,main):struct.pack_into('<5i4xQQQQQ',mem,at,1,0,1,1,1,0,0xdead0000,interp,main,1)
 if decoy is not None:header(decoy,data+decoy+0x100,data+decoy+0x200)
 if runtime is not None:
  interp=data+runtime+0xf860;header(runtime,interp,interp)
  struct.pack_into('<Q',mem,interp-data+40,data+runtime);struct.pack_into('<Q',mem,interp-data+0x378,modules)
 s=object.__new__(tracker.Session);s.engine=tracker.engine_config({});s.base=0x100000;s.data_ranges=[(data,data+size)];s.cache={};s.runtime=None;s.blocks=0
 def q(a):
  if not data<=a<data+size-7:raise ValueError('Unmapped pointer')
  return struct.unpack_from('<Q',mem,a-data)[0]
 def block(start,count):s.blocks+=1;return bytes(mem[start-data:start-data+count*4096])
 s.q=q;s.block=block;s.typ=lambda a:'dict' if a==modules else 'int'
 return s,data
class RuntimeSearchTests(unittest.TestCase):
 def test_moved_runtime_found_by_its_header(self):
  s,data=fake_memory(runtime=0x5008,decoy=0x1000)
  self.assertEqual(s.locate([]),data+0x5008-s.base);self.assertEqual(s.runtime,data+0x5008)
 def test_header_across_chunk_boundary(self):
  s,data=fake_memory(runtime=tracker.SCAN_PAGES*4096-8)
  s.locate([]);self.assertEqual(s.runtime,data+tracker.SCAN_PAGES*4096-8)
 def test_known_offset_needs_no_scan(self):
  s,data=fake_memory(runtime=0x5008)
  self.assertEqual(s.locate([data+0x5008-s.base]),data+0x5008-s.base);self.assertEqual(s.blocks,0)
 def test_missing_runtime_is_a_structure_error(self):
  s,data=fake_memory(decoy=0x1000)
  with self.assertRaisesRegex(tracker.StructureError,'intérprete'):s.locate([])
CATALOG=dict(package='p',expected_patch='202610280026',engine_header_sha256='old',weapons=[dict(weapon_id='w1',achievement_id=1,name='W')],collections=[dict(id=1,name='C')])
def fake_session(verified,patch_version,counters):
 class FakeSession:
  header_sha='new';verified_engine=verified;runtime=0x1000;base=0;module_key=1;module_address=2;cache={}
  def __init__(self,*args):pass
  def locate(self,hints,status):return 0x1000
  def module(self,name):return 2
  def modules(self):return 0
  def dict_entries(self,a):return [(1,2)]
  def module_attrs(self,a):return {'PATCH_VERSION':10,'Player':20}
  def string(self,a):return patch_version if a==10 else 'Game.Game'
  def typ(self,a):return 'PlayerAvatar'
  def counters(self,player):return counters()
  def close(self):pass
 return FakeSession
def read_with(session):
 with patch.object(tracker,'discover',return_value=('s','42')),patch.object(tracker,'Session',session),patch.object(tracker,'command',return_value='42'):
  return tracker.collect('adb',CATALOG)
def broken():raise tracker.StructureError('No se reconoce la tabla de propiedades de esta build.')
def maps(finished):return {'AttachmentProcess_weaponKillData':{'w1':5},'Achievement_listenAchiData':{},'Achievement_finishAchiData':finished}
class UnverifiedBuildTests(unittest.TestCase):
 def test_structure_error_on_new_build_asks_for_update(self):
  with self.assertRaises(tracker.TrackerError) as ctx:read_with(fake_session(False,'202611010000',broken))
  self.assertEqual(UPDATE_BUILD.search(str(ctx.exception)).groups(),('202611010000','202610280026'))
 def test_new_build_with_inconsistent_achievements_is_rejected(self):
  with self.assertRaises(tracker.TrackerError) as ctx:read_with(fake_session(False,'202611010000',lambda:maps({'1':1})))
  self.assertTrue(UPDATE_BUILD.search(str(ctx.exception)))
 def test_consistent_new_build_is_shown_as_unverified(self):
  data=read_with(fake_session(False,'202611010000',lambda:maps({})))
  self.assertFalse(data['verified_build']);self.assertEqual(data['engine'],dict(header_sha256='new',runtime_offset='0x1000'));self.assertEqual(data['rows'][0]['kills'],5)
 def test_same_patch_with_new_engine_is_unverified(self):
  self.assertFalse(read_with(fake_session(False,'202610280026',lambda:maps({})))['verified_build'])
 def test_verified_build_keeps_the_original_error(self):
  with self.assertRaisesRegex(tracker.StructureError,'No se reconoce la tabla'):read_with(fake_session(True,'202610280026',broken))
 def test_engine_override_is_merged(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'engine.json';path.write_text(json.dumps(dict(expected_patch='202611010000',engine=dict(runtime_offset='0x7600000'))),'utf-8')
   out=resources.with_engine_override(dict(expected_patch='old',engine=dict(runtime_offset='0x1',interp_modules=888)),path)
  self.assertEqual(out,dict(expected_patch='202611010000',engine=dict(runtime_offset='0x7600000',interp_modules=888)))
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

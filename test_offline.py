import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
for name in ('tracker','adb_runtime','memory_reader','readonly','integrity'):sys.modules[name]=None
import offline
def fixture():
 return dict(captured_at="2026-10-30T12:00:00-03:00",rows=[dict(r,kills=None) for r in offline.CATALOG["weapons"]],summary=[dict(g,progress=0) for g in offline.CATALOG["collections"]])
class OfflineTests(unittest.TestCase):
 def test_export_loads_without_reader_modules(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x.json';p.write_text(json.dumps(fixture()));r=offline.snapshot(p)
  self.assertEqual(len(r['rows']),len(offline.CATALOG['weapons']));self.assertTrue(r['offline'])
 def test_bad_counters_rejected(self):
  base=fixture()
  for val in [-1,True,'123',10**13]:
   base['rows'][0]['kills']=val
   with tempfile.TemporaryDirectory() as t:
    p=Path(t)/'x.json';p.write_text(json.dumps(base))
    with self.assertRaises(ValueError):offline.snapshot(p)
 def test_no_imported_display_strings_are_trusted(self):
  base=fixture();base['rows'][0]['weapon']='UNTRUSTED'
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x.json';p.write_text(json.dumps(base));r=offline.snapshot(p)
  self.assertNotEqual(r['rows'][0]['weapon'],'UNTRUSTED')
if __name__=='__main__':unittest.main()

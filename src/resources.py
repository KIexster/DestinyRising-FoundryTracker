"""Bundled files, the weapon catalog and the small JSON files kept in %APPDATA%\\FoundryTracker."""
import sys,os,json,tempfile
from pathlib import Path
BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
VERSION='1.0.3'
GOAL=1000
HOME=Path(os.environ.get('APPDATA',str(Path.home())))/'FoundryTracker'
SETTINGS=HOME/'settings.json'
def load_json(path,default):
 try:
  with Path(path).open('rb') as stream:raw=stream.read(8*1024*1024+1)
  if len(raw)>8*1024*1024:return default
  return json.loads(raw.decode('utf-8'))
 except (OSError,ValueError,RecursionError):return default
def save_json(path,data):
 temp=None
 try:
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as stream:
   temp=Path(stream.name);json.dump(data,stream,ensure_ascii=False)
  os.replace(temp,path)
 except OSError:pass
 finally:
  if temp is not None:temp.unlink(missing_ok=True)

def load_settings():
 data=load_json(SETTINGS,{});return data if isinstance(data,dict) else {}
def save_settings(data):save_json(SETTINGS,data)
def with_engine_override(catalog,path):
 """An engine.json published with a release teaches this version a new game build without a new executable."""
 data=load_json(path,{})
 if not isinstance(data,dict):return catalog
 for key in ('expected_patch','engine_header_sha256'):
  if isinstance(data.get(key),str):catalog[key]=data[key]
 if isinstance(data.get('engine'),dict):catalog['engine']={**catalog.get('engine',{}),**data['engine']}
 return catalog
CATALOG=with_engine_override(json.loads((BASE/'catalog.json').read_text('utf-8')),HOME/'engine.json')

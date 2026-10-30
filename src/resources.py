"""Bundled files, the weapon catalog and the small JSON files kept in %APPDATA%\\FoundryTracker."""
import sys,os,json
from pathlib import Path
BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
CATALOG=json.loads((BASE/'catalog.json').read_text('utf-8'))
VERSION='0.7.1'
GOAL=1000
HOME=Path(os.environ.get('APPDATA',str(Path.home())))/'FoundryTracker'
SETTINGS=HOME/'settings.json'
def load_json(path,default):
 try:return json.loads(Path(path).read_text('utf-8'))
 except (OSError,ValueError):return default
def save_json(path,data):
 try:
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.tmp')
  temp.write_text(json.dumps(data,ensure_ascii=False),'utf-8');temp.replace(path)
 except OSError:pass
def load_settings():
 data=load_json(SETTINGS,{});return data if isinstance(data,dict) else {}
def save_settings(data):save_json(SETTINGS,data)

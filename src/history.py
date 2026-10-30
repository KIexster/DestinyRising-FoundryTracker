"""Local history of validated reads (kills per weapon ID), session gains and the shortest path to 8/8."""
from resources import HOME,GOAL,load_json,save_json
FILE=HOME/'history.json'
LIMIT=200
class History:
 """Gains compare the newest read with the session start, or with the previous read when no session is open."""
 def __init__(self,path=FILE,persist=True):
  self.path=path;self.persist=persist;data=load_json(path,{}) if persist else {}
  data=data if isinstance(data,dict) else {}
  self.reads=[x for x in data.get('reads',[]) if isinstance(x,dict) and 'kills' in x];self.session=data.get('session')
 @staticmethod
 def snapshot(data):
  return {'captured_at':data['captured_at'],'kills':{r['weapon_id']:r['kills'] for r in data['rows'] if r['kills'] is not None}}
 def add(self,data):
  snap=self.snapshot(data)
  if not self.reads or self.reads[-1]['captured_at']!=snap['captured_at']:self.reads=(self.reads+[snap])[-LIMIT:];self.save()
 def save(self):
  if self.persist:save_json(self.path,{'reads':self.reads,'session':self.session})
 def baseline(self):
  if self.session:return self.session
  return self.reads[-2] if len(self.reads)>=2 else None
 def gains(self):
  """Weapon ID -> kills gained. A weapon without an earlier record counts from zero."""
  base=self.baseline()
  if not base or not self.reads:return {}
  old=base['kills'];return {w:k-old.get(w,0) for w,k in self.reads[-1]['kills'].items() if k-old.get(w,0)>0}
 def start_session(self):
  if self.reads:self.session=dict(self.reads[-1]);self.save()
 def end_session(self):
  gains=self.gains();self.session=None;self.save();return gains
def shortest_path(rows,progress):
 """Fewest kills to reach 8 completed weapon IDs: the pending weapons closest to 1,000.
 A weapon without a record counts as a full 1,000 to go."""
 need=max(0,8-progress)
 if not need:return {'need':0,'kills':0,'weapons':[],'possible':True,'unknown':0}
 pending=sorted((r for r in rows if not r['completed']),key=lambda r:(r['remaining'] if r['kills'] is not None else GOAL,r['weapon']))[:need]
 return {'need':need,'kills':sum(r['remaining'] if r['kills'] is not None else GOAL for r in pending),'weapons':[r['weapon_id'] for r in pending],
  'possible':len(pending)==need,'unknown':sum(r['kills'] is None for r in pending)}

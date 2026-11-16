"""Offline release entry point: no game connection, ADB, memory reader or network."""
import json,datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox
import gallery,theme
from resources import CATALOG,load_json
MAX_KILLS=10**12

def snapshot(path):
 data=load_json(path,None)
 if not isinstance(data,dict) or not isinstance(data.get('rows'),list) or not isinstance(data.get('summary'),list):raise ValueError('Select a Foundry Tracker JSON export.')
 if len(data['rows'])>5000 or len(data['summary'])>100:raise ValueError('Export too large.')
 known={r['weapon_id'] for r in CATALOG['weapons']};kills={}
 for r in data['rows']:
  if not isinstance(r,dict) or r.get('weapon_id') not in known:raise ValueError('Unknown weapon in export.')
  k=r.get('kills')
  if k is not None and (type(k) is not int or not 0<=k<=MAX_KILLS):raise ValueError('Invalid kill counter.')
  w=r['weapon_id']
  if w in kills and kills[w]!=k:raise ValueError('Conflicting weapon counters.')
  kills[w]=k
 progress={}
 for g in data['summary']:
  if not isinstance(g,dict) or type(g.get('id')) is not int or type(g.get('progress')) is not int or not 0<=g['progress']<=8:raise ValueError('Invalid achievement progress.')
  if g['id'] in progress:raise ValueError('Duplicate achievement.')
  progress[g['id']]=g['progress']
 if set(progress)!={g['id'] for g in CATALOG['collections']}:raise ValueError('Missing or unknown achievements.')
 rows=[];summary=[]
 for r in CATALOG['weapons']:
  k=kills.get(r['weapon_id']);rows.append(dict(r,kills=k,remaining=max(0,1000-k) if k is not None else None,completed=k is not None and k>=1000))
 for g in CATALOG['collections']:
  measured=sum(r['completed'] for r in rows if r['achievement_id']==g['id']);n=progress[g['id']]
  summary.append(dict(g,progress=n,measured=measured,consistent=min(measured,8)==n))
 stamp=data.get('captured_at')
 if not isinstance(stamp,str):raise ValueError('Missing snapshot date.')
 datetime.datetime.fromisoformat(stamp)
 return dict(captured_at=stamp,rows=rows,summary=summary,weapon_counter_count=sum(k is not None for k in kills.values()),offline=True)

class OfflineApp(gallery.App):
 def __init__(self,root):
  super().__init__(root,adb=None)
  self.demo=('Offline','');self.history.persist=False
  self.toggle.pack_forget();self.session_button.pack_forget()
  self.retranslate()
 def retranslate(self):
  super().retranslate()
  es=self.lang=='es'
  self.root.title('Foundry Tracker - Offline')
  self.refresh_button.configure(text='Abrir exportacion JSON' if es else 'Open JSON export')
  self.footer.configure(text='SIN CONEXION: no conecta con el juego. Los datos corresponden a la fecha del archivo.' if es else 'OFFLINE: no game connection. Data reflects the date of the imported file.')
 def refresh(self):
  if self.busy or self.closed:return
  path=filedialog.askopenfilename(title='Foundry Tracker JSON',filetypes=[('JSON','*.json')])
  if not path:return
  try:data=snapshot(path)
  except (ValueError,KeyError,TypeError,OSError) as exc:messagebox.showerror('Invalid export',str(exc));return
  self.events.put(('data',data))
 def schedule(self):pass
 def remember_engine(self,*args):pass

def main():
 gallery.enable_dpi_awareness();root=tk.Tk();theme.init_scale(root);OfflineApp(root);root.mainloop()
if __name__=='__main__':main()

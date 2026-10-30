"""Compact always-on-top window (session gains and the weapons closest to 1,000, or one followed weapon) and milestone toasts."""
import tkinter as tk
from theme import BG,PANEL,LINE,MUTED,DIM,FG,ACCENT,DONE,ERROR,STATUS,FONT,px,size,finish,rounded
from widgets import FlatButton
from resources import CATALOG,GOAL,save_settings
from history import followed
ROWS=3
TOAST_MS=7000
TOAST_WIDTH=300
class MiniWindow:
 """Small window that stays above the game. Closing it only hides it; the main window keeps everything.
 It shows either the general view or one weapon followed from the weapon drawer (kept in settings as mini_weapon)."""
 def __init__(self,app):self.app=app;self.win=None;self.weapon=app.settings.get('mini_weapon');self.last=None;self.share=0.0;self.share_color=ACCENT;self.next_id=None
 def toggle(self):
  if self.win:self.close()
  else:self.open()
 def follow(self,weapon_id):
  """Follow one weapon ID, opening the window if needed; None goes back to the general view."""
  self.weapon=weapon_id;self.last=None
  if weapon_id:self.app.settings['mini_weapon']=weapon_id
  else:self.app.settings.pop('mini_weapon',None)
  save_settings(self.app.settings)
  if weapon_id and not self.win:self.open()
  elif self.win:self.update();self.win.lift()
  self.app.inspector.draw()
 def open(self):
  if self.win:self.win.deiconify();self.win.lift();return
  app=self.app;w=self.win=tk.Toplevel(app.root,bg=BG,padx=px(18),pady=px(14))
  w.attributes('-topmost',True);w.resizable(False,False);w.protocol('WM_DELETE_WINDOW',self.close)
  if app.settings.get('mini_geometry'):
   try:w.geometry(app.settings['mini_geometry'])
   except tk.TclError:pass
  g=self.general=tk.Frame(w,bg=BG)
  self.head=tk.Label(g,bg=BG,fg=MUTED,font=(FONT,9,'bold'),anchor='w');self.head.pack(fill='x')
  self.total=tk.Label(g,bg=BG,fg=ACCENT,font=(FONT,22,'bold'),anchor='w');self.total.pack(fill='x')
  self.gained=tk.Label(g,bg=BG,fg=FG,font=(FONT,10),anchor='w',justify='left');self.gained.pack(fill='x',pady=(0,px(10)))
  tk.Frame(g,bg=LINE,height=px(1),width=px(280)).pack(fill='x',pady=(0,px(10)))
  self.near_head=tk.Label(g,bg=BG,fg=MUTED,font=(FONT,9,'bold'),anchor='w');self.near_head.pack(fill='x')
  self.near=tk.Label(g,bg=BG,fg=FG,font=(FONT,10),anchor='w',justify='left');self.near.pack(fill='x',pady=(0,px(12)))
  self.build_single()
  row=self.bottom=tk.Frame(w,bg=BG);row.pack(fill='x')
  self.status=tk.Label(row,bg=BG,fg=DIM,font=(FONT,9),anchor='w');self.status.pack(side='left',fill='x',expand=True,padx=(0,px(12)))
  self.button=FlatButton(row,app,app.refresh,primary=True);self.button.configure(font=(FONT,9,'bold'),padx=px(12),pady=px(5));self.button.pack(side='right')
  self.update();app.update_buttons()
 def build_single(self):
  s=self.single=tk.Frame(self.win,bg=BG);top=tk.Frame(s,bg=BG);top.pack(fill='x')
  self.follow_head=tk.Label(top,bg=BG,fg=MUTED,font=(FONT,9,'bold'));self.follow_head.pack(side='left')
  self.show_all=link(tk.Label(top,bg=BG,fg=MUTED,font=(FONT,9,'bold')),MUTED,lambda:self.follow(None));self.show_all.pack(side='right')
  body=tk.Frame(s,bg=BG);body.pack(fill='x',pady=(px(10),px(8)))
  self.art=tk.Label(body,bg=BG);self.names=tk.Frame(body,bg=BG);self.names.pack(side='left',fill='x',expand=True)
  self.name=tk.Label(self.names,bg=BG,fg=FG,font=(FONT,12,'bold'),anchor='w',justify='left',wraplength=px(210));self.name.pack(fill='x')
  self.where=tk.Label(self.names,bg=BG,fg=MUTED,font=(FONT,9),anchor='w',justify='left',wraplength=px(210));self.where.pack(fill='x')
  line=tk.Frame(s,bg=BG);line.pack(fill='x')
  self.count=tk.Label(line,bg=BG,font=(FONT,22,'bold'),anchor='w');self.count.pack(side='left')
  self.percent=tk.Label(line,bg=BG,font=(FONT,11,'bold'));self.percent.pack(side='right',anchor='s',pady=(0,px(6)))
  self.bar=tk.Canvas(s,width=px(280),height=px(8),bg=BG,highlightthickness=0);self.bar.pack(fill='x',pady=(px(2),px(10)));self.bar.bind('<Configure>',lambda e:self.draw_bar())
  self.foot=tk.Frame(s,bg=BG);self.foot.pack(fill='x',pady=(0,px(12)))
  self.detail=tk.Label(self.foot,bg=BG,fg=FG,font=(FONT,10),anchor='w',justify='left')
  self.next_link=link(tk.Label(self.foot,bg=BG,fg=ACCENT,font=(FONT,10,'bold'),anchor='w',justify='left',wraplength=px(280)),ACCENT,lambda:self.next_id and self.follow(self.next_id))
 def close(self):
  if not self.win:return
  self.remember();self.win.destroy();self.win=None;self.app.update_buttons()
 def remember(self):
  """Where the window was and whether it was open, so the next start puts it back."""
  if self.win:self.app.settings['mini_geometry']='+%d+%d'%(self.win.winfo_x(),self.win.winfo_y())
  self.app.settings['mini_open']=bool(self.win);save_settings(self.app.settings)
 def update(self):
  if not self.win:return
  self.win.title(self.app.T('mini_title'))
  shown,hidden=(self.single,self.general) if self.weapon else (self.general,self.single)
  hidden.pack_forget();shown.pack(fill='x',before=self.bottom)
  if self.weapon:self.update_single()
  else:self.update_general()
  self.update_status()
 def update_single(self):
  """The followed weapon. While a read is running the last values stay on screen instead of blanking."""
  app=self.app;T=app.T;wid=self.weapon
  if app.data:info=followed(app.data['rows'],wid);gain=app.current_gains.get(wid);self.last=(info,gain)
  else:info,gain=self.last or (None,None)
  row=info['row'] if info else None;known=[x for x in CATALOG['weapons'] if x['weapon_id']==wid]
  self.follow_head.configure(text=T('mini_following'));self.show_all.configure(text=T('mini_show_all'))
  self.name.configure(text=(row or (known[0] if known else {})).get('weapon',wid))
  self.where.configure(text='  ·  '.join(info['collections'] if info else dict.fromkeys(x['collection'] for x in known)))
  image=app.weapon_image(wid,'s');self.art.pack_forget()
  if image:self.art.configure(image=image);self.art.pack(side='left',padx=(0,px(12)),before=self.names)
  kills=row['kills'] if row else None;done=bool(row and row['completed']);color=DONE if done else ACCENT if kills is not None else DIM
  self.count.configure(text=f"{app.num(kills) if kills is not None else '—'} / {app.num(GOAL)}",fg=color)
  self.percent.configure(text=T('st_done') if done else f'{min(100,round(kills/GOAL*100))} %' if kills is not None else '',fg=color)
  self.share=min(1.0,(kills or 0)/GOAL);self.share_color=color;self.draw_bar()
  if row is None:parts=[T('mini_wait' if not app.data and not self.last else 'mini_follow_missing')]
  elif kills is None:parts=[T('st_unknown')]
  else:parts=[] if done else [T('mini_follow_left',kills=app.num(row['remaining']))]
  if gain:parts.append(T('gain_session' if app.history.session else 'gain_read',kills=app.num(gain)))
  after=info['next'] if info and done else None;self.next_id=after['weapon_id'] if after else None
  self.detail.pack_forget();self.next_link.pack_forget()
  if parts:self.detail.configure(text='  ·  '.join(parts));self.detail.pack(fill='x')
  if done:
   text=T('mini_follow_next',weapon=after['weapon'],kills=app.num(after['remaining'] if after['kills'] is not None else GOAL)) if after else T('mini_follow_all_done')
   self.next_link.base=ACCENT if after else MUTED;self.next_link.configure(text=text,fg=self.next_link.base,cursor='hand2' if after else '');self.next_link.pack(fill='x',pady=(px(4) if parts else 0,0))
 def draw_bar(self):
  c=self.bar;c.delete('all');w=size(c)[0];rounded(c,0,0,w,8,4,fill=LINE,outline='')
  if self.share>0:rounded(c,0,0,max(8,w*self.share),8,4,fill=self.share_color,outline='')
  finish(c)
 def update_general(self):
  app=self.app;T=app.T;gains=app.current_gains;rows=app.data['rows'] if app.data else []
  self.head.configure(text=T('mini_session' if app.history.session else 'mini_last'))
  self.total.configure(text='+'+app.num(sum(gains.values())))
  names={r['weapon_id']:r['weapon'] for r in rows}
  top=sorted(gains.items(),key=lambda x:(-x[1],names.get(x[0],x[0])))[:ROWS]
  self.gained.configure(text='\n'.join(f'{names.get(w,w)}   +{app.num(k)}' for w,k in top) or T('mini_no_gains'))
  self.near_head.configure(text=T('mini_closest',goal=app.num(GOAL)))
  # One line per weapon ID: the same weapon can belong to more than one collection.
  pending={r['weapon_id']:r for r in rows if not r['completed'] and r['kills'] is not None}
  near=sorted(pending.values(),key=lambda r:(r['remaining'],r['weapon']))[:ROWS]
  text='\n'.join(T('mini_left',weapon=r['weapon'],kills=app.num(r['remaining'])) for r in near)
  self.near.configure(text=text or T('mini_all_done' if app.data else 'mini_wait'))
 def update_status(self):
  if not self.win:return
  app=self.app;T=app.T
  if app.busy:text,color=T('reading')+'…',STATUS
  elif app.message[3]:text,color=T('mini_error'),ERROR
  elif app.data:text,color=T('mini_updated',time=app.data['captured_at'][11:16]),DIM
  else:text,color='',DIM
  self.status.configure(text=text,fg=color);self.button.configure(text=T('mini_refresh'));self.button.set_enabled(not app.busy)
class Toasts:
 """Borderless notices in the bottom-right corner, above the game; they fade in, stack and close on their own."""
 def __init__(self,app):self.app=app;self.shown=[]
 def show(self,title,body,color=DONE):
  root=self.app.root;t=tk.Toplevel(root,bg=color);t.overrideredirect(True);t.attributes('-topmost',True)
  inner=tk.Frame(t,bg=PANEL,padx=px(18),pady=px(12));inner.pack(fill='both',expand=True,padx=px(2),pady=px(2))
  tk.Label(inner,text=title,bg=PANEL,fg=color,font=(FONT,11,'bold'),anchor='w').pack(fill='x')
  tk.Label(inner,text=body,bg=PANEL,fg=FG,font=(FONT,10),anchor='w',justify='left',wraplength=px(320)).pack(fill='x',pady=(px(4),0))
  # Same minimum width for every toast so a stack lines up.
  t.update_idletasks();w,h=max(t.winfo_reqwidth(),px(TOAST_WIDTH)),t.winfo_reqheight();left,top,right,bottom=work_area(root)
  y=bottom-px(16)-h-sum(s.winfo_height()+px(10) for s in self.shown)
  t.geometry(f'{w}x{h}+{right-w-px(16)}+{max(top,y)}')
  for widget in (t,inner,*inner.winfo_children()):widget.bind('<Button-1>',lambda e,t=t:self.dismiss(t))
  self.shown.append(t);t.after(TOAST_MS,lambda:self.dismiss(t))
  try:t.attributes('-alpha',0.0);self.app.anim.tween(('toast',id(t)),260,lambda v:t.attributes('-alpha',v))
  except tk.TclError:pass
  try:
   import winsound;winsound.MessageBeep(winsound.MB_ICONASTERISK)
  except (ImportError,RuntimeError):pass
 def dismiss(self,t):
  if t in self.shown:self.shown.remove(t)
  try:t.destroy()
  except tk.TclError:pass
def link(label,color,command):
 """A label that acts as a text link: brighter on hover, runs command on click."""
 label.bind('<Enter>',lambda e:str(label['cursor'])=='hand2' and label.configure(fg=FG));label.bind('<Leave>',lambda e:label.configure(fg=label.base))
 label.bind('<Button-1>',lambda e:command());label.base=color;label.configure(cursor='hand2');return label
def work_area(root):
 """Screen area without the taskbar, in the same pixels Tk uses (the process is DPI aware)."""
 try:
  import ctypes,ctypes.wintypes
  rect=ctypes.wintypes.RECT()
  if ctypes.windll.user32.SystemParametersInfoW(0x30,0,ctypes.byref(rect),0):return rect.left,rect.top,rect.right,rect.bottom
 except (ImportError,AttributeError,OSError):pass
 return 0,0,root.winfo_screenwidth(),root.winfo_screenheight()-px(48)
def window_frame():
 """Side border and top border with the title bar of a normal window, in pixels: Tk places the outer frame, not the content."""
 try:
  import ctypes
  m=ctypes.windll.user32.GetSystemMetrics;side=m(32)+m(92)
  if side>0:return side,m(4)+m(33)+m(92)
 except (ImportError,AttributeError,OSError):pass
 return px(8),px(31)

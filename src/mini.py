"""Compact always-on-top window (session gains and the weapons closest to 1,000) and milestone toasts."""
import tkinter as tk
from theme import BG,PANEL,LINE,MUTED,DIM,FG,ACCENT,DONE,ERROR,STATUS,FONT,px
from widgets import FlatButton
from resources import GOAL,save_settings
ROWS=3
TOAST_MS=7000
TOAST_WIDTH=300
class MiniWindow:
 """Small window that stays above the game. Closing it only hides it; the main window keeps everything."""
 def __init__(self,app):self.app=app;self.win=None
 def toggle(self):
  if self.win:self.close()
  else:self.open()
 def open(self):
  if self.win:self.win.deiconify();self.win.lift();return
  app=self.app;w=self.win=tk.Toplevel(app.root,bg=BG,padx=px(18),pady=px(14))
  w.attributes('-topmost',True);w.resizable(False,False);w.protocol('WM_DELETE_WINDOW',self.close)
  if app.settings.get('mini_geometry'):
   try:w.geometry(app.settings['mini_geometry'])
   except tk.TclError:pass
  self.head=tk.Label(w,bg=BG,fg=MUTED,font=(FONT,9,'bold'),anchor='w');self.head.pack(fill='x')
  self.total=tk.Label(w,bg=BG,fg=ACCENT,font=(FONT,22,'bold'),anchor='w');self.total.pack(fill='x')
  self.gained=tk.Label(w,bg=BG,fg=FG,font=(FONT,10),anchor='w',justify='left');self.gained.pack(fill='x',pady=(0,px(10)))
  tk.Frame(w,bg=LINE,height=px(1),width=px(280)).pack(fill='x',pady=(0,px(10)))
  self.near_head=tk.Label(w,bg=BG,fg=MUTED,font=(FONT,9,'bold'),anchor='w');self.near_head.pack(fill='x')
  self.near=tk.Label(w,bg=BG,fg=FG,font=(FONT,10),anchor='w',justify='left');self.near.pack(fill='x',pady=(0,px(12)))
  row=tk.Frame(w,bg=BG);row.pack(fill='x')
  self.status=tk.Label(row,bg=BG,fg=DIM,font=(FONT,9),anchor='w');self.status.pack(side='left',fill='x',expand=True,padx=(0,px(12)))
  self.button=FlatButton(row,app,app.refresh,primary=True);self.button.configure(font=(FONT,9,'bold'),padx=px(12),pady=px(5));self.button.pack(side='right')
  self.update();app.update_buttons()
 def close(self):
  if not self.win:return
  self.remember();self.win.destroy();self.win=None;self.app.update_buttons()
 def remember(self):
  """Where the window was and whether it was open, so the next start puts it back."""
  if self.win:self.app.settings['mini_geometry']='+%d+%d'%(self.win.winfo_x(),self.win.winfo_y())
  self.app.settings['mini_open']=bool(self.win);save_settings(self.app.settings)
 def update(self):
  if not self.win:return
  app=self.app;T=app.T;gains=app.current_gains;rows=app.data['rows'] if app.data else []
  self.win.title(T('mini_title'))
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
  self.update_status()
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
def work_area(root):
 """Screen area without the taskbar, in the same pixels Tk uses (the process is DPI aware)."""
 try:
  import ctypes,ctypes.wintypes
  rect=ctypes.wintypes.RECT()
  if ctypes.windll.user32.SystemParametersInfoW(0x30,0,ctypes.byref(rect),0):return rect.left,rect.top,rect.right,rect.bottom
 except (ImportError,AttributeError,OSError):pass
 return 0,0,root.winfo_screenwidth(),root.winfo_screenheight()-px(48)

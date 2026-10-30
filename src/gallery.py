"""Foundry Tracker window: home emblems, collection view, intro, notices and the read loop.

Look and feel: theme.py · texts: lang/*.json · widgets: widgets.py, cards.py, weapons.py ·
history and shortest path: history.py · share card: sharecard.py · reader: tracker.py.
"""
import sys,re,json,csv,time,math,threading,queue,datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,font as tkfont
from tracker import collect
import theme,i18n,sharecard,adb_runtime
from resources import BASE,CATALOG,VERSION,GOAL,load_settings,save_settings
from theme import BG,PANEL,PANEL_HI,LINE,MUTED,DIM,FG,ACCENT,DONE,ARC,ERROR,STATUS,SPLASH_BG,FONT,px,size,finish,mix,ease_in_out,rounded
from widgets import Animator,FlatButton,Toggle,Segmented
from cards import EmblemCard
from weapons import WeaponList,Inspector
from history import History,shortest_path,milestones
from mini import MiniWindow,Toasts,work_area,window_frame
# tracker.py stops on an unknown game build; these messages become a "download the new version" notice.
UPDATE_BUILD=re.compile(r'Build (\S+) no validada\. Esta versión admite (\S+)\.')
UPDATE_ENGINE='Motor no compatible'
AUTO_MS=30000      # automatic refresh; a refresh of a running game takes 3-5 s since 0.8.1
TOAST_LIMIT=4      # more milestones than this in one read become a single "and N more" toast
class App:
 def __init__(self,root,demo=None,adb=None):
  self.root=root;self.demo=demo;self.adb=adb;self.data=None;self.busy=False;self.closed=False;self.events=queue.Queue();self.auto_id=None;self.selected=None;self.mode='all';self.shimmer=-9.0;self.sweep=0.0;self.spin=0;self.phase=0.0
  self.settings=load_settings();self.lang=self.settings.get('lang') if self.settings.get('lang') in i18n.LANGS else i18n.DEFAULT_LANG;self.message=('key','starting',{},False)
  self.history=History(persist=not demo);self.current_gains={};self.paths={};self.notice=None
  self.anim=Animator(root);self.small=tkfont.Font(family=FONT,size=9,weight='bold');self.weapon_cache={};self.goal_row=None
  self.mini=MiniWindow(self);self.toasts=Toasts(self);self.last_progress=None
  # Centred in the screen area the taskbar leaves free, title bar included.
  left,top,right,bottom=work_area(root);side,caption=window_frame();aw,ah=right-left,bottom-top
  w,h=min(px(1230),aw-60),min(px(900),ah-caption-px(20))
  root.geometry(f'{w}x{h}+{left+(aw-w)//2-side}+{top+max(0,(ah-h-caption)//2)}');root.minsize(min(px(1040),w),min(px(840),h));root.configure(bg=BG)
  # Gold wolves emblem instead of the Tk feather, for this window and every dialog it opens.
  try:root.iconbitmap(default=str(BASE/'emblems'/'app_icon.ico'))
  except tk.TclError:pass
  style=ttk.Style();style.theme_use('clam');style.configure('TEntry',fieldbackground=PANEL,foreground=FG,insertcolor=FG,bordercolor=LINE,lightcolor=LINE,darkcolor=LINE,padding=px(7))
  style.configure('Vertical.TScrollbar',background=PANEL,troughcolor=BG,bordercolor=BG,arrowcolor=MUTED,lightcolor=PANEL,darkcolor=PANEL);style.map('Vertical.TScrollbar',background=[('active',PANEL_HI)])
  main=tk.Frame(root,bg=BG,padx=px(28),pady=px(22));main.pack(fill='both',expand=True)
  top=tk.Frame(main,bg=BG);top.pack(fill='x')
  self.header=tk.Label(top,bg=BG,fg=FG,font=(FONT,26,'bold'));self.header.pack(side='left')
  right=tk.Frame(top,bg=BG);right.pack(side='right')
  self.lang_switch=Segmented(right,self,[(code,i18n.label(code)) for code in i18n.LANGS],self.set_lang,small=True);self.lang_switch.pack(side='right');self.lang_switch.select(self.lang,animate=False)
  tk.Label(right,text=f'FOUNDRY TRACKER  /  {VERSION}',bg=BG,fg=DIM,font=(FONT,9,'bold')).pack(side='right',padx=(0,px(16)))
  self.tagline=tk.Label(main,bg=BG,fg=MUTED,font=(FONT,10));self.tagline.pack(anchor='w',pady=(px(2),px(16)))
  bar=tk.Frame(main,bg=BG);bar.pack(fill='x',pady=(0,px(18)))
  self.refresh_button=FlatButton(bar,self,self.refresh,primary=True);self.refresh_button.pack(side='left')
  self.auto=tk.BooleanVar(value=False);self.toggle=Toggle(bar,self,self.auto,self.schedule);self.toggle.pack(side='left',padx=px(18))
  self.export_button=FlatButton(bar,self,self.export);self.export_button.pack(side='right')
  self.share_button=FlatButton(bar,self,self.share);self.share_button.pack(side='right',padx=(0,px(10)))
  self.session_button=FlatButton(bar,self,self.toggle_session);self.session_button.pack(side='right',padx=(0,px(10)))
  self.mini_button=FlatButton(bar,self,self.mini.toggle);self.mini_button.pack(side='right',padx=(0,px(10)))
  self.stage=tk.Frame(main,bg=BG);self.stage.pack(fill='both',expand=True)
  self.images={}
  for g in CATALOG['collections']:
   # Above 140 % scale the 128 px originals keep the emblems close to their 96-dpi size.
   big=BASE/g['emblem'].replace('.png','_original.png');self.images[g['id']]=tk.PhotoImage(file=str(big if theme.S>=1.4 and big.exists() else BASE/g['emblem']))
  self.home=tk.Frame(self.stage,bg=BG);heading=tk.Frame(self.home,bg=BG);heading.pack(fill='x',pady=(0,px(12)))
  self.challenges=tk.Label(heading,bg=BG,fg=ACCENT,font=(FONT,11,'bold'));self.challenges.pack(side='left')
  self.closest=tk.Label(heading,bg=BG,fg=MUTED,font=(FONT,10));self.closest.pack(side='right')
  grid=tk.Frame(self.home,bg=BG);grid.pack(fill='both',expand=True);self.cards={}
  for i,g in enumerate(CATALOG['collections']):
   grid.columnconfigure(i%3,weight=1,uniform='card');grid.rowconfigure(i//3,weight=1,uniform='row')
   card=EmblemCard(grid,self,g,self.images[g['id']],i);card.grid(row=i//3,column=i%3,sticky='nsew',padx=(0,px(14)),pady=(0,px(14)));self.cards[g['id']]=card
  self.build_detail()
  self.status=tk.Label(main,bg=BG,fg=STATUS,font=(FONT,10),anchor='w',justify='left',wraplength=px(1120));self.status.pack(fill='x',pady=(px(16),px(4)))
  self.footer=tk.Label(main,bg=BG,fg=DIM,font=(FONT,9),anchor='w');self.footer.pack(fill='x')
  self.retranslate();self.show(self.home,0)
  self.intro()
  root.bind('<Escape>',lambda e:self.escape());root.bind('<Control-r>',lambda e:self.refresh());root.bind('<F5>',lambda e:self.refresh())
  root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll);root.after(50,self.pulse);root.after(700,self.refresh)
  if self.settings.get('mini_open') and not demo:root.after(1600,self.mini.open)
 # Opening animation and the root notice
 def intro(self):
  """Opening: the emblem lights up along its centre line and splits open like two doors."""
  files=[BASE/'emblems'/'splash_left.png',BASE/'emblems'/'splash_right.png'];self.doors=[];self.doors_opening=False;self.seam=0.0
  if '--no-intro' in sys.argv or not all(f.exists() for f in files):
   for card in self.cards.values():card.enter()
   self.root.after(300,self.show_notice);return
  self.door_images=[tk.PhotoImage(file=str(f)) for f in files]
  for side,image in zip(('left','right'),self.door_images):
   door=tk.Canvas(self.root,bg=SPLASH_BG,highlightthickness=0,bd=0,cursor='hand2');door.side=side;door.image=image
   door.bind('<Configure>',lambda e,d=door:self.draw_door(d));door.bind('<Button-1>',lambda e:self.open_doors(fast=True))
   door.place(relx=0 if side=='left' else 0.5,rely=0,relwidth=0.5,relheight=1);tk.Misc.tkraise(door);self.doors.append(door)
  try:self.root.attributes('-alpha',0.0);self.anim.tween('fade',380,lambda t:self.root.attributes('-alpha',t))
  except tk.TclError:pass
  self.anim.tween('seam',520,self.set_seam,delay=520);self.door_timer=self.root.after(1250,self.open_doors)
 def draw_door(self,door):
  # Doors are drawn in real pixels: the halves are 900 px tall images centred on the seam.
  door.delete('all');w=door.winfo_width();h=door.winfo_height();left=door.side=='left';x=w-1 if left else 0
  door.create_image(w if left else 0,h/2,image=door.image,anchor='e' if left else 'w')
  if self.seam>0:
   half=h/2*self.seam
   door.create_line(x,h/2-half,x,h/2+half,fill=mix(SPLASH_BG,ACCENT,0.45*self.seam),width=px(12))
   door.create_line(x,h/2-half,x,h/2+half,fill=mix(SPLASH_BG,DONE,self.seam),width=px(3))
 def set_seam(self,t):
  self.seam=t
  for door in self.doors:self.draw_door(door)
 def open_doors(self,fast=False):
  if not self.doors or self.doors_opening:return
  self.doors_opening=True;self.root.after_cancel(self.door_timer)
  if fast:
   self.anim.cancel('fade');self.anim.cancel('seam')
   try:self.root.attributes('-alpha',1.0)
   except tk.TclError:pass
  duration=450 if fast else 950
  for card in self.cards.values():card.enter(delay=duration*0.45)
  def step(t):
   shift=(self.root.winfo_width()/2+px(40))*t;self.doors[0].place_configure(x=-shift);self.doors[1].place_configure(x=shift)
  self.anim.tween('doors',duration,step,done=self.close_doors,curve=ease_in_out)
 def close_doors(self):
  for door in self.doors:door.destroy()
  self.doors=[];self.door_images=[];self.show_notice()
 def show_notice(self):
  """Root reminder shown on every start until "Don't show this again" is ticked."""
  if self.settings.get('hide_root_notice') or self.notice or self.closed:return
  shade=self.notice=tk.Frame(self.root,bg=BG);shade.place(relx=0,rely=0,relwidth=1,relheight=1);tk.Misc.tkraise(shade)
  panel=tk.Frame(shade,bg=PANEL,highlightthickness=px(2),highlightbackground=ACCENT,highlightcolor=ACCENT,padx=px(34),pady=px(28));panel.place(relx=0.5,rely=0.5,anchor='center',y=px(30))
  tk.Label(panel,text=self.T('notice_title'),bg=PANEL,fg=ACCENT,font=(FONT,20,'bold')).pack(anchor='w')
  tk.Label(panel,text=self.T('notice_body'),bg=PANEL,fg=FG,font=(FONT,11),wraplength=px(540),justify='left').pack(anchor='w',pady=(px(12),px(12)))
  tk.Label(panel,text=self.T('notice_steps'),bg=PANEL,fg=MUTED,font=(FONT,11),justify='left').pack(anchor='w')
  row=tk.Frame(panel,bg=PANEL);row.pack(fill='x',pady=(px(24),0))
  self.notice_hide=tk.BooleanVar(value=False);hide=Toggle(row,self,self.notice_hide,lambda:None,bg=PANEL);hide.label.configure(text=self.T('notice_hide'));hide.pack(side='left')
  FlatButton(row,self,self.close_notice,primary=True,text=self.T('notice_ok')).pack(side='right',padx=(px(40),0))
  self.anim.tween('notice',380,lambda t:panel.place_configure(y=px(30)*(1-t)))
 def close_notice(self):
  if not self.notice:return
  if self.notice_hide.get():self.settings['hide_root_notice']=True;save_settings(self.settings)
  self.notice.destroy();self.notice=None
 # Collection view
 def build_detail(self):
  d=self.detail=tk.Frame(self.stage,bg=BG)
  self.back=tk.Label(d,bg=BG,fg=MUTED,font=(FONT,10,'bold'),cursor='hand2');self.back.pack(anchor='w',pady=(0,px(12)))
  self.back.bind('<Button-1>',lambda e:self.go_home());self.back.bind('<Enter>',lambda e:self.back.configure(fg=ACCENT));self.back.bind('<Leave>',lambda e:self.back.configure(fg=MUTED))
  hero=tk.Frame(d,bg=BG);hero.pack(fill='x',pady=(0,px(16)))
  self.hero=tk.Canvas(hero,width=px(146),height=px(146),bg=BG,highlightthickness=0);self.hero.pack(side='left',padx=(0,px(22)));self.hero_fill=0.0
  text=tk.Frame(hero,bg=BG);text.pack(side='left',fill='x',expand=True)
  self.detail_title=tk.Label(text,bg=BG,fg=FG,font=(FONT,24,'bold'));self.detail_title.pack(anchor='w')
  self.rule=tk.Label(text,bg=BG,fg=MUTED,font=(FONT,10));self.rule.pack(anchor='w',pady=(px(4),px(10)))
  self.pips=tk.Canvas(text,height=px(14),bg=BG,highlightthickness=0);self.pips.pack(fill='x');self.pips.bind('<Configure>',lambda e:self.draw_pips())
  stats=tk.Frame(d,bg=BG);stats.pack(fill='x',pady=(0,px(12)));self.metrics=[]
  for key in ('m_progress','m_done','m_pending'):
   box=tk.Frame(stats,bg=PANEL,padx=px(18),pady=px(12));box.pack(side='left',fill='x',expand=True,padx=(0,px(12)))
   title=tk.Label(box,bg=PANEL,fg=MUTED,font=(FONT,9,'bold'));title.pack(anchor='w');value=tk.Label(box,text='—',bg=PANEL,fg=FG,font=(FONT,22,'bold'));value.pack(anchor='w',pady=(px(4),0));self.metrics.append((key,title,value))
  goal=tk.Frame(d,bg=BG);goal.pack(fill='x',pady=(px(2),px(10)))
  self.next_goal=tk.Label(goal,bg=BG,fg=ACCENT,font=(FONT,10,'bold'),anchor='w',wraplength=px(1120),justify='left');self.next_goal.pack(fill='x')
  self.goal_bar=tk.Canvas(goal,height=px(6),bg=BG,highlightthickness=0);self.goal_bar.pack(fill='x',pady=(px(8),0));self.goal_share=0.0;self.goal_bar.bind('<Configure>',lambda e:self.draw_goal())
  self.path_label=tk.Label(goal,bg=BG,fg=MUTED,font=(FONT,10),anchor='w',wraplength=px(1120),justify='left');self.path_label.pack(fill='x',pady=(px(8),0))
  filters=tk.Frame(d,bg=BG);filters.pack(fill='x',pady=(0,px(10)))
  self.tabs=Segmented(filters,self,[('all','—'),('done','—'),('pending','—')],self.set_mode);self.tabs.pack(side='left')
  self.search=tk.StringVar();self.search.trace_add('write',lambda *a:self.render_list());self.search_entry=ttk.Entry(filters,textvariable=self.search,width=26,font=(FONT,10));self.search_entry.pack(side='right')
  self.search_label=tk.Label(filters,bg=BG,fg=MUTED,font=(FONT,10));self.search_label.pack(side='right',padx=px(10))
  self.list=WeaponList(d,self);self.list.pack(fill='both',expand=True);self.inspector=Inspector(d,self)
  self.next_goal.bind('<Button-1>',lambda e:self.goal_row and self.inspect(self.goal_row))
 def weapon_image(self,weapon_id,size):
  """Bundled weapon art: 's' list thumbnail (48 px, 72 px 'm' above 130 % scale), 'l' drawer render. None if missing."""
  key=(weapon_id,size)
  if key not in self.weapon_cache:
   self.weapon_cache[key]=None
   for variant in (['m','s'] if size=='s' and theme.S>=1.3 else [size]):
    path=BASE/'weapons'/f'{weapon_id}_{variant}.png'
    if path.exists():
     try:self.weapon_cache[key]=tk.PhotoImage(file=str(path));break
     except tk.TclError:pass
  return self.weapon_cache[key]
 def inspect(self,row):self.list.selected=row['weapon_id'];self.list.draw();self.inspector.open(row)
 def hide_inspector(self):self.inspector.hide();self.list.selected=None
 def escape(self):
  if self.notice:self.close_notice()
  elif self.inspector.shown:self.inspector.close()
  elif self.selected is not None:self.go_home()
 # Texts
 def T(self,key,**kw):return i18n.text(self.lang,key,**kw)
 def num(self,n):return i18n.number(self.lang,n)
 def set_lang(self,lang):
  self.lang=lang;self.settings['lang']=lang;save_settings(self.settings);self.retranslate()
 def retranslate(self):
  self.root.title(self.T('title'));self.header.configure(text=self.T('header'));self.tagline.configure(text=self.T('tagline'));self.challenges.configure(text=self.T('challenges'))
  self.refresh_button.configure(text=self.T('refresh') if not self.busy else self.T('reading'));self.toggle.label.configure(text=self.T('auto'));self.export_button.configure(text=self.T('export'));self.share_button.configure(text=self.T('share'))
  self.back.configure(text=self.T('back'));self.rule.configure(text=self.T('rule',goal=self.num(GOAL)));self.search_label.configure(text=self.T('search'));self.footer.configure(text=self.T('footer'))
  for key,title,_ in self.metrics:title.configure(text=self.T(key))
  self.tabs.set_labels({'all':self.T('tab_all'),'done':self.T('tab_done'),'pending':self.T('tab_pending')})
  self.update_buttons();self.update_closest();self.redraw_gains()
  self.render_detail(animate=False);self.render_status()
 # Derived data: gains, shortest paths, card texts
 def gains(self):return self.current_gains
 def summary_for(self,aid):return next((x for x in self.data['summary'] if x['id']==aid),None) if self.data else None
 def summary(self):return self.summary_for(self.selected) if self.selected is not None else None
 def collection_rows(self,aid):return [x for x in self.data['rows'] if x['achievement_id']==aid] if self.data else []
 def collection_gain(self,aid):return sum(self.current_gains.get(w,0) for w in {r['weapon_id'] for r in self.collection_rows(aid)})
 def compute_paths(self):
  paths={}
  for g in CATALOG['collections']:
   s=self.summary_for(g['id'])
   if s:paths[g['id']]=shortest_path(self.collection_rows(g['id']),s['progress'])
  return paths
 def card_status(self,aid):
  if self.data is None:return self.T('card_wait')
  s=self.summary_for(aid);progress=s['progress'] if s else 0;path=self.paths.get(aid)
  if progress>=8:tail=self.T('card_done')
  elif path and path['possible']:tail=self.T('card_path',kills=self.num(path['kills']))
  else:tail=self.T('card_open')
  return f'{progress} / 8  ·  '+tail
 def update_closest(self):
  open_paths=[(p['kills'],aid) for aid,p in self.paths.items() if p['need'] and p['possible']]
  if not open_paths:self.closest.configure(text='');return
  kills,aid=min(open_paths);name=next(g['name'] for g in CATALOG['collections'] if g['id']==aid)
  self.closest.configure(text=self.T('closest',name=name,kills=self.num(kills)))
 def redraw_gains(self):
  for card in self.cards.values():card.draw()
  self.list.draw_header();self.list.draw();self.inspector.draw()
 def update_buttons(self):
  active=bool(self.history.session)
  self.session_button.configure(text=self.T('session_end',kills=self.num(sum(self.current_gains.values()))) if active else self.T('session_start'))
  self.session_button.set_enabled(active or (self.data is not None and not self.busy))
  for button in (self.share_button,self.export_button):button.set_enabled(self.data is not None and not self.busy)
  self.mini_button.configure(text=self.T('mini_close' if self.mini.win else 'mini_open'));self.mini.update()
 def toggle_session(self):
  if self.history.session:
   gains=self.history.end_session();self.message=('session',None,dict(kills=self.num(sum(gains.values())),weapons=len(gains)),False)
  elif self.data:self.history.start_session();self.message=('key','session_started',{},False)
  else:return
  self.current_gains=self.history.gains();self.update_buttons();self.redraw_gains();self.render_status()
 # Navigation
 def show(self,view,direction):
  other=self.detail if view is self.home else self.home;other.place_forget()
  view.place(relx=0,rely=0,relwidth=1,relheight=1,x=direction*px(60))
  if direction:self.anim.tween('stage',300,lambda t:view.place_configure(x=direction*px(60)*(1-t)))
 def open_collection(self,aid):
  self.hide_inspector();self.selected=aid;g=next(x for x in CATALOG['collections'] if x['id']==aid);self.detail_title.configure(text=g['name']);self.search.set('');self.mode='all';self.tabs.select('all',animate=False)
  self.show(self.detail,1);self.render_detail(animate=True)
 def go_home(self):
  self.hide_inspector();self.selected=None;self.show(self.home,-1)
  for card in self.cards.values():card.draw()
 def set_mode(self,mode):self.mode=mode;self.render_list()
 def render_detail(self,animate=True):
  if self.selected is None:return
  s=self.summary();rows=self.collection_rows(self.selected) if s else [];done=sum(x['completed'] for x in rows)
  targets=[s['progress'] if s else None,done if s else None,len(rows)-done if s else None]
  for (key,_,label),target in zip(self.metrics,targets):
   if target is None:label.configure(text='—');continue
   fmt=(lambda v:f'{v} / 8') if key=='m_progress' else (lambda v:self.num(v))
   if animate:self.anim.tween(('metric',key),650,lambda t,l=label,f=fmt,v=target:l.configure(text=f(round(v*t))),delay=120)
   else:label.configure(text=fmt(target))
  closest=sorted([x for x in rows if not x['completed'] and x['kills'] is not None],key=lambda x:-x['kills']);share=0.0;self.goal_row=None
  if not s:text=self.T('no_data' if self.data else 'next_wait')
  elif s['progress']>=8:text=self.T('next_done');share=1.0
  elif closest:c=self.goal_row=closest[0];text=self.T('next',weapon=c['weapon'],kills=self.num(c['kills']),remaining=self.num(c['remaining']));share=c['kills']/GOAL
  else:text=self.T('next_none')
  image=self.weapon_image(self.goal_row['weapon_id'],'s') if self.goal_row else None
  self.next_goal.configure(text=('   '+text) if image else text,image=image or '',compound='left',cursor='hand2' if image else '',fg=DONE if s and s['progress']>=8 else ACCENT)
  path=self.paths.get(self.selected) if s and s['progress']<8 else None
  if not path:ptext=''
  elif not path['possible']:ptext=self.T('path_impossible')
  elif path['unknown']:ptext=self.T('path_unknown',kills=self.num(path['kills']),count=path['need'],unknown=path['unknown'],goal=self.num(GOAL))
  else:ptext=self.T('path',kills=self.num(path['kills']),count=path['need'])
  self.path_label.configure(text=ptext);self.list.path=set(path['weapons']) if path and path['possible'] else set()
  progress=float(s['progress']) if s else 0.0
  if animate:
   self.hero_fill=0.0;self.goal_share=0.0
   self.anim.tween('hero',800,lambda t:self.set_detail_fill(progress*t,share*t),delay=150)
  else:self.set_detail_fill(progress,share)
  self.render_list(animate)
 def set_detail_fill(self,fill,share):self.hero_fill=fill;self.goal_share=share;self.draw_pips();self.draw_goal();self.draw_hero()
 def draw_pips(self):
  c=self.pips;c.delete('all');s=self.summary();complete=bool(s and s['progress']>=8);pip,gap=34,7
  for i in range(8):
   x=i*(pip+gap);base=mix(LINE,ARC,max(0,1-abs(i-self.shimmer))*0.55) if self.busy else LINE;rounded(c,x,3,x+pip,11,4,fill=base,outline='')
   part=max(0.0,min(1.0,self.hero_fill-i))
   if part>0:rounded(c,x,3,x+pip*part,11,4,fill=DONE if complete else ACCENT,outline='')
  finish(c)
 def draw_goal(self):
  c=self.goal_bar;c.delete('all');w,_=size(c);rounded(c,0,0,w,6,3,fill=LINE,outline='')
  if self.goal_share>0:rounded(c,0,0,max(6,w*min(1.0,self.goal_share)),6,3,fill=DONE if self.goal_share>=1 else ACCENT,outline='')
  finish(c)
 def draw_hero(self):
  c=self.hero;c.delete('all');s=self.summary();complete=bool(s and s['progress']>=8);color=DONE if complete else ACCENT
  # The emblem's corners sit inside the ring (radius 68), so the progress arc stays visible.
  c.create_oval(9,9,137,137,fill=mix(BG,color,0.08+0.05*math.sin(self.phase)),outline='')
  c.create_oval(5,5,141,141,outline=LINE,width=px(3))
  c.create_arc(5,5,141,141,start=90,extent=-359.9*min(1.0,self.hero_fill/8),style='arc',outline=color,width=px(3))
  c.create_arc(5,5,141,141,start=(self.phase*40)%360,extent=36,style='arc',outline=mix(BG,FG,0.35),width=px(3))
  if self.selected is not None:c.create_image(73,73,image=self.images[self.selected])
  finish(c)
 def render_list(self,animate=False):
  if self.selected is None:return
  rows=self.collection_rows(self.selected);needle=self.search.get().casefold()
  if self.mode=='done':rows=[x for x in rows if x['completed']]
  if self.mode=='pending':rows=[x for x in rows if not x['completed']]
  if needle:rows=[x for x in rows if needle in (x['weapon']+' '+x['weapon_id']).casefold()]
  self.list.set_rows(rows,animate=animate or self.list.reveal<1)
 # Status line
 def say(self,key,error=False,**kw):self.message=('key',key,kw,error);self.render_status()
 def render_status(self):
  kind,value,kw,error=self.message;color=ERROR if error else (STATUS if self.busy else MUTED);weight='normal'
  if kind=='tracker':
   update=UPDATE_BUILD.search(value) if error else None
   if update:text=self.T('needs_update',build=update[1],supported=update[2]);color=ACCENT;weight='bold'
   elif error and value.startswith(UPDATE_ENGINE):text=self.T('needs_update_engine');color=ACCENT;weight='bold'
   else:text=i18n.tracker_text(value,self.lang)
  elif kind=='updated':
   bad=kw['bad'];check=self.T('review',names=', '.join(bad)) if bad else self.T('verified');text=self.T('updated',time=kw['time'],count=self.num(kw['count']),check=check)
   if kw.get('unverified'):text+='  ·  '+self.T('unverified',build=kw['unverified'])
   if self.demo:text+='  ·  '+self.T('demo',file=self.demo[0])
  elif kind=='exported':text=self.T('exported',path=value)
  elif kind=='shared':text=self.T('share_saved',path=value)
  elif kind=='session':text=self.T('session_summary',**kw)
  else:text=self.T(value,**kw)
  spinner='◜◝◞◟'[self.spin%4]+'  ' if self.busy else ''
  self.status.configure(text=spinner+text,fg=color,font=(FONT,10,weight));self.mini.update_status()
 # Reading
 def refresh(self):
  if self.busy or self.closed:return
  if self.auto_id:self.root.after_cancel(self.auto_id);self.auto_id=None
  self.busy=True;self.refresh_button.set_enabled(False);self.refresh_button.configure(text=self.T('reading'));self.data=None;self.paths={};self.current_gains={}
  self.update_buttons();self.update_closest()
  for card in self.cards.values():card.set_progress(0)
  self.render_detail(animate=False);self.say('detecting')
  def work():
   try:
    if self.demo:time.sleep(1.2);self.events.put(('data',json.loads(Path(self.demo[1]).read_text('utf-8'))));return
    self.events.put(('data',collect(self.adb,CATALOG,lambda msg:self.events.put(('status',msg)),self.settings.get('runtime_offsets'),self.settings.get('warm'))))
   except Exception as exc:self.events.put(('error',str(exc)))
  threading.Thread(target=work,daemon=True).start()
 def poll(self):
  if self.closed:return
  try:
   while True:
    kind,value=self.events.get_nowait()
    if kind=='status':self.message=('tracker',value,{},False);self.render_status();continue
    self.busy=False;self.refresh_button.set_enabled(True);self.refresh_button.configure(text=self.T('refresh'))
    if kind=='data':
     warm=value.pop('warm',None);old_kills=self.history.reads[-1]['kills'] if self.history.reads else None
     self.data=value;self.history.add(value);self.announce(old_kills,value);self.current_gains=self.history.gains();self.paths=self.compute_paths();bad=[x['name'] for x in value['summary'] if not x['consistent']]
     self.remember_engine(value.get('engine'),warm)
     unverified=value.get('patch') if value.get('verified_build') is False else None
     self.message=('updated',None,dict(time=value['captured_at'][11:19],count=value['weapon_counter_count'],bad=bad,unverified=unverified),bool(bad))
     for g in CATALOG['collections']:s=self.summary_for(g['id']);self.cards[g['id']].set_progress(s['progress'] if s else 0)
     self.update_closest();self.render_detail(animate=True);self.inspector.draw()
    else:self.message=('tracker',value,{},True)
    self.update_buttons();self.render_status();self.schedule()
  except queue.Empty:pass
  self.root.after(100,self.poll)
 def pulse(self):
  """Ambient motion: loading shimmer, spinner and the glow of completed emblems."""
  if self.closed:return
  self.phase+=0.12
  if self.busy:self.sweep+=0.35;self.shimmer=self.sweep%11-1.5
  if self.busy:
   self.spin+=1;self.render_status();self.draw_pips();self.refresh_button.configure(text=self.T('reading')+'.'*(1+self.spin//6%3))
   if self.selected is None:
    for card in self.cards.values():card.draw()
  elif self.selected is None:
   glow=(math.sin(self.phase)+1)/2
   for card in self.cards.values():
    if (card.progress or 0)>=8:card.glow=glow;card.draw()
  if self.selected is not None:self.draw_hero()
  self.root.after(50,self.pulse)
 def announce(self,old_kills,data):
  """Toasts for weapons that reached 1,000 kills and achievements that reached 8/8 since the previous read."""
  found=[] if self.demo else milestones(old_kills,self.last_progress,data);goal=self.num(GOAL)
  for kind,item in found[:TOAST_LIMIT]:
   if kind=='weapon':self.toasts.show(self.T('toast_weapon',goal=goal),self.T('toast_weapon_body',weapon=item['weapon'],goal=goal))
   else:self.toasts.show(self.T('toast_achievement'),self.T('toast_achievement_body',name=item['name']))
  if len(found)>TOAST_LIMIT:self.toasts.show(self.T('toast_more_title'),self.T('toast_more',count=len(found)-TOAST_LIMIT))
  self.last_progress={x['id']:x['progress'] for x in data['summary']}
 def remember_engine(self,engine,warm=None):
  """Where the interpreter was found for this game build, so the next read skips the memory search, and the pages
  this read needed, so the next read of the same game process fetches them in a few batches (kept across restarts)."""
  if self.demo or not engine:return
  offsets=self.settings.setdefault('runtime_offsets',{})
  offsets.pop(engine['header_sha256'],None);offsets[engine['header_sha256']]=engine['runtime_offset']
  while len(offsets)>8:offsets.pop(next(iter(offsets)))
  if warm:self.settings['warm']=warm
  save_settings(self.settings)
 def schedule(self):
  if self.auto_id:self.root.after_cancel(self.auto_id);self.auto_id=None
  if self.auto.get() and not self.busy and not self.closed:self.auto_id=self.root.after(AUTO_MS,self.refresh)
 # Files
 def export(self):
  if not self.data:return
  name=filedialog.asksaveasfilename(title=self.T('export_title'),defaultextension='.csv',filetypes=[(self.T('csv'),'*.csv'),(self.T('json'),'*.json')],initialfile='Foundry_Progreso_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
  if not name:return
  try:
   if name.lower().endswith('.json'):Path(name).write_text(json.dumps(self.data,ensure_ascii=False,indent=2),'utf-8')
   else:
    with open(name,'w',newline='',encoding='utf-8-sig') as f:
     cols=['collection','weapon','weapon_id','kills','remaining','completed'];writer=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows([r for r in self.data['rows'] if self.selected is None or r['achievement_id']==self.selected])
   self.message=('exported',name,{},False);self.render_status()
  except OSError as exc:messagebox.showerror(self.T('save_error'),str(exc))
 def share_texts(self):
  done=sum(1 for g in CATALOG['collections'] if (self.summary_for(g['id']) or {}).get('progress',0)>=8)
  return dict(title=self.T('challenges'),subtitle=self.T('share_complete',done=done,total=len(CATALOG['collections'])),footer=self.T('share_footer',version=VERSION,date=self.data['captured_at'][:10]))
 def share(self):
  if not self.data:return
  name=filedialog.asksaveasfilename(title=self.T('share_title'),defaultextension='.png',filetypes=[(self.T('png'),'*.png')],initialfile='Foundry_Tracker_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
  if not name:return
  try:sharecard.render(name,self.data,self.share_texts());self.message=('shared',name,{},False);self.render_status()
  except Exception as exc:messagebox.showerror(self.T('save_error'),str(exc))
 def close(self):
  self.closed=True
  if self.auto_id:self.root.after_cancel(self.auto_id)
  self.mini.remember();self.root.destroy()
  if self.adb:adb_runtime.release(self.adb)
def enable_dpi_awareness():
 """Sharp text on 125 % / 150 % displays; theme.px() and theme.finish() keep the layout proportions."""
 try:
  import ctypes
  try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
  except (AttributeError,OSError):ctypes.windll.user32.SetProcessDPIAware()
 except Exception:pass
def main():
 demo=None
 if '--demo' in sys.argv:
  path=Path(sys.argv[sys.argv.index('--demo')+1]);demo=(path.name,str(path))
 adb=None if demo else adb_runtime.prepare()
 if '--diagnostic' in sys.argv:
  try:data=collect(adb,CATALOG);Path(sys.argv[sys.argv.index('--diagnostic')+1]).write_text(json.dumps(data,indent=2),'utf-8')
  finally:adb_runtime.release(adb)
  return
 enable_dpi_awareness();root=tk.Tk();theme.init_scale(root);App(root,demo,adb);root.mainloop()

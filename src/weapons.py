"""Weapon list of a collection and the side drawer with the weapon render."""
import tkinter as tk
from tkinter import ttk
from resources import GOAL
from theme import BG,PANEL,PANEL_HI,LINE,MUTED,DIM,FG,ACCENT,DONE,INK,FONT,px,unit,size,measure,finish,mix,ease,rounded
class WeaponList(tk.Frame):
 COLUMNS=[('weapon',0.32,'w'),('weapon_id',0.10,'w'),('kills',0.11,'e'),('remaining',0.11,'e'),('progress',0.20,'w'),('state',0.16,'w')]
 ROW=56
 def __init__(self,master,app):
  super().__init__(master,bg=BG);self.app=app;self.source=[];self.rows=[];self.sort_key=None;self.reverse=False;self.hover=None;self.reveal=1.0;self.selected=None;self.path=set()
  self.header=tk.Canvas(self,height=px(34),bg=BG,highlightthickness=0,cursor='hand2');self.header.pack(fill='x')
  body=tk.Frame(self,bg=BG);body.pack(fill='both',expand=True)
  self.canvas=tk.Canvas(body,bg=BG,highlightthickness=0,cursor='hand2');self.scroll=ttk.Scrollbar(body,orient='vertical',command=self.canvas.yview);self.canvas.configure(yscrollcommand=self.scroll.set)
  self.canvas.pack(side='left',fill='both',expand=True);self.scroll.pack(side='right',fill='y')
  self.header.bind('<Button-1>',self.header_click);self.header.bind('<Configure>',lambda e:self.draw_header())
  self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<Motion>',self.motion);self.canvas.bind('<Button-1>',self.click)
  self.canvas.bind('<Enter>',lambda e:self.canvas.bind_all('<MouseWheel>',self.wheel));self.canvas.bind('<Leave>',lambda e:(self.set_hover(None),self.canvas.unbind_all('<MouseWheel>')))
 def wheel(self,event):self.canvas.yview_scroll(int(-event.delta/120),'units')
 def positions(self,width):
  x=12;out=[]
  for key,share,anchor in self.COLUMNS:span=(width-24)*share;out.append((key,x,x+span,anchor));x+=span
  return out
 def draw_header(self):
  c=self.header;c.delete('all');w,_=size(c)
  labels=dict(weapon='col_weapon',weapon_id='col_id',kills='col_kills',remaining='col_remaining',progress='col_progress',state='col_state')
  for key,a,b,anchor in self.positions(w):
   text=self.app.T(labels[key])+(('  ▼' if self.reverse else '  ▲') if key==self.sort_key else '')
   c.create_text(a+8 if anchor=='w' else b-8,17,text=text,anchor=anchor,fill=ACCENT if key==self.sort_key else MUTED,font=(FONT,9,'bold'))
  c.create_line(12,33,w-12,33,fill=LINE);finish(c)
 def header_click(self,event):
  x=unit(event.x)
  for key,a,b,_ in self.positions(size(self.header)[0]):
   if a<=x<=b and key!='progress':
    self.reverse=not self.reverse if self.sort_key==key else key in ('kills','progress');self.sort_key=key;self.set_rows(self.source,animate=False);return
 def ordered(self,rows):
  if self.sort_key is None:return sorted(rows,key=lambda x:(not x['completed'],-(x['kills'] or 0),x['weapon']))
  if self.sort_key in ('kills','remaining'):
   known=[x for x in rows if x['kills'] is not None];unknown=[x for x in rows if x['kills'] is None]
   return sorted(known,key=lambda x:x[self.sort_key],reverse=self.reverse)+unknown
  key=(lambda x:(0 if x['completed'] else 1 if x['kills'] is not None else 2)) if self.sort_key=='state' else (lambda x:x[self.sort_key].casefold())
  return sorted(rows,key=key,reverse=self.reverse)
 def set_rows(self,rows,animate=True):
  self.source=rows;self.rows=self.ordered(rows);self.draw_header();self.canvas.yview_moveto(0)
  if animate:self.app.anim.tween(('rows',id(self)),450+28*len(self.rows),lambda t:self.update_reveal(t))
  else:self.reveal=1.0;self.draw()
 def update_reveal(self,t):self.reveal=t;self.draw()
 def row_at(self,event):
  index=int(unit(self.canvas.canvasy(event.y))//self.ROW);return index if 0<=index<len(self.rows) else None
 def motion(self,event):self.set_hover(self.row_at(event))
 def set_hover(self,index):
  if index!=self.hover:self.hover=index;self.draw()
 def click(self,event):
  index=self.row_at(event)
  if index is not None:self.app.inspect(self.rows[index])
 def draw(self):
  c=self.canvas;c.delete('all');w,_=size(c);cols=self.positions(w);total=450+28*len(self.rows);gains=self.app.gains()
  if not self.rows:
   c.create_text(w/2,60,text=self.app.T('empty' if self.app.data else 'next_wait'),fill=MUTED,font=(FONT,11));finish(c);c.configure(scrollregion=(0,0,px(w),px(120)));return
  for i,row in enumerate(self.rows):
   local=ease(max(0.0,min(1.0,(self.reveal*total-i*28)/450))) if self.reveal<1 else 1.0
   y=i*self.ROW+(1-local)*10;known=row['kills'] is not None;mid=y+self.ROW/2;chosen=row['weapon_id']==self.selected
   base=PANEL if i%2==0 else mix(PANEL,BG,0.45);bg=mix(BG,PANEL_HI if i==self.hover else base,local)
   rounded(c,8,y+2,w-8,y+self.ROW-2,10,fill=bg,outline=mix(bg,ACCENT,local) if chosen else '',width=2 if chosen else 1)
   if row['weapon_id'] in self.path:rounded(c,10,y+10,14,y+self.ROW-10,2,fill=mix(bg,ACCENT,local),outline='')
   text=mix(bg,FG,local);muted=mix(bg,MUTED,local);state_color=DONE if row['completed'] else (ACCENT if known else DIM);gain=gains.get(row['weapon_id'])
   for key,a,b,anchor in cols:
    if key=='weapon':
     image=self.app.weapon_image(row['weapon_id'],'s')
     if image and local>0.35:c.create_image(a+32,mid,image=image)
     c.create_text(a+64,mid,text=row['weapon'],anchor='w',fill=text,font=(FONT,11,'bold'))
    elif key=='weapon_id':c.create_text(a+8,mid,text=row['weapon_id'],anchor='w',fill=muted,font=(FONT,10))
    elif key=='kills':
     c.create_text(b-8,mid-(7 if gain else 0),text=self.app.num(row['kills']) if known else '—',anchor='e',fill=muted,font=(FONT,10))
     if gain:c.create_text(b-8,mid+11,text='+'+self.app.num(gain),anchor='e',fill=mix(bg,DONE,local),font=(FONT,9,'bold'))
    elif key=='remaining':c.create_text(b-8,mid,text=self.app.num(row['remaining']) if known else '—',anchor='e',fill=muted,font=(FONT,10))
    elif key=='progress':
     track_end=b-14;rounded(c,a+8,mid-3,track_end,mid+3,3,fill=mix(bg,LINE,local),outline='')
     if known:
      share=min(1.0,row['kills']/GOAL)*local
      if share>0:rounded(c,a+8,mid-3,a+8+(track_end-a-8)*share,mid+3,3,fill=mix(bg,DONE if row['completed'] else ACCENT,local),outline='')
    else:
     label=self.app.T('st_done' if row['completed'] else 'st_progress' if known else 'st_unknown');tw=measure(self.app.small,label)+22
     # Completed weapons get a solid gold chip so they stand apart from the bronze "in progress" ones.
     chip,ink=(mix(bg,DONE,local),mix(bg,INK,local)) if row['completed'] else (mix(bg,state_color,0.16*local),mix(bg,state_color,local))
     rounded(c,a+8,mid-11,a+8+tw,mid+11,11,fill=chip,outline='');c.create_text(a+8+tw/2,mid,text=label,fill=ink,font=self.app.small)
  finish(c);c.configure(scrollregion=(0,0,px(w),px(len(self.rows)*self.ROW+8)))
class Inspector(tk.Canvas):
 """Drawer with the weapon render and its numbers; slides in from the right of the collection view."""
 WIDTH=460
 def __init__(self,master,app):
  super().__init__(master,bg=PANEL,highlightthickness=0,bd=0);self.app=app;self.row=None;self.fill=0.0;self.shown=False
  self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.click)
 def open(self,row):
  self.row=row;self.fill=0.0;width=px(self.WIDTH)
  if not self.shown:
   self.shown=True;self.place(relx=1.0,x=width,rely=0,relheight=1,width=width,anchor='ne');tk.Misc.tkraise(self)
   self.app.anim.tween('inspector',280,lambda t:self.place_configure(x=width*(1-t)))
  target=min(1.0,(row['kills'] or 0)/GOAL)
  self.app.anim.tween('inspector_fill',700,lambda t:self.set_fill(target*t),delay=180)
 def set_fill(self,value):self.fill=value;self.draw()
 def hide(self):self.shown=False;self.place_forget()
 def close(self):
  if not self.shown:return
  self.shown=False;self.app.list.selected=None;self.app.list.draw();width=px(self.WIDTH)
  self.app.anim.tween('inspector',220,lambda t:self.place_configure(x=width*t),done=self.place_forget)
 def click(self,event):
  if unit(event.x)>size(self)[0]-48 and unit(event.y)<48:self.close()
 def draw(self):
  self.delete('all')
  if not self.row:return
  w,h=size(self);row=self.row;known=row['kills'] is not None;complete=row['completed'];color=DONE if complete else (ACCENT if known else DIM)
  self.create_line(1,0,1,h,fill=ACCENT,width=px(2));self.create_text(w-26,24,text='✕',fill=MUTED,font=(FONT,13,'bold'))
  self.create_oval(w/2-180,46,w/2+180,206,fill=mix(PANEL,color,0.12),outline='')
  image=self.app.weapon_image(row['weapon_id'],'l')
  if image:self.create_image(w/2,126,image=image)
  y=232;self.create_text(26,y,text=row['weapon'],anchor='w',fill=FG,font=(FONT,17,'bold'),width=px(w-52))
  self.create_text(26,y+28,text=f"{row['weapon_id']}  ·  {row['collection']}",anchor='w',fill=MUTED,font=(FONT,10))
  box=(w-52-12)/2
  for i,(key,value) in enumerate([('col_kills',row['kills']),('col_remaining',row['remaining'])]):
   x=26+i*(box+12);rounded(self,x,y+50,x+box,y+122,12,fill=PANEL_HI,outline='')
   self.create_text(x+16,y+68,text=self.app.T(key),anchor='w',fill=MUTED,font=(FONT,9,'bold'))
   self.create_text(x+16,y+100,text=self.app.num(value) if known else '—',anchor='w',fill=FG,font=(FONT,21,'bold'))
  bar=y+148;rounded(self,26,bar,w-26,bar+10,5,fill=LINE,outline='')
  if self.fill>0:rounded(self,26,bar,26+max(10,(w-52)*self.fill),bar+10,5,fill=color,outline='')
  if known:self.create_text(w-26,bar+30,text=f'{min(100,round(row["kills"]/GOAL*100))} %',anchor='e',fill=color,font=(FONT,11,'bold'))
  label=self.app.T('st_done' if complete else 'st_progress' if known else 'st_unknown');tw=measure(self.app.small,label)+22
  chip,ink=(DONE,INK) if complete else (mix(PANEL,color,0.18),color)
  rounded(self,26,bar+19,26+tw,bar+41,11,fill=chip,outline='');self.create_text(26+tw/2,bar+30,text=label,fill=ink,font=self.app.small)
  gain=self.app.gains().get(row['weapon_id'])
  if gain:self.create_text(26,bar+66,text=self.app.T('gain_session' if self.app.history.session else 'gain_read',kills=self.app.num(gain)),anchor='w',fill=DONE,font=(FONT,11,'bold'))
  finish(self)

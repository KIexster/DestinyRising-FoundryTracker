"""Shared building blocks: the animation loop, buttons, the toggle switch and the sliding tab strip."""
import time
import tkinter as tk
from tkinter import font as tkfont
from theme import BG,PANEL,PANEL_HI,LINE,MUTED,DIM,FG,ACCENT,TAB,INK,FONT,px,unit,measure,finish,mix,ease,rounded
class Animator:
 """One shared 60 fps loop for every tween, so idle windows cost nothing."""
 def __init__(self,root):self.root=root;self.items={};self.running=False
 def tween(self,key,duration,step,done=None,delay=0,curve=None):
  self.items[key]=(time.perf_counter()+delay/1000,max(duration,1)/1000,step,done,curve or ease)
  if not self.running:self.running=True;self.root.after(16,self.tick)
 def cancel(self,key):self.items.pop(key,None)
 def tick(self):
  now=time.perf_counter()
  for key,(start,duration,step,done,curve) in list(self.items.items()):
   if now<start:continue
   t=min(1.0,(now-start)/duration)
   try:step(curve(t))
   except tk.TclError:self.items.pop(key,None);continue
   if t>=1 and self.items.get(key,(None,))[0]==start:
    self.items.pop(key,None)
    if done:done()
  if self.items:self.root.after(16,self.tick)
  else:self.running=False
class FlatButton(tk.Label):
 def __init__(self,master,app,command,primary=False,**kw):
  self.app=app;self.command=command;self.enabled=True;self.mix=0.0
  self.base,self.hover,self.text=(ACCENT,'#f2d595',INK) if primary else (PANEL,PANEL_HI,FG)
  super().__init__(master,bg=self.base,fg=self.text,font=(FONT,10,'bold'),padx=px(18),pady=px(9),cursor='hand2',**kw)
  self.bind('<Enter>',lambda e:self.fade(1));self.bind('<Leave>',lambda e:self.fade(0));self.bind('<Button-1>',lambda e:self.enabled and self.command())
 def fade(self,target):
  if not self.enabled:return
  start=self.mix;self.app.anim.tween(('button',id(self)),140,lambda t:self.paint(start+(target-start)*t))
 def paint(self,v):self.mix=v;self.configure(bg=mix(self.base,self.hover,v))
 def set_enabled(self,enabled):
  self.enabled=enabled;self.configure(cursor='hand2' if enabled else 'arrow',fg=self.text if enabled else DIM,bg=self.base if enabled else PANEL)
  if enabled:self.paint(0)
class Toggle(tk.Frame):
 def __init__(self,master,app,variable,command,bg=BG):
  super().__init__(master,bg=bg,cursor='hand2');self.app=app;self.var=variable;self.command=command;self.pos=1.0 if variable.get() else 0.0;self.bg=bg
  self.canvas=tk.Canvas(self,width=px(40),height=px(22),bg=bg,highlightthickness=0);self.canvas.pack(side='left');self.label=tk.Label(self,bg=bg,fg=MUTED,font=(FONT,10));self.label.pack(side='left',padx=(px(8),0))
  for w in (self,self.canvas,self.label):w.bind('<Button-1>',self.toggle)
  self.draw()
 def toggle(self,_=None):
  self.var.set(not self.var.get());start=self.pos;target=1.0 if self.var.get() else 0.0
  self.app.anim.tween(('toggle',id(self)),180,lambda t:self.draw(start+(target-start)*t));self.command()
 def draw(self,pos=None):
  if pos is not None:self.pos=pos
  c=self.canvas;c.delete('all');rounded(c,1,2,39,20,9,fill=mix(LINE,ACCENT,self.pos));x=11+18*self.pos;c.create_oval(x-7,4,x+7,18,fill=mix(MUTED,INK,self.pos),outline='');finish(c)
class Segmented(tk.Canvas):
 """Tab strip whose highlight pill slides to the chosen option."""
 def __init__(self,master,app,options,command,small=False):
  self.app=app;self.options=options;self.command=command;self.small=small;self.font=tkfont.Font(family=FONT,size=9 if small else 10,weight='bold');self.labels=dict(options);self.current=options[0][0];self.pill=None;self.hover=None
  self.h=28 if small else 36
  super().__init__(master,height=px(self.h),bg=BG,highlightthickness=0,cursor='hand2')
  self.bind('<Button-1>',self.click);self.bind('<Motion>',self.motion);self.bind('<Leave>',lambda e:self.motion(None));self.layout()
 def layout(self):
  pad=12 if self.small else 18;x=2;self.spans=[]
  for key,_ in self.options:w=measure(self.font,self.labels[key])+pad*2;self.spans.append((key,x,x+w));x+=w+4
  self.configure(width=px(x));self.pill=self.span(self.current);self.draw()
 def span(self,key):return next((a,b) for k,a,b in self.spans if k==key)
 def set_labels(self,labels):self.labels.update(labels);self.layout()
 def select(self,key,animate=True):
  self.current=key;start=self.pill;end=self.span(key)
  if not animate or start is None:self.pill=end;self.draw();return
  self.app.anim.tween(('segment',id(self)),220,lambda t:self.slide(start,end,t))
 def slide(self,start,end,t):self.pill=(start[0]+(end[0]-start[0])*t,start[1]+(end[1]-start[1])*t);self.draw()
 def click(self,event):
  x=unit(event.x)
  for key,a,b in self.spans:
   if a<=x<=b and key!=self.current:self.select(key);self.command(key)
 def motion(self,event):
  over=next((k for k,a,b in self.spans if event and a<=unit(event.x)<=b),None)
  if over!=self.hover:self.hover=over;self.draw()
 def draw(self):
  self.delete('all');h=self.h;rounded(self,0,0,self.spans[-1][2]+2,h,h/2,fill=PANEL)
  if self.pill:rounded(self,self.pill[0],3,self.pill[1],h-3,(h-6)/2,fill=ACCENT if self.small else TAB)
  for key,a,b in self.spans:
   active=key==self.current;color=(INK if self.small else FG) if active else (FG if key==self.hover else MUTED)
   self.create_text((a+b)/2,h/2,text=self.labels[key],fill=color,font=self.font)
  finish(self)

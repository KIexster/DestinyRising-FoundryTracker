"""Emblem cards on the home screen."""
import tkinter as tk
from theme import BG,PANEL,PANEL_HI,LINE,MUTED,FG,ACCENT,DONE,ARC,FONT,px,size,finish,mix,rounded
class EmblemCard(tk.Canvas):
 def __init__(self,master,app,collection,image,index):
  super().__init__(master,bg=BG,highlightthickness=0,bd=0,cursor='hand2')
  self.app=app;self.g=collection;self.image=image;self.index=index;self.hover=0.0;self.reveal=0.0;self.fill=0.0;self.progress=None;self.glow=0.0
  self.bind('<Configure>',lambda e:self.draw());self.bind('<Enter>',lambda e:self.set_hover(1));self.bind('<Leave>',lambda e:self.set_hover(0));self.bind('<Button-1>',lambda e:app.open_collection(collection['id']))
 def set_hover(self,target):
  start=self.hover;self.app.anim.tween(('hover',id(self)),180,lambda t:self.update_value('hover',start+(target-start)*t))
 def update_value(self,name,value):setattr(self,name,value);self.draw()
 def enter(self,delay=0):self.app.anim.tween(('reveal',id(self)),480,lambda t:self.update_value('reveal',t),delay=delay+self.index*70)
 def set_progress(self,progress):
  start=self.fill;target=float(progress or 0);self.progress=progress
  self.app.anim.tween(('fill',id(self)),700,lambda t:self.update_value('fill',start+(target-start)*t),delay=200+self.index*80)
 def draw(self):
  self.delete('all');w,h=size(self)
  if w<40 or h<40:return
  r=self.reveal;complete=(self.progress or 0)>=8;shift=(1-r)*24-self.hover*4
  bg=mix(BG,mix(PANEL,PANEL_HI,self.hover),r);edge=mix(BG,mix(LINE,ACCENT,max(self.hover*0.85,self.glow*0.7 if complete else 0)),r)
  # The frame stays put (a shifted frame clipped at the canvas edge); only the content rises on hover.
  rounded(self,2,2,w-2,h-2,16,fill=bg,outline=edge,width=2 if complete or self.hover>0.5 else 1)
  # Halo + emblem 88 + name + pips + status, centred with 14 px on top so the halo keeps clear of the
  # frame when lifted on hover. Short cards shrink the halo first, then tighten the gaps below the emblem.
  radius=max(44,min(52,h-143));k=max(0.8,min(1.0,(h-28-radius)/113));below=113*k+8
  cx=w/2;cy=max(14,(h-radius-below)/2)+radius+shift
  halo=mix(bg,ACCENT if complete else ARC,(0.10+0.12*self.hover+(0.10*self.glow if complete else 0))*r)
  self.create_oval(cx-radius,cy-radius,cx+radius,cy+radius,fill=halo,outline='')
  if r>0.15:self.create_image(cx,cy,image=self.image)
  name_y=cy+68*k;self.create_text(cx,name_y,text=self.g['name'],fill=mix(bg,FG,r),font=(FONT,13,'bold'),width=px(w-36))
  pip,gap=24,6;x0=cx-(8*pip+7*gap)/2;y=name_y+20*k;color=DONE if complete else ACCENT
  for i in range(8):
   x=x0+i*(pip+gap);base=mix(bg,LINE,r)
   if self.app.busy:base=mix(base,ARC,max(0,1-abs(i-self.app.shimmer))*0.55)
   rounded(self,x,y,x+pip,y+7,3,fill=base,outline='')
   part=max(0.0,min(1.0,self.fill-i))
   if part>0:rounded(self,x,y,x+pip*part,y+7,3,fill=mix(base,color,r),outline='')
  self.create_text(cx,y+25*k,text=self.app.card_status(self.g['id']),fill=mix(bg,DONE if complete else MUTED,r),font=(FONT,10))
  gain=self.app.collection_gain(self.g['id'])
  if gain and r>0.5:self.create_text(w-16,18,text='+'+self.app.num(gain),anchor='ne',fill=mix(bg,DONE,r),font=(FONT,10,'bold'))
  finish(self)

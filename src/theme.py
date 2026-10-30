"""Palette, fonts and drawing helpers. Change the look of the whole app from here.

Canvases are drawn in 96-dpi units and mapped to real pixels with finish(), so the layout stays
the same on 125 % / 150 % displays while text stays sharp (Tk sizes the fonts itself).
"""
# Black and gold palette
BG='#0b0a08'          # window background
PANEL='#151310'       # cards, rows, panels
PANEL_HI='#221d15'    # hovered panel
LINE='#3a3122'        # borders, empty bars and pips
MUTED='#b8a888'       # secondary text
DIM='#6e6250'         # disabled text, "no record"
FG='#f7f0e1'          # main text
ACCENT='#d9a84e'      # gold: buttons, titles, in-progress bars
DONE='#ffd98a'        # light gold: completed weapons and achievements
ARC='#fff0c8'         # loading shimmer and soft halos
ERROR='#ff8f84'
STATUS='#e2d2ad'      # status line while reading
TAB='#3b3020'         # selected filter tab
INK='#1b1408'         # text on gold
SPLASH_BG='#100f0f'   # edge colour of the opening emblem
FONT='Segoe UI'

S=1.0
def init_scale(root):
 """Reads the display scale once (1.0 at 96 dpi). Call it right after creating the Tk root."""
 global S
 try:S=max(1.0,round(root.winfo_fpixels('1i')/96,2))
 except Exception:S=1.0
 return S
def px(value):return int(round(value*S))
def unit(value):return value/S
def size(widget):return widget.winfo_width()/S,widget.winfo_height()/S
def measure(font,text):return font.measure(text)/S
def finish(canvas):
 if S!=1.0:canvas.scale('all',0,0,S,S)
def mix(a,b,t):
 t=max(0.0,min(1.0,t));a=int(a[1:],16);b=int(b[1:],16)
 return '#%02x%02x%02x'%tuple(round(((a>>s)&255)+(((b>>s)&255)-((a>>s)&255))*t) for s in (16,8,0))
def ease(t):return 1-(1-t)**3
def ease_in_out(t):return 4*t**3 if t<0.5 else 1-(-2*t+2)**3/2
def rounded(canvas,x1,y1,x2,y2,r,**kw):
 r=max(0,min(r,(x2-x1)/2,(y2-y1)/2))
 return canvas.create_polygon(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1,smooth=True,**kw)

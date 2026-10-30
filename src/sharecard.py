"""PNG share card (1200x720) in the black and gold style, drawn with Pillow."""
import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from resources import BASE,CATALOG
from theme import BG,PANEL,LINE,MUTED,FG,ACCENT,DONE
W,H=1200,720
def font(size,bold=False):
 folder=os.path.join(os.environ.get('WINDIR','C:\\Windows'),'Fonts')
 for name in (('segoeuib.ttf','arialbd.ttf') if bold else ('segoeui.ttf','arial.ttf')):
  try:return ImageFont.truetype(os.path.join(folder,name),size)
  except OSError:pass
 return ImageFont.load_default()
def logo(size):
 """The gold wolves emblem, cut out of the two halves used by the opening animation."""
 halves=[Image.open(BASE/'emblems'/name).convert('RGB') for name in ('splash_left.png','splash_right.png')]
 full=Image.new('RGB',(halves[0].width+halves[1].width,halves[0].height));full.paste(halves[0],(0,0));full.paste(halves[1],(halves[0].width,0))
 cx,cy,r=full.width//2,full.height//2,int(full.height*0.385)
 return full.crop((cx-r,cy-r,cx+r,cy+r)).resize((size,size),Image.LANCZOS)
def emblem(collection,size):
 path=BASE/collection['emblem'].replace('.png','_original.png')
 if not path.exists():path=BASE/collection['emblem']
 return Image.open(path).convert('RGBA').resize((size,size),Image.LANCZOS)
def render(path,data,texts):
 """texts: title, subtitle and footer, already translated by the caller."""
 card=Image.new('RGB',(W,H),BG)
 glow=Image.new('L',(W,H),0);ImageDraw.Draw(glow).ellipse((W*0.2,-260,W*0.8,260),fill=70);glow=glow.filter(ImageFilter.GaussianBlur(90))
 card=Image.composite(Image.new('RGB',(W,H),ACCENT),card,glow.point(lambda v:v*0.35))
 mark=logo(112);mask=Image.new('L',mark.size,0);ImageDraw.Draw(mask).ellipse((1,1,110,110),fill=255)
 card.paste(mark,(48,34),mask.filter(ImageFilter.GaussianBlur(1)));d=ImageDraw.Draw(card)
 d.text((182,52),texts['title'],font=font(40,True),fill=ACCENT);d.text((184,104),texts['subtitle'],font=font(22),fill=MUTED)
 progress={x['id']:x['progress'] for x in data['summary']};groups=CATALOG['collections'];tile,gap=250,20
 rows=[groups[:4],groups[4:]]
 for r,row in enumerate(rows):
  x0=(W-(len(row)*tile+(len(row)-1)*gap))//2;y=180+r*240
  for i,g in enumerate(row):
   x=x0+i*(tile+gap);value=progress.get(g['id'],0);complete=value>=8
   d.rounded_rectangle((x,y,x+tile,y+220),radius=18,fill=PANEL,outline=DONE if complete else LINE,width=3 if complete else 2)
   icon=emblem(g,96);card.paste(icon,(x+(tile-96)//2,y+16),icon)
   d.text((x+tile/2,y+134),g['name'],font=font(20,True),fill=FG,anchor='mm')
   pip,space=22,5;px0=x+(tile-(8*pip+7*space))/2
   for p in range(8):d.rounded_rectangle((px0+p*(pip+space),y+158,px0+p*(pip+space)+pip,y+164),radius=3,fill=(DONE if complete else ACCENT) if p<value else LINE)
   d.text((x+tile/2,y+192),f'{value} / 8',font=font(18,True),fill=DONE if complete else MUTED,anchor='mm')
 d.text((W-40,H-28),texts['footer'],font=font(18),fill=MUTED,anchor='rs')
 card.save(path)
 return path

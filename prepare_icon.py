"""Internal tool: builds src/emblems/app_icon.ico (window, taskbar and .exe icon) from the gold wolves emblem."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
ROOT=Path(__file__).parent;EMBLEMS=ROOT/'src'/'emblems'
SIZES=[16,20,24,32,40,48,64,128,256]
def emblem(size):
 halves=[Image.open(EMBLEMS/name).convert('RGB') for name in ('splash_left.png','splash_right.png')]
 full=Image.new('RGB',(halves[0].width+halves[1].width,halves[0].height));full.paste(halves[0],(0,0));full.paste(halves[1],(halves[0].width,0))
 cx,cy,r=full.width//2,full.height//2,int(full.height*0.395)
 art=full.crop((cx-r,cy-r,cx+r,cy+r)).resize((size,size),Image.LANCZOS)
 if size<=48:art=ImageEnhance.Contrast(art).enhance(1.35).filter(ImageFilter.UnsharpMask(1,120,2))
 elif size<=128:art=ImageEnhance.Contrast(art).enhance(1.2).filter(ImageFilter.UnsharpMask(1,60,2))
 big=size*4;mask=Image.new('L',(big,big),0);ImageDraw.Draw(mask).ellipse((2,2,big-3,big-3),fill=255)
 icon=art.convert('RGBA');icon.putalpha(mask.resize((size,size),Image.LANCZOS));return icon
def main():
 images=[emblem(s) for s in SIZES]
 images[-1].save(EMBLEMS/'app_icon.png')
 images[-1].save(EMBLEMS/'app_icon.ico',sizes=[(s,s) for s in SIZES],append_images=images[:-1])
 print('icono',EMBLEMS/'app_icon.ico')
if __name__=='__main__':main()

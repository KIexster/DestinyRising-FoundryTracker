"""Internal tool: builds the weapon images bundled in src/weapons from ../Assets/Weapons.

Each catalog weapon gets {id}_s.png (48 px list thumbnail), {id}_m.png (72 px thumbnail for displays
scaled 130 % or more) and {id}_l.png (detail render, fits 420x165).
The source folders are named after the weapon; the files inside start with the weapon ID.
"""
import re,json,glob
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).parent;ASSETS=ROOT.parent/'Assets'/'Weapons';OUT=ROOT/'src'/'weapons'
THUMB=48;THUMB_HI=72;LARGE=(420,165)
def source(weapon_id,kinds):
 # Variant IDs such as aw03s03t01 (The Jade Rabbit) reuse the art of their base weapon.
 for wid in dict.fromkeys([weapon_id,re.sub(r't\d+$','',weapon_id)]):
  for kind in kinds:
   found=sorted(glob.glob(str(ASSETS/'*'/f'{wid}_{kind}__*.png')))
   if found:return Image.open(found[0]).convert('RGBA')
 return None
def fit(image,box):
 scale=min(box[0]/image.width,box[1]/image.height,1.0)
 return image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.LANCZOS)
def main():
 OUT.mkdir(exist_ok=True);catalog=json.loads((ROOT/'src'/'catalog.json').read_text('utf-8'));missing=[]
 for weapon_id in sorted({w['weapon_id'] for w in catalog['weapons']}):
  small=source(weapon_id,['gear','gear_fullsize','gear_bigsize']);large=source(weapon_id,['gear_bigsize','gear_fullsize','gear'])
  if small is None:missing.append(weapon_id);continue
  fit(small,(THUMB,THUMB)).save(OUT/f'{weapon_id}_s.png',optimize=True);fit(small,(THUMB_HI,THUMB_HI)).save(OUT/f'{weapon_id}_m.png',optimize=True)
  fit(large,LARGE).save(OUT/f'{weapon_id}_l.png',optimize=True)
 print('imágenes',len(list(OUT.glob('*_s.png'))),'sin imagen',missing)
if __name__=='__main__':main()

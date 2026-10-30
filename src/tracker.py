from pathlib import Path
import json,struct,subprocess,hashlib,datetime,time,atexit
from memory_reader import FastReader
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
# CPython 3.12 layout of the game's interpreter and the C++ chain from the player to its property table.
# catalog.json "engine" and %APPDATA%\FoundryTracker\engine.json override any of these values.
ENGINE=dict(runtime_offset=0x75f1d08,runtime_head=0x28,interp_runtime=40,interp_modules=0x378,player_storage=[32,16,32,0,512,32])
# _PyRuntime starts with _initialized, preinitializing, preinitialized, core_initialized and initialized.
RUNTIME_HEADER=struct.pack('<5i',1,0,1,1,1)
SCAN_PAGES=64
MODULE_BATCH=64
class TrackerError(Exception):pass
class StructureError(TrackerError):
 """Memory without the expected layout. On an unverified build it means the reader needs an update."""
def engine_config(catalog):
 e=dict(ENGINE);e.update(catalog.get('engine',{}))
 return {k:int(v,0) if isinstance(v,str) else v for k,v in e.items()}
def outdated(patch,catalog):
 if patch:return TrackerError(f'Build {patch} no validada. Esta versión admite {catalog["expected_patch"]}. Actualiza el lector.')
 return TrackerError('Motor no compatible con esta versión del lector. Se detuvo la lectura; hace falta actualizar Foundry Tracker.')
def command(adb,args,timeout=15,check=True):
 p=subprocess.run([str(adb)]+args,capture_output=True,timeout=timeout,creationflags=FLAGS)
 if check and p.returncode:raise TrackerError('ADB no pudo completar la lectura. Comprueba MuMu y su acceso root.')
 return p.stdout.decode('utf-8','replace').strip()
def discover(adb,package):
 raw=command(adb,['devices']);serials=[x.split()[0] for x in raw.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=='device']
 if not serials:
  command(adb,['connect','127.0.0.1:16384'],check=False)
  raw=command(adb,['devices']);serials=[x.split()[0] for x in raw.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=='device']
 found={}
 for serial in serials:
  # MuMu can be listed twice (emulator-5554 and 127.0.0.1:16384); boot_id tells apart real instances.
  out=command(adb,['-s',serial,'shell',f'echo B:$(cat /proc/sys/kernel/random/boot_id) P:$(pidof {package})'],check=False).split()
  boot=next((x[2:] for x in out if x.startswith('B:')),'');pid=next((x[2:] for x in out if x.startswith('P:')),'')
  if pid.isdigit():found.setdefault(boot or serial,(serial,pid))
 found=list(found.values())
 if not found:raise TrackerError('No se encontró Destiny Rising GLOBAL abierto. Enciende MuMu, habilita ADB y abre tu personaje en el juego.')
 if len(found)!=1:raise TrackerError('Hay varias sesiones del juego abiertas. Deja abierta solo la que quieres consultar.')
 return found[0]
class Session(FastReader):
 def close(self):
  super().close()
  atexit.unregister(self.close)
  self.cache.clear();self.types.clear()
 def __init__(self,adb,serial,pid,catalog):
  self.adb=str(adb);self.serial=serial;self.pid=pid;self.cache={};self.calls=0;self.types={};self.channel=None;self.ranges=[];self.base=None
  self.engine=engine_config(catalog);self.runtime=None;self.data_ranges=[]
  root=command(adb,['-s',serial,'shell','su','0','id'],check=False)
  if 'uid=0' not in root:raise TrackerError('Se necesita acceso root de MuMu para leer los contadores. Actívalo en la configuración del emulador.')
  raw=command(adb,['-s',serial,'shell','su','0','cat',f'/proc/{pid}/maps']);game_rw=False
  for line in raw.splitlines():
   p=line.split();a,b=(int(x,16) for x in p[0].split('-'));self.ranges.append((a,b,p[1]));path=p[-1] if len(p)>5 else ''
   if path.endswith('/libGame.so') and int(p[2],16)==0:self.base=a
   # libGame's writable data and the .bss right after it hold the interpreter state.
   game_rw=p[1].startswith('rw') and (path.endswith('/libGame.so') or (path=='[anon:.bss]' and game_rw))
   if game_rw:self.data_ranges.append((a,b))
  if not self.base:raise TrackerError('El motor del juego aún no está cargado. Espera a entrar con tu personaje.')
  self.header_sha=hashlib.sha256(self.read(self.base,4096)).hexdigest();self.verified_engine=self.header_sha==catalog['engine_header_sha256']
 def is_runtime(self,a):
  e=self.engine
  try:
   interp=self.q(a+e['runtime_head'])
   return bool(interp) and self.q(interp+e['interp_runtime'])==a and self.typ(self.q(interp+e['interp_modules']))=='dict'
  except ValueError:return False
 def locate(self,hints=(),status=lambda message:None):
  """Find _PyRuntime: known offsets first, then libGame's data scanned outwards from the known one. Returns its offset."""
  for off in dict.fromkeys(list(hints)+[self.engine['runtime_offset']]):
   if self.is_runtime(self.base+off):self.runtime=self.base+off;return off
  status('Build nueva: buscando el intérprete del juego en memoria (solo la primera vez)…')
  chunk=SCAN_PAGES*4096;near=self.base+self.engine['runtime_offset'];head=self.engine['runtime_head']
  starts=sorted(((s,b) for a,b in self.data_ranges for s in range(a,b,chunk)),key=lambda x:abs(x[0]-near))
  for start,end in starts:
   # One extra page so a header that crosses into the next chunk is still seen whole.
   count=min(SCAN_PAGES+1,(end-start)//4096);data=self.block(start,count)
   for j in range(count):self.cache.setdefault(start+j*4096,data[j*4096:(j+1)*4096])
   i=data.find(RUNTIME_HEADER)
   while 0<=i<chunk and i+head+24<=len(data):
    interp,main,next_id=struct.unpack_from('<3Q',data,i+head)
    if i%8==0 and interp and interp==main and 1<=next_id<=64 and self.is_runtime(start+i):self.runtime=start+i;return self.runtime-self.base
    i=data.find(RUNTIME_HEADER,i+4)
  raise StructureError('No se encontró el intérprete del juego en memoria.')
 def module(self,name,hint=None):
  entries=self.dict_entries(self.modules());values=dict(entries)
  # A refresh of the same game process checks the key found last time before reading thousands of module names.
  if hint in values and self.string(hint)==name:
   self.module_key=hint;self.module_address=values[hint];return values[hint]
  # Otherwise the names are fetched MODULE_BATCH at a time and the search stops at the first match.
  for i in range(0,len(entries),MODULE_BATCH):
   batch=entries[i:i+MODULE_BATCH];self.gather([k for k,v in batch])
   for k,v in batch:
    if self.string(k)==name:
     self.module_key=k;self.module_address=v;return v
  raise TrackerError('El juego aún no tiene cargado el módulo del personaje.')
 def modules(self):
  # Stable interpreter list, independent of whether a Python thread currently owns the GIL.
  e=self.engine;interp=self.q(self.runtime+e['runtime_head'])
  if not interp or self.q(interp+e['interp_runtime'])!=self.runtime:raise StructureError('Intérprete no compatible o todavía sin inicializar.')
  return self.q(interp+e['interp_modules'])
 def module_attrs(self,a):
  """Module globals by name; the key objects are kept in attr_keys so later checks can compare pointers."""
  entries=self.dict_entries(self.q(a+16));self.gather([k for k,v in entries]);self.attr_keys={};values=dict(entries)
  for k,v in entries:
   if self.typ(k)=='str':self.attr_keys[self.string(k)]=k
  return {name:values[k] for name,k in self.attr_keys.items()}
 def cppstr(self,a):
  flag=self.read(a,1)[0];n=self.q(a+8) if flag&1 else flag>>1;p=self.q(a+16) if flag&1 else a+1
  if n>100000:raise StructureError('Cadena fuera de límites; lectura detenida.')
  return self.read(p,n).decode('utf-8')
 def int_map(self,a):
  w=self.q(self.q(a+32)+16);data=self.q(w+16)
  if self.q(w+24):raise StructureError('Formato inesperado de contadores.')
  count=self.q(data+40)
  if count>10000:raise StructureError('Contador fuera de límites.')
  node=self.q(data+32);seen=set();out={}
  while node:
   if node in seen or len(seen)>=10000:raise TrackerError('Mapa inconsistente; vuelve a actualizar.')
   seen.add(node);keyptr=self.q(node+16)&~7;kind=self.read(keyptr+20,1)[0]
   if kind==0:key=struct.unpack('<q',self.read(keyptr+24,8))[0]
   elif kind==1:key=self.cppstr(keyptr+24)
   else:raise StructureError('Tipo de clave no compatible.')
   if self.read(node+40,1)[0]!=0:raise StructureError('Tipo de valor no compatible.')
   value=struct.unpack('<q',self.read(node+32,8))[0]
   out[str(key)]=value;node=self.q(node)
  if len(out)!=count:raise TrackerError('Los contadores cambiaron durante la lectura. Actualiza de nuevo.')
  return out
 def counters(self,player):
  storage=player
  for off in self.engine['player_storage']:storage=self.q(storage+off)
  wrap=self.q(storage+16);meta=self.q(wrap);table=self.q(meta+32);node=self.q(table+32);count=self.q(table+40)
  if not 1<=count<=10000:raise StructureError('No se reconoce la tabla de propiedades de esta build.')
  vec=self.q(self.q(wrap+24)+24);seen=set();out={}
  wanted={'AttachmentProcess_weaponKillData','Achievement_listenAchiData','Achievement_finishAchiData'}
  while node:
   if node in seen or len(seen)>=10000:raise StructureError('Tabla de propiedades inconsistente.')
   seen.add(node);key=self.string(self.q(node+16));desc=self.q(node+24)
   if key in wanted:
    idx=struct.unpack('<i',self.read(desc,4))[0]
    if not 0<=idx<count:raise StructureError('Índice de propiedad inválido.')
    at=vec+idx*16
    if self.read(at+8,1)[0]!=4:raise StructureError('El contador tiene un formato no compatible.')
    value=self.q(at);out[key]=self.int_map(value) if value else {}
    if wanted.issubset(out):break
   node=self.q(node)
  if not wanted.issubset(out):raise TrackerError('Faltan propiedades del personaje. Espera a terminar la carga.')
  return out
def collect(adb,catalog,status=lambda message:None,hints=None,warm=None):
 """hints: {libGame header sha256: runtime offset as hex} remembered from earlier reads.
 warm: the 'warm' entry of the previous result. Its pages are fetched fresh up front in a few round trips,
 so a refresh of the same game process costs a few batches instead of hundreds of single-page reads."""
 start=time.monotonic();status('Buscando el juego en MuMu…');serial,pid=discover(adb,catalog['package']);session=None;patch=None;verified=True
 try:
  session=Session(adb,serial,pid,catalog);verified=session.verified_engine;status('Localizando el personaje y comprobando la build…')
  key=f'{serial}:{pid}:{session.header_sha}';same=isinstance(warm,dict) and warm.get('key')==key
  if same:session.gather(warm.get('pages') or [])
  try:known=[int((hints or {})[session.header_sha],16)]
  except (KeyError,ValueError,TypeError):known=[]
  session.locate(known,status)
  attrs=session.module_attrs(session.module('Game.Game',warm.get('module') if same else None))
  patch=session.string(attrs['PATCH_VERSION']);verified=verified and patch==catalog['expected_patch']
  if not verified:status('Build sin verificar: comprobando la estructura antes de mostrar nada…')
  player=attrs.get('Player')
  if not player or session.typ(player)!='PlayerAvatar':raise TrackerError('Entra con tu personaje al menú del juego para leer sus logros.')
  status('Leyendo contadores de bajas y progreso. No cambies de personaje…');maps=session.counters(player)
  current=command(adb,['-s',serial,'shell','pidof',catalog['package']],check=False).split()
  if not current or current[0]!=pid:raise TrackerError('El juego se cerró o reinició. Vuelve a actualizar.')
  session.cache.clear()
  if (session.module_key,session.module_address) not in session.dict_entries(session.modules()) or session.string(session.module_key)!='Game.Game':raise TrackerError('El modulo cambio durante la lectura.')
  if (session.attr_keys['Player'],player) not in session.dict_entries(session.q(session.module_address+16)):raise TrackerError('Cambió el personaje durante la lectura. Actualiza de nuevo.')
  kills=maps['AttachmentProcess_weaponKillData'];progress=maps['Achievement_listenAchiData'];finished=maps['Achievement_finishAchiData'];rows=[];summary=[]
  if any(not 0<=v<=10**12 for v in kills.values()):raise StructureError('Se rechazaron contadores fuera de rango.')
  for item in catalog['weapons']:
   k=kills.get(item['weapon_id']);rows.append(dict(item,kills=k,remaining=max(0,1000-k) if k is not None else None,completed=k is not None and k>=1000))
  for group in catalog['collections']:
   aid=str(group['id']);measured=sum(x['completed'] for x in rows if x['achievement_id']==group['id']);recorded=8 if aid in finished else progress.get(aid,0)
   summary.append(dict(group,progress=recorded,measured=measured,consistent=min(measured,8)==min(recorded,8)))
  # On a build nobody has checked yet, every achievement must agree with its weapons before anything is shown.
  if not verified and not all(x['consistent'] for x in summary):raise StructureError('Los logros no cuadran con las armas en una build sin verificar.')
  engine=dict(header_sha256=session.header_sha,runtime_offset=hex(session.runtime-session.base))
  return dict(captured_at=datetime.datetime.now().astimezone().isoformat(),serial=serial,package=catalog['package'],patch=patch,pid=pid,verified_build=verified,engine=engine,weapon_counter_count=len(kills),duration_seconds=round(time.monotonic()-start,1),summary=summary,rows=rows,warm=dict(key=key,module=session.module_key,pages=sorted(session.touched)))
 except StructureError as exc:
  if not verified:raise outdated(patch,catalog) from exc
  raise
 except (TrackerError,subprocess.TimeoutExpired):raise
 except Exception as exc:
  if not verified:raise outdated(patch,catalog) from exc
  raise TrackerError('No se pudo validar la estructura del juego. Espera a terminar la carga y actualiza. Detalle: '+str(exc)) from exc
 finally:
  if session:session.close()

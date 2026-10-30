from pathlib import Path
import json,struct,subprocess,hashlib,datetime,time,atexit
from memory_reader import FastReader
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
class TrackerError(Exception):pass
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
  root=command(adb,['-s',serial,'shell','su','0','id'],check=False)
  if 'uid=0' not in root:raise TrackerError('Se necesita acceso root de MuMu para leer los contadores. Actívalo en la configuración del emulador.')
  raw=command(adb,['-s',serial,'shell','su','0','cat',f'/proc/{pid}/maps'])
  for line in raw.splitlines():
   p=line.split();a,b=(int(x,16) for x in p[0].split('-'));self.ranges.append((a,b,p[1]))
   if len(p)>5 and p[-1].endswith('/libGame.so') and int(p[2],16)==0:self.base=a
  if not self.base:raise TrackerError('El motor del juego aún no está cargado. Espera a entrar con tu personaje.')
  if hashlib.sha256(self.read(self.base,4096)).hexdigest()!=catalog['engine_header_sha256']:
   self.close();raise TrackerError('Motor no compatible con esta versión del lector. Se detuvo la lectura; hace falta actualizar Foundry Tracker.')
 def module(self,name):
  for k,v in self.dict_entries(self.modules()):
   if self.string(k)==name:
    self.module_key=k;self.module_address=v;return v
  raise TrackerError('El juego aún no tiene cargado el módulo del personaje.')
 def modules(self):
  # Stable interpreter list, independent of whether a Python thread currently owns the GIL.
  runtime=self.base+0x75f1d08;interp=self.q(runtime+0x28)
  if not interp or self.q(interp+40)!=runtime:raise TrackerError('Intérprete no compatible o todavía sin inicializar.')
  return self.q(interp+0x378)
 def module_attrs(self,a):return {self.string(k):v for k,v in self.dict_entries(self.q(a+16)) if self.typ(k)=='str'}
 def cppstr(self,a):
  flag=self.read(a,1)[0];n=self.q(a+8) if flag&1 else flag>>1;p=self.q(a+16) if flag&1 else a+1
  if n>100000:raise TrackerError('Cadena fuera de límites; lectura detenida.')
  return self.read(p,n).decode('utf-8')
 def int_map(self,a):
  w=self.q(self.q(a+32)+16);data=self.q(w+16)
  if self.q(w+24):raise TrackerError('Formato inesperado de contadores.')
  count=self.q(data+40)
  if count>10000:raise TrackerError('Contador fuera de límites.')
  node=self.q(data+32);seen=set();out={}
  while node:
   if node in seen or len(seen)>=10000:raise TrackerError('Mapa inconsistente; vuelve a actualizar.')
   seen.add(node);keyptr=self.q(node+16)&~7;kind=self.read(keyptr+20,1)[0]
   if kind==0:key=struct.unpack('<q',self.read(keyptr+24,8))[0]
   elif kind==1:key=self.cppstr(keyptr+24)
   else:raise TrackerError('Tipo de clave no compatible.')
   if self.read(node+40,1)[0]!=0:raise TrackerError('Tipo de valor no compatible.')
   value=struct.unpack('<q',self.read(node+32,8))[0]
   out[str(key)]=value;node=self.q(node)
  if len(out)!=count:raise TrackerError('Los contadores cambiaron durante la lectura. Actualiza de nuevo.')
  return out
 def counters(self,player):
  s=self.q(player+32);e=self.q(s+16);p=self.q(e+32);c=self.q(p);b=self.q(c+512);storage=self.q(b+32)
  wrap=self.q(storage+16);meta=self.q(wrap);table=self.q(meta+32);node=self.q(table+32);count=self.q(table+40)
  if not 1<=count<=10000:raise TrackerError('No se reconoce la tabla de propiedades de esta build.')
  vec=self.q(self.q(wrap+24)+24);seen=set();out={}
  wanted={'AttachmentProcess_weaponKillData','Achievement_listenAchiData','Achievement_finishAchiData'}
  while node:
   if node in seen or len(seen)>=10000:raise TrackerError('Tabla de propiedades inconsistente.')
   seen.add(node);key=self.string(self.q(node+16));desc=self.q(node+24)
   if key in wanted:
    idx=struct.unpack('<i',self.read(desc,4))[0]
    if not 0<=idx<count:raise TrackerError('Índice de propiedad inválido.')
    at=vec+idx*16
    if self.read(at+8,1)[0]!=4:raise TrackerError('El contador tiene un formato no compatible.')
    value=self.q(at);out[key]=self.int_map(value) if value else {}
    if wanted.issubset(out):break
   node=self.q(node)
  if not wanted.issubset(out):raise TrackerError('Faltan propiedades del personaje. Espera a terminar la carga.')
  return out
def collect(adb,catalog,status=lambda message:None):
 start=time.monotonic();status('Buscando el juego en MuMu…');serial,pid=discover(adb,catalog['package']);session=None
 try:
  session=Session(adb,serial,pid,catalog);status('Localizando el personaje y comprobando la build…')
  attrs=session.module_attrs(session.module('Game.Game'))
  patch=session.string(attrs['PATCH_VERSION'])
  if patch!=catalog['expected_patch']:raise TrackerError(f'Build {patch} no validada. Esta versión admite {catalog["expected_patch"]}. Actualiza el lector.')
  player=attrs.get('Player')
  if not player or session.typ(player)!='PlayerAvatar':raise TrackerError('Entra con tu personaje al menú del juego para leer sus logros.')
  status('Leyendo contadores de bajas y progreso. No cambies de personaje…');maps=session.counters(player)
  current=command(adb,['-s',serial,'shell','pidof',catalog['package']],check=False).split()
  if not current or current[0]!=pid:raise TrackerError('El juego se cerró o reinició. Vuelve a actualizar.')
  session.cache.clear()
  if (session.module_key,session.module_address) not in session.dict_entries(session.modules()) or session.string(session.module_key)!='Game.Game':raise TrackerError('El modulo cambio durante la lectura.')
  if session.module_attrs(session.module_address).get('Player')!=player:raise TrackerError('Cambió el personaje durante la lectura. Actualiza de nuevo.')
  kills=maps['AttachmentProcess_weaponKillData'];progress=maps['Achievement_listenAchiData'];finished=maps['Achievement_finishAchiData'];rows=[];summary=[]
  if any(not 0<=v<=10**12 for v in kills.values()):raise TrackerError('Se rechazaron contadores fuera de rango.')
  for item in catalog['weapons']:
   k=kills.get(item['weapon_id']);rows.append(dict(item,kills=k,remaining=max(0,1000-k) if k is not None else None,completed=k is not None and k>=1000))
  for group in catalog['collections']:
   aid=str(group['id']);measured=sum(x['completed'] for x in rows if x['achievement_id']==group['id']);recorded=8 if aid in finished else progress.get(aid,0)
   summary.append(dict(group,progress=recorded,measured=measured,consistent=min(measured,8)==min(recorded,8)))
  return dict(captured_at=datetime.datetime.now().astimezone().isoformat(),serial=serial,package=catalog['package'],patch=patch,pid=pid,weapon_counter_count=len(kills),duration_seconds=round(time.monotonic()-start,1),summary=summary,rows=rows)
 except (TrackerError,subprocess.TimeoutExpired):raise
 except Exception as exc:raise TrackerError('No se pudo validar la estructura del juego. Espera a terminar la carga y actualiza. Detalle: '+str(exc)) from exc
 finally:
  if session:session.close()

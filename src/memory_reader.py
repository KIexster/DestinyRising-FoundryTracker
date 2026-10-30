import struct,subprocess,concurrent.futures,atexit,base64
class Reader:
 def read(self,a,n):
  if n<0 or n>16*1024*1024:raise ValueError('Bounded read exceeded')
  out=bytearray()
  while n:
   pg=a&~4095;off=a-pg;take=min(n,4096-off)
   if pg not in self.cache:
    span=next((r for r in self.ranges if r[0]<=pg and pg+4096<=r[1] and r[2].startswith('r')),None)
    if not span:raise ValueError(f'Unmapped pointer {a:x}')
    result=subprocess.run([self.adb,'-s',self.serial,'exec-out','su','0','dd',f'if=/proc/{self.pid}/mem','bs=4096',f'skip={pg//4096}','count=1','status=none'],capture_output=True,timeout=15)
    if result.returncode or len(result.stdout)!=4096:raise ValueError('Read failed or short')
    self.cache[pg]=result.stdout;self.calls+=1
   out+=self.cache[pg][off:off+take];a+=take;n-=take
  return bytes(out)
 def q(self,a):return struct.unpack('<Q',self.read(a,8))[0]
 def typ(self,a):
  p=self.q(a+8)
  if p not in self.types:self.types[p]=self.read(self.q(p+24),80).split(b'\0')[0].decode('ascii','replace')
  return self.types[p]
 def string(self,a):
  if self.typ(a)!='str':return None
  h=self.read(a,48);n=struct.unpack_from('<q',h,16)[0];state=struct.unpack_from('<I',h,32)[0];kind=(state>>2)&7;compact=(state>>5)&1;ascii_=(state>>6)&1
  if not 0<=n<=100000 or kind not in [1,2,4]:raise ValueError('Invalid string')
  p=a+(56 if ascii_ else 80) if compact else self.q(a+88)
  return self.read(p,n*kind).decode({1:'latin1',2:'utf-16le',4:'utf-32le'}[kind])
 def dict_entries(self,a):
  if self.typ(a)!='dict':raise ValueError('Not a dict: '+self.typ(a))
  h=self.read(a,48);used,ver,keys,values=struct.unpack_from('<4Q',h,16);kh=self.read(keys,32);logsize,logbytes,kind=kh[8:11];ne=struct.unpack_from('<q',kh,24)[0]
  if not 0<=ne<=300000 or logbytes>25 or kind>2:raise ValueError('Invalid dictionary')
  start=keys+32+(1<<logbytes);stride=24 if kind==0 else 16;data=self.read(start,ne*stride);vv=self.read(values,ne*8) if values else None;result=[]
  for i in range(ne):
   key,val=struct.unpack_from('<QQ',data,i*stride+(8 if kind==0 else 0))
   if values:val=struct.unpack_from('<Q',vv,i*8)[0]
   if key and val:result.append((key,val))
  if len(result)!=used:raise ValueError('Dictionary changed or inconsistent layout')
  return result
 def modules(self):
  rt=self.base+0x75f1d08;t=self.q(rt+0x240);interp=self.q(t+16);assert self.q(interp+40)==rt
  return self.q(interp+0x378)

class FastReader(Reader):
 def close(self):
  proc=getattr(self,'channel',None)
  if proc:
   try:proc.stdin.write(b'exit\n');proc.stdin.flush();proc.wait(timeout=2)
   except Exception:proc.kill()
   self.channel=None
  executor=getattr(self,'executor',None)
  if executor:executor.shutdown(wait=False,cancel_futures=True)
 def block(self,start,count):
  if not getattr(self,'channel',None):
   self.channel=subprocess.Popen([self.adb,'-s',self.serial,'shell','-T','su','0','sh'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
   self.executor=concurrent.futures.ThreadPoolExecutor(max_workers=1);atexit.register(self.close)
  n=count*4096
  cmd=f"dd if=/proc/{self.pid}/mem bs=4096 skip={start//4096} count={count} status=none 2>/dev/null | base64; printf 'READ_END\\n'\n"
  self.channel.stdin.write(cmd.encode('ascii'));self.channel.stdin.flush()
  def receive():
   lines=[];total=0
   while True:
    line=self.channel.stdout.readline()
    if not line:raise ValueError('Channel ended')
    line=line.strip()
    if line==b'READ_END':break
    total+=len(line)
    if total>n*2+4096:raise ValueError('Oversized channel response')
    lines.append(line)
   return base64.b64decode(b''.join(lines),validate=True)
  future=self.executor.submit(receive)
  try:data=future.result(timeout=15)
  except Exception:self.close();raise
  if len(data)!=n:raise ValueError('Read failed or short')
  return data

 def read(self,a,n):
  if n<0 or n>16*1024*1024:raise ValueError('Bounded read exceeded')
  out=bytearray()
  while n:
   pg=a&~4095;off=a-pg;take=min(n,4096-off)
   if pg not in self.cache:
    span=next((r for r in self.ranges if r[0]<=pg and pg+4096<=r[1] and r[2].startswith('r')),None)
    if not span:raise ValueError(f'Unmapped pointer {a:x}')
    start=max(span[0],pg&~4095);end=min(span[1],start+4096);count=(end-start)//4096
    payload=self.block(start,count)
    for j in range(count):self.cache[start+j*4096]=payload[j*4096:(j+1)*4096]
    self.calls+=1
   out+=self.cache[pg][off:off+take];a+=take;n-=take
  return bytes(out)
 def string(self,a):
  if self.typ(a)!='str':return None
  h=self.read(a,48);n=struct.unpack_from('<q',h,16)[0];state=struct.unpack_from('<I',h,32)[0];kind=(state>>2)&7;compact=(state>>5)&1;ascii_=(state>>6)&1
  if not 0<=n<=100000 or kind not in [1,2,4]:raise ValueError('Invalid string')
  p=a+(56 if ascii_ else 80) if compact else self.q(a+88)
  return self.read(p,n*kind).decode({1:'latin1',2:'utf-16le',4:'utf-32le'}[kind])
 def scalar(self,a):
  t=self.typ(a)
  if t=='str':return self.string(a)
  if t=='NoneType':return None
  if t in ['int','bool']:
   n=struct.unpack('<q',self.read(a+16,8))[0]
   if abs(n)>100:raise ValueError('Unreasonable integer')
   raw=self.read(a+24,abs(n)*4);v=sum(struct.unpack_from('<I',raw,i*4)[0]<<(30*i) for i in range(abs(n)))
   return bool(v) if t=='bool' else (-v if n<0 else v)
  if t=='float':return struct.unpack('<d',self.read(a+16,8))[0]
  return {'type':t,'address':hex(a)}
 def describe(self,a):
  t=self.typ(a);d={'type':t,'address':hex(a)}
  if t in ['dict','list','tuple','str','bytes']:d['size']=self.q(a+16)
  elif t in ['int','bool','float','NoneType']:d['value']=self.scalar(a)
  return d
 def value(self,a,depth=0,seen=None):
  if seen is None:seen=set()
  t=self.typ(a)
  if t not in ['dict','list','tuple']:return self.scalar(a)
  if depth>10 or a in seen:return self.describe(a)
  seen=set(seen);seen.add(a)
  if t=='dict':
   es=self.dict_entries(a)
   if len(es)>500:return self.describe(a)
   return {str(self.scalar(k)):self.value(v,depth+1,seen) for k,v in es}
  n=self.q(a+16)
  if n>1000:return self.describe(a)
  p=self.q(a+24) if t=='list' else a+24
  return [self.value(self.q(p+i*8),depth+1,seen) for i in range(n)]

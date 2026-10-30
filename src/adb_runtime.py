"""Private ADB: a stable copy outside the PyInstaller temp folder and a server port of its own.

A server started from _MEIxxxx outlives the window and keeps that temp folder from being deleted;
port 5037 is shared with MuMu and any other adb on the machine. Every open window registers itself,
so closing one window does not stop the server another window is still using.
"""
import os,sys,shutil,subprocess,hashlib
from pathlib import Path
from resources import BASE
PORT='5041'
FILES=('adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll')
LOCAL=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'FoundryTracker'/'adb'
INSTANCES=LOCAL.parent/'instances'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def same(a,b):return b.exists() and a.stat().st_size==b.stat().st_size and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def prepare():
 """Return the adb.exe to use. Every adb call made by this process, memory_reader's included, inherits the port."""
 os.environ['ANDROID_ADB_SERVER_PORT']=PORT;register()
 source=BASE/'adb'
 if not hasattr(sys,'_MEIPASS'):return source/'adb.exe'
 try:
  LOCAL.mkdir(parents=True,exist_ok=True)
  stale=[name for name in FILES if not same(source/name,LOCAL/name)]
  # A server left by a crashed older version still holds its files; stop it before replacing them.
  if stale and (LOCAL/'adb.exe').exists():shutdown(LOCAL/'adb.exe')
  for name in stale:shutil.copy2(source/name,LOCAL/name)
  return LOCAL/'adb.exe'
 except OSError:return source/'adb.exe'
def register():
 """One empty file per open window: the windows that share the adb server."""
 try:INSTANCES.mkdir(parents=True,exist_ok=True);(INSTANCES/str(os.getpid())).touch()
 except OSError:pass
def alive(pid):
 """Whether a process with this id is running; it only asks Windows, it never touches the process."""
 try:
  import ctypes
  kernel=ctypes.windll.kernel32;handle=kernel.OpenProcess(0x1000,False,pid)
  if not handle:return False
  code=ctypes.c_ulong();ok=kernel.GetExitCodeProcess(handle,ctypes.byref(code));kernel.CloseHandle(handle)
  return bool(ok) and code.value==259
 except (AttributeError,OSError):return False
def release(adb):
 """Called when a window closes: stop the server unless another Foundry Tracker window still uses it."""
 others=False
 try:
  for entry in INSTANCES.iterdir():
   if entry.name!=str(os.getpid()) and entry.name.isdigit() and alive(int(entry.name)):others=True
   else:entry.unlink(missing_ok=True)
 except OSError:pass
 if not others:shutdown(adb)
def shutdown(adb):
 """Stop this app's own server (port 5041)."""
 try:subprocess.run([str(adb),'kill-server'],capture_output=True,timeout=5,creationflags=FLAGS)
 except (OSError,subprocess.TimeoutExpired):pass

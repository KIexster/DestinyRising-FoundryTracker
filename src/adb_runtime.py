"""Private ADB: a stable copy outside the PyInstaller temp folder and a server port of its own.

A server started from _MEIxxxx outlives the window and keeps that temp folder from being deleted;
port 5037 is shared with MuMu and any other adb on the machine.
"""
import os,sys,shutil,subprocess,hashlib
from pathlib import Path
from resources import BASE
PORT='5041'
FILES=('adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll')
LOCAL=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'FoundryTracker'/'adb'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def same(a,b):return b.exists() and a.stat().st_size==b.stat().st_size and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def prepare():
 """Return the adb.exe to use. Every adb call made by this process, memory_reader's included, inherits the port."""
 os.environ['ANDROID_ADB_SERVER_PORT']=PORT
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
def shutdown(adb):
 """Stop this app's own server (port 5041) so nothing keeps running after the window closes."""
 try:subprocess.run([str(adb),'kill-server'],capture_output=True,timeout=5,creationflags=FLAGS)
 except (OSError,subprocess.TimeoutExpired):pass

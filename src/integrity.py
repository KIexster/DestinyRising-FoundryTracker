"""Pinned bundled ADB identity. Update only when reviewing a new platform-tools release."""
import hashlib
from pathlib import Path
ADB_SHA256={'adb.exe': 'b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f', 'AdbWinApi.dll': 'c1d653030b4bde65d3e07e4d0b0979e17be56df1436cdd15528630f27808050d', 'AdbWinUsbApi.dll': '0710e894d9b40f71a670c13c694079d564c92c1279da382cfe4850983aaebe1b'}
def verify_adb(directory):
 directory=Path(directory)
 for name,expected in ADB_SHA256.items():
  file=directory/name
  if file.is_symlink() or not file.is_file() or file.stat().st_size>32*1024*1024:
   raise RuntimeError('ADB integrity check failed: '+name)
  with file.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
  if actual!=expected:raise RuntimeError('ADB integrity check failed: '+name)
 return directory/'adb.exe'

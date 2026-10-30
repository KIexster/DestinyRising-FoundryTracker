"""Every command Foundry Tracker may send through ADB, as a closed list. Anything else is refused before it runs, so no
code path, edited catalog or engine.json can make the app write to the game, install something or run other commands.
The README lists the same commands under "What runs on the emulator"."""
import re
N=r'[0-9]+'
PACKAGE=r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+'
READ=rf'dd if=/proc/{N}/mem bs=4096 skip={N} count={N} status=none'
# On the emulator: who am I (root check), the game's pid, its memory map and reads of its memory.
SHELL=[r'id',rf'cat /proc/{N}/maps',rf'pidof {PACKAGE}',rf'echo B:\$\(cat /proc/sys/kernel/random/boot_id\) P:\$\(pidof {PACKAGE}\)',READ]
# On the PC: the local ADB server only.
HOST=[r'devices',r'connect 127\.0\.0\.1:16384',r'kill-server']
COMMAND=re.compile('|'.join(HOST+[rf'(?:shell|exec-out)(?: su 0)? (?:{"|".join(SHELL)})',r'shell -T su 0 sh']))
CHANNEL=re.compile(rf'{READ}(?:;{READ})*')
class Blocked(RuntimeError):pass
def check(args):
 """args: an adb command line without the adb path. '-s <serial>' only picks the emulator."""
 line=' '.join(args[2:] if args[:1]==['-s'] else args)
 if not COMMAND.fullmatch(line):raise Blocked(f'Comando bloqueado por seguridad (Foundry Tracker solo lee): {line}')
 return args
def check_channel(cmd):
 """What the root shell opened with 'shell -T su 0 sh' may run: memory reads, nothing else."""
 if not CHANNEL.fullmatch(cmd):raise Blocked(f'Comando bloqueado por seguridad (Foundry Tracker solo lee): {cmd[:120]}')
 return cmd

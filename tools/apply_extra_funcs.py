#!/usr/bin/env python3
"""Sync syms/extra_funcs.txt into syms/dump.toml (we keep no splat tree, so dump.toml is
edited in place). Also converts fix_backbranches.py MISSING lines on stdin into entries,
sized to the end of the containing function (recomp_loop.py's convention)."""
import re, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'tools')
from recomp_loop import add_func_to_dump, load_funcs   # noqa (module runs nothing at import? see guard)
funcs = load_funcs()
have = {(sec, vram) for sec, name, vram, size in funcs}
dump = open('syms/dump.toml').read()
def add(sec, vram, size):
    if (sec, vram) in have: return False
    add_func_to_dump(sec, f'func_{vram:08X}', vram, size)
    have.add((sec, vram)); return True
n = 0
for line in open('syms/extra_funcs.txt'):
    m = re.match(r'(\w+) func_[0-9A-Fa-f]+ (0x[0-9A-Fa-f]+) (0x[0-9A-Fa-f]+)', line)
    if m and add(m.group(1), int(m.group(2), 16), int(m.group(3), 16)): n += 1
for line in sys.stdin if not sys.stdin.isatty() else []:
    m = re.search(r'Add "(\w+) func_[0-9A-Fa-f]+ (0x[0-9A-Fa-f]+) <size>"', line)
    if not m: continue
    sec, target = m.group(1), int(m.group(2), 16)
    host = [(v, s) for sc, nm, v, s in funcs if sc == sec and v < target < v + s]
    if not host:  # the branch crosses sections: file the entry under the section that owns the target
        host = [(v, s) for sc, nm, v, s in funcs if v < target < v + s and sc != 'entry']
        sec = next((sc for sc, nm, v, s in funcs if v < target < v + s and sc != 'entry'), sec)
    if host:
        v, s = max(host); size = v + s - target
    else:
        nxt = [v for sc, nm, v, s in funcs if sc == sec and v > target]
        if not nxt: print('no host for', line.strip()); continue
        size = min(nxt) - target
    if add(sec, target, size):
        open('syms/extra_funcs.txt', 'a').write(f'{sec} func_{target:08X} 0x{target:08X} 0x{size:X}\n'); n += 1
print(f'{n} entries added to syms/dump.toml')

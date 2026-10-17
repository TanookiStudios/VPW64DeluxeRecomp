#!/usr/bin/env python3
"""A function cannot end on a jump or branch: its delay slot belongs to it. Where the hack
rewrote a retail function in place and grew it by one instruction, the retail map's size cuts
the final delay slot off (e.g. the `move $t7,$zero` after `jr $ra` in func_80031FE8). Grow
such functions by one word. Idempotent."""
import re, struct
d = open('vpw2.z64', 'rb').read()
W = lambda o: struct.unpack_from('>I', d, o)[0]
t = open('syms/dump.toml').read()
secs = [(m.group(1), int(m.group(2), 16), int(m.group(3), 16)) for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)', t)]
def is_jump(w):
    op = w >> 26
    return op in (1, 2, 3, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0 and (w & 0x3F) in (8, 9)) or (op == 0x11 and (w >> 21) & 0x1F == 8)
sec = None; rom = vram = 0; out = []; grown = 0
for line in t.split('\n'):
    m = re.match(r'name = "([^"]+)"$', line)
    if m:
        sec = m.group(1); rom, vram = next((r, v) for n, r, v in secs if n == sec)
    f = re.search(r'\{ name = "(\w+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+) \}', line)
    if f and sec not in ('hack_far', 'hack_match'):
        v, s = int(f.group(2), 16), int(f.group(3), 16)
        last = W(rom + (v + s - 4 - vram))
        if is_jump(last):
            line = line.replace(f'size = {f.group(3)}', f'size = 0x{s + 4:X}'); grown += 1
            print(f'  {f.group(1)} ({sec}): size 0x{s:X} -> 0x{s+4:X} (ended on a jump)')
    out.append(line)
open('syms/dump.toml', 'w').write('\n'.join(out))
print(f'{grown} functions grown to include their final delay slot')

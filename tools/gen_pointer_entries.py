#!/usr/bin/env python3
"""The hack's own code builds retail code addresses with lui/ori (or lui/addiu) and later jumps
to them through registers or tables. Some land in the MIDDLE of retail functions. Scan the hack's
code (far block, main-segment hack code, trampolines, overlay hack code) for such constants and
add them as mid-entries sized to the function's end. Idempotent."""
import re, struct, sys
sys.path.insert(0, 'tools')
from recomp_loop import add_func_to_dump
d = open('vpw2.z64', 'rb').read()
W = lambda o: struct.unpack_from('>I', d, o)[0]
t = open('syms/dump.toml').read()
secs = []
for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)\nsize = (0x[0-9A-Fa-f]+)(.*?)(?=\n\[\[section\]\]|\Z)', t, re.S):
    name, rom, vram, size, body = m.groups()
    funcs = sorted((int(a, 16), int(b, 16)) for a, b in re.findall(r'vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', body))
    secs.append((name, int(rom, 16), int(vram, 16), int(size, 16), funcs))
def owner(v):
    for n, r, vr, s, fs in secs:
        if n.startswith('hack_') or n == 'entry': continue
        if vr <= v < vr + s:
            for fv, fsz in fs:
                if fv < v < fv + fsz: return n, fv, fsz
    return None
existing = set(re.findall(r'vram = (0x[0-9A-Fa-f]+), size', t))
added = 0
for n, r, vr, s, fs in secs:
    if not n.startswith('hack_'): continue
    for fv, fsz in fs:
        for off in range(0, fsz - 4, 4):
            w = W(r + (fv + off - vr))
            if (w >> 26) != 0xF or not (0x8000 <= (w & 0xFFFF) <= 0x8018): continue
            rt = (w >> 16) & 0x1F
            for k in (1, 2, 3):
                w2 = W(r + (fv + off + 4 * k - vr)); op = w2 >> 26
                if ((w2 >> 21) & 0x1F) == rt and ((w2 >> 16) & 0x1F) == rt and op in (9, 0xD):
                    imm = w2 & 0xFFFF
                    v = (((w & 0xFFFF) << 16) + (imm - 0x10000 if (op == 9 and imm & 0x8000) else imm)) & 0xFFFFFFFF
                    own = owner(v)
                    if own and not (v & 3) and f'0x{v:08X}' not in existing:
                        on, ofv, ofsz = own
                        add_func_to_dump(on, f'func_{v:08X}', v, ofv + ofsz - v)
                        open('syms/extra_funcs.txt', 'a').write(f'{on} func_{v:08X} 0x{v:08X} 0x{ofv + ofsz - v:X}\n')
                        existing.add(f'0x{v:08X}'); added += 1
                    break
print(f'{added} mid-entries added from constants in hack code')

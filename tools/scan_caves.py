#!/usr/bin/env python3
"""List jump/branch targets in the ROM's code that land outside every function in
syms/dump.toml (ROM-hack code caves), and non-empty gaps between functions."""
import re, struct
d = open('vpw2.z64', 'rb').read()
secs = []
for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)\nsize = (0x[0-9A-Fa-f]+)(.*?)(?=\n\[\[section\]\]|\Z)', open('syms/dump.toml').read(), re.S):
    name, rom, vram, size, body = m.groups()
    funcs = [(int(a, 16), int(b, 16)) for a, b in re.findall(r'vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', body)]
    secs.append((name, int(rom, 16), int(vram, 16), int(size, 16), sorted(funcs)))
def owner(v):
    for n, r, vr, s, fs in secs:
        if vr <= v < vr + s:
            for fv, fsz in fs:
                if fv <= v < fv + fsz: return n, fv
            return n, None
    return None, None
out = {}
for n, r, vr, s, fs in secs:
    for fv, fsz in fs:
        for off in range(0, fsz, 4):
            pc = fv + off; w = struct.unpack_from('>I', d, r + (pc - vr))[0]
            op = w >> 26; tgt = None
            if op in (2, 3): tgt = (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
            elif op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0x11 and (w >> 21) & 0x1F == 8):
                tgt = pc + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2)
            if tgt is None: continue
            sn, fo = owner(tgt)
            if fo is None:
                out.setdefault((sn, tgt), []).append((n, fv, pc))
for (sn, tgt), srcs in sorted(out.items(), key=lambda x: (x[0][0] or '', x[0][1])):
    print(f'{sn or "OUTSIDE":10} target 0x{tgt:08X} <- ' + ', '.join(f'{fn} func_{fv:08X}+0x{pc-fv:X}' for fn, fv, pc in srcs[:4]))
print('-- non-empty gaps between functions')
for n, r, vr, s, fs in secs:
    end = vr
    for fv, fsz in fs + [(vr + s, 0)]:
        if fv > end:
            blob = d[r + (end - vr): r + (fv - vr)]
            if any(blob): print(f'{n}: gap 0x{end:08X}-0x{fv:08X} ({fv-end} bytes)')
        end = max(end, fv + fsz)

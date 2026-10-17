#!/usr/bin/env python3
"""Discover the ROM hack's CPU functions in the main segment's data area
(vram 0x80039620..0x8004B340, loaded in place by IPL3), by recursive descent from every
jump/branch into that window made by already-mapped code. Prints dump.toml function lines."""
import re, struct, sys
d = open('vpw2.z64', 'rb').read()
WIN_LO, WIN_HI = 0x80039620, 0x8004B340
R = lambda v: v - 0x7FFFF400
W = lambda v: struct.unpack_from('>I', d, R(v))[0]
secs = []
for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)\nsize = (0x[0-9A-Fa-f]+)(.*?)(?=\n\[\[section\]\]|\Z)', open('syms/dump.toml').read(), re.S):
    name, rom, vram, size, body = m.groups()
    funcs = [(int(a, 16), int(b, 16)) for a, b in re.findall(r'vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', body)]
    secs.append((name, int(rom, 16), int(vram, 16), int(size, 16), funcs))
def targets_of(w, pc):
    op = w >> 26
    if op in (2, 3): return (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2), op == 3
    if op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0x11 and (w >> 21) & 0x1F == 8):
        return pc + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2), False
    return None, False
stubbed = set(re.findall(r'"(func_[0-9A-F]+)"', re.search(r'stubs = \[(.*?)\]', open('vpw2.toml').read(), re.S).group(1)))
seeds = set(); by_src = {}
for n, r, vr, s, fs in secs:
    if n.startswith('hack'): continue
    for fv, fsz in fs:
        if f'func_{fv:08X}' in stubbed: continue
        for off in range(0, fsz, 4):
            pc = fv + off; t, _ = targets_of(struct.unpack_from('>I', d, r + (pc - vr))[0], pc)
            if t is not None and WIN_LO <= t < WIN_HI: seeds.add(t); by_src.setdefault(fv, []).append(t)
funcs = {}
todo = sorted(seeds)
while todo:
    entry = todo.pop()
    if entry in funcs: continue
    pc = entry; maxfwd = entry; end = None
    while pc < WIN_HI:
        w = W(pc); t, is_call = targets_of(w, pc)
        if t is not None:
            if is_call:
                if WIN_LO <= t < WIN_HI and t not in funcs: todo.append(t)
            elif (w >> 26) == 2:  # j
                if WIN_LO <= t < WIN_HI and not (entry <= t <= maxfwd + 0x400) and t not in funcs: todo.append(t)
                if t > maxfwd and entry <= t < entry + 0x2000: maxfwd = t
            else:
                if t > maxfwd and t < entry + 0x4000: maxfwd = t
        uncond = (w == 0x03E00008) or ((w & 0xFC1F07FF) == 0x00000008) or ((w >> 26) == 2) or (w & 0xFFFF0000) == 0x10000000  # jr ra / jr rX / j / b
        if uncond and pc >= maxfwd:
            end = pc + 8; break
        pc += 4
    funcs[entry] = (end or pc) - entry
for v in sorted(funcs):
    print(f'    {{ name = "func_{v:08X}", vram = 0x{v:08X}, size = 0x{funcs[v]:X} }},')
print(f'# {len(funcs)} functions, seeds {len(seeds)}', file=sys.stderr)
for fv, ts in sorted(by_src.items(), key=lambda x: -len(x[1]))[:12]: print(f'#   seeds from func_{fv:08X}: {len(ts)} e.g. {[hex(t) for t in ts[:4]]}', file=sys.stderr)

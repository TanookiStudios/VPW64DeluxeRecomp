#!/usr/bin/env python3
"""The hack hides code in the DATA area of each overlay (as it does in the main segment).
For every overlay, run a recursive descent from every jump that lands in its data area and
write a `hack_<overlay>` section (same rom image as the overlay, so the runtime loads and
unloads it with the overlay). Idempotent."""
import re, struct, sys
d = open('vpw2.z64', 'rb').read()
W = lambda rom: struct.unpack_from('>I', d, rom)[0]
t = open('syms/dump.toml').read()
secs = []
for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)\nsize = (0x[0-9A-Fa-f]+)(.*?)(?=\n\[\[section\]\]|\Z)', t, re.S):
    name, rom, vram, size, body = m.groups()
    funcs = [(int(a, 16), int(b, 16)) for a, b in re.findall(r'vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', body)]
    secs.append((name, int(rom, 16), int(vram, 16), int(size, 16), sorted(funcs)))
# overlay data areas (rom), from disasm/vpw2.yaml: code end -> next segment start
DATA = {'ovl_a': (0x695E0, 0x71A90), 'ovl_b': (0x7C710, 0x84710), 'ovl_c': (0xD5840, 0xE11A0), 'ovl_d': (0x14BCA0, 0x152DF0)}
stubbed = set(re.findall(r'"(func_[0-9A-F]+)"', re.search(r'stubs = \[(.*?)\]', open('vpw2.toml').read(), re.S).group(1)))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS64, CS_MODE_BIG_ENDIAN
md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_BIG_ENDIAN)
def R0(v, orom, ovram): return orom + (v - ovram)
def decodable(rom):
    w = d[rom:rom + 4]
    return w != b'\0\0\0\0' and next(md.disasm(w, 0), None) is not None
def sane_target(w, pc):
    op = w >> 26
    if op in (2, 3): return 0x80000000 <= (0x80000000 | ((w & 0x3FFFFFF) << 2)) < 0x80400000
    if op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17):
        t = pc + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2)
        return 0x80000000 <= t < 0x80400000
    return True
def looks_like_code(rom):
    """first word decodes, and a jr/j/jal shows up within the next 0x400 bytes"""
    if not decodable(rom): return False
    for o in range(rom, rom + 0x400, 4):
        w = W(o)
        if w == 0x03E00008 or (w >> 26) in (2, 3): return True
    return False
def targets_of(w, pc):
    op = w >> 26
    if op in (2, 3): return (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2), op == 3
    if op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0x11 and (w >> 21) & 0x1F == 8):
        return pc + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2), False
    return None, False
out_sections = []
for ovl, (dr0, dr1) in DATA.items():
    orom, ovram = next((r, v) for n, r, v, s, f in secs if n == ovl)
    lo, hi = ovram + (dr0 - orom), ovram + (dr1 - orom)
    # seeds: jumps into [lo,hi) from this overlay's own code and from main/hack code
    # Only code that can be in memory at the same time as this overlay may jump into its data
    # area (ovl_a/ovl_d share one slot, ovl_b/ovl_c the other). Across overlays only j/jal count.
    COLOAD = {'ovl_a': {'main_1050', 'ovl_a', 'ovl_b', 'ovl_c'}, 'ovl_b': {'main_1050', 'ovl_a', 'ovl_b'},
              'ovl_c': {'main_1050', 'ovl_a', 'ovl_c'}, 'ovl_d': {'main_1050', 'ovl_d'}}
    seeds = set()
    for n, r, vr, s, fs in secs:
        if n not in COLOAD[ovl]: continue
        for fv, fsz in fs:
            if f'func_{fv:08X}' in stubbed: continue
            for off in range(0, fsz, 4):
                w = W(r + (pc := fv + off) - vr); tg, _ = targets_of(w, pc)
                if tg is None or not (lo <= tg < hi): continue
                if (w >> 26) not in (2, 3): continue          # only j/jal: branch targets in data are noise
                if not looks_like_code(R0(tg, orom, ovram)): continue
                seeds.add(tg)
    funcs = {}; todo = sorted(seeds)
    R = lambda v: orom + (v - ovram)
    while todo:
        entry = todo.pop()
        if entry in funcs: continue
        pc = entry; maxfwd = entry; end = None
        while pc < hi:
            w = W(R(pc))
            if not decodable(R(pc)) and w != 0 or not sane_target(w, pc):
                end = pc; break                       # ran into data: the routine ends here
            tg, is_call = targets_of(w, pc)
            if tg is not None:
                if is_call:
                    if lo <= tg < hi and tg not in funcs: todo.append(tg)
                elif (w >> 26) == 2:
                    if lo <= tg < hi and not (entry <= tg <= maxfwd + 0x400) and tg not in funcs: todo.append(tg)
                    if tg > maxfwd and entry <= tg < entry + 0x2000: maxfwd = tg
                elif tg > maxfwd and tg < entry + 0x4000: maxfwd = tg
            uncond = (w == 0x03E00008) or ((w & 0xFC1F07FF) == 0x8) or ((w >> 26) == 2) or (w & 0xFFFF0000) == 0x10000000
            if uncond and pc >= maxfwd: end = pc + 8; break
            pc += 4
        if (end or pc) - entry >= 8: funcs[entry] = (end or pc) - entry
    if not funcs: print(f'{ovl}: no hack code in its data area'); continue
    lines = ''.join(f'    {{ name = "func_{v:08X}", vram = 0x{v:08X}, size = 0x{funcs[v]:X} }},\n' for v in sorted(funcs))
    out_sections.append(f'[[section]]\nname = "hack_{ovl}"\nrom = 0x{dr0:08X}\nvram = 0x{lo:08X}\nsize = 0x{dr1 - dr0:X}\n\nfunctions = [\n{lines}]\n\n')
    print(f'hack_{ovl}: {len(funcs)} functions from {len(seeds)} seeds')
# drop sections from earlier runs that this run no longer produces
produced = {re.search(r'name = "(\w+)"', sec).group(1) for sec in out_sections}
for stale in set(re.findall(r'name = "(hack_ovl_[a-d])"', t)) - produced:
    t = re.sub(r'\[\[section\]\]\nname = "%s".*?\]\n\n' % stale, '', t, flags=re.S); print('removed stale', stale)
for sec in out_sections:
    name = re.search(r'name = "(\w+)"', sec).group(1)
    if f'name = "{name}"' in t: t = re.sub(r'\[\[section\]\]\nname = "%s".*?\]\n\n' % name, sec, t, flags=re.S)
    else:
        i = t.index('[[section]]\nname = "ovl_a"'); t = t[:i] + sec + t[i:]
open('syms/dump.toml', 'w').write(t)

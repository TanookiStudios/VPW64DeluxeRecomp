#!/usr/bin/env python3
"""List every `jal` into the hack's trampoline block, follow it through the pointer slot to the
far-block routine, and classify how that routine comes back: `jr $ra` (a real call) or `j` into
retail code (an escape). Escapes must be translated as tail calls (patch jal -> j in vpw2.toml)."""
import re, struct, sys
d = open('vpw2.z64', 'rb').read()
W = lambda o: struct.unpack_from('>I', d, o)[0]
ROM, RAM, SZ = 0x2FA1704, 0x80364B30, 0x25380
P = 0x80368AF0
secs = [('main_1050', 0x1000, 0x80000400, 0x4BF40 - 0x1000), ('ovl_a', 0x4BF40, 0x800E6AF0, 0x695E0 - 0x4BF40),
        ('ovl_b', 0x71A90, 0x80119450, 0x7C710 - 0x71A90), ('ovl_c', 0x84710, 0x80119450, 0xD5840 - 0x84710),
        ('ovl_d', 0xE11A0, 0x800E6AF0, 0x14BCA0 - 0xE11A0)]
# installer tables: slot -> value (both installers write "P-0x7F00+X")
slots = {}
for a, b in [(ROM, ROM + SZ), (0x2FC6444, 0x2FC6764)]:
    for o in range(a, b - 20, 4):
        w = W(o)
        if (w >> 26) == 0x2B and ((w >> 21) & 0x1F) == 1 and any((W(o - 4 * k) >> 26) == 0xF and ((W(o - 4 * k) >> 16) & 0x1F) == 1 and (W(o - 4 * k) & 0xFFFF) == 0x8009 for k in (1, 2)):
            imm = w & 0xFFFF; slot = (0x80090000 + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
            rt = (w >> 16) & 0x1F
            for k in range(1, 6):
                wk = W(o - 4 * k)
                if (wk >> 26) == 0xF and ((wk >> 16) & 0x1F) == rt:
                    w2 = W(o - 4 * k + 4); lo = w2 & 0xFFFF if (w2 >> 26) == 0xD else 0
                    slots[slot] = P - 0x7F00 + (((wk & 0xFFFF) << 16) | lo); break
far_starts = sorted(int(v, 16) for v in re.findall(r'vram = (0x803[6-8][0-9A-F]+)', open('syms/dump.toml').read()))
def routine_exits(v):
    """exits of the far routine at v up to the next routine start: ('ra',pc) or ('j',pc,target)"""
    nxt = next((s for s in far_starts if s > v), v + 0x400)
    out = []
    for pc in range(v, nxt, 4):
        w = W(ROM + (pc - RAM))
        if w == 0x03E00008: out.append(('ra', pc))
        elif (w >> 26) == 2: out.append(('j', pc, 0x80000000 | ((w & 0x3FFFFFF) << 2)))
        elif (w & 0xFC1FFFFF) == 0x8: out.append(('jrX', pc))
    return out
hooks = []
for name, rom, vram, size in secs:
    for o in range(rom, rom + size - 4, 4):
        w = W(o)
        if (w >> 26) == 3:
            t = 0x80000000 | ((w & 0x3FFFFFF) << 2)
            if 0x8009FDD0 <= t < 0x800A00F0:
                trom = 0x2FC6444 + (t - 0x8009FDD0)
                w0, w1 = W(trom), W(trom + 4)
                if (w0 >> 26) == 0xF and (w1 >> 26) == 0x23:   # lui $at; lw $at,off($at)
                    imm = w1 & 0xFFFF; slot = (0x80090000 + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
                    far = slots.get(slot)
                    ex = routine_exits(far) if far else []
                    kinds = {e[0] for e in ex}
                    hooks.append((name, vram + (o - rom), t, slot, far, ex))
for name, pc, t, slot, far, ex in hooks:
    desc = ', '.join(f'{e[0]}@{e[1]:08X}' + (f'->{e[2]:08X}' if e[0] == 'j' else '') for e in ex)
    print(f'{name} jal@{pc:08X} -> tramp {t:08X} slot {slot:08X} -> far {far if far is None else hex(far)}: {desc}')

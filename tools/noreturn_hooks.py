#!/usr/bin/env python3
"""The hack's helper routines often end with `j <retail address>` (the address the hook's jal
would return to) instead of `jr $ra`. On hardware that is a return; N64Recomp turns the jal into
a C call whose caller then continues too, so the function tail runs twice. Every `jal` (or
slot-resolved `jalr $t9`) to such a never-returning helper becomes a plain jump via instruction
patches in vpw2.toml, so the translated flow is one straight chain of tail calls. Idempotent."""
import re, struct
d = open('vpw2.z64', 'rb').read()
W = lambda o: struct.unpack_from('>I', d, o)[0]
dump = open('syms/dump.toml').read()
secs = []
for m in re.finditer(r'\[\[section\]\]\nname = "([^"]+)"\nrom = (0x[0-9A-Fa-f]+)\nvram = (0x[0-9A-Fa-f]+)\nsize = (0x[0-9A-Fa-f]+)(.*?)(?=\n\[\[section\]\]|\Z)', dump, re.S):
    name, rom, vram, size, body = m.groups()
    funcs = [(n, int(a, 16), int(b, 16)) for n, a, b in re.findall(r'name = "(\w+)", vram = (0x[0-9A-Fa-f]+), size = (0x[0-9A-Fa-f]+)', body)]
    secs.append((name, int(rom, 16), int(vram, 16), int(size, 16), funcs))
HACK = {'hack_main', 'hack_far', 'hack_match', 'hack_tramp', 'entry'}
def rom_of(v):
    for n, r, vr, s, fs in secs:
        if vr <= v < vr + s and n != 'ovl_d' and not (n == 'ovl_c' and v < 0x80119450 + 0x51130 and any(x == 'ovl_b' for x, *_ in secs) and False):
            return r + (v - vr)
    return None
# slot table (far-block installers): slot -> far routine
P = 0x80368AF0; ROM, RAM = 0x2FA1704, 0x80364B30
slots = {}
for a, b in [(ROM, ROM + 0x25380), (0x2FC6444, 0x2FC6764)]:
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
# hack functions: exits
hack_funcs = {}
for n, r, vr, s, fs in secs:
    if n not in HACK: continue
    for fname, fv, fsz in fs:
        exits = []; last_uncond = False
        for pc in range(fv, fv + fsz, 4):
            w = W(r + (pc - vr))
            if w == 0x03E00008: exits.append(('ret', pc))
            elif (w & 0xFC1FFFFF) == 0x8 or (w & 0xFC00003F) == 0x9: exits.append(('jrX', pc))
            elif (w >> 26) == 2: exits.append(('j', 0x80000000 | ((w & 0x3FFFFFF) << 2)))
        tail = W(r + (fv + fsz - 8 - vr)) if fsz >= 8 else 0
        falls = not (tail == 0x03E00008 or (tail & 0xFC1F07FF) == 0x8 or (tail >> 26) == 2 or (tail & 0xFFFF0000) == 0x10000000)
        hack_funcs[fv] = (fname, fsz, exits, falls, n)
# A `j` to the START of a real function is a tail call that still returns to the hook's caller
# (fine as translated). Only a `j` into the MIDDLE of retail code is a "continuation" that the
# caller's C must not follow. Real starts: the retail map (syms/retail_dump.toml) plus hack code.
real_starts = {int(v, 16) for v in re.findall(r'vram = (0x[0-9A-Fa-f]+), size', open('syms/retail_dump.toml').read())} | set(hack_funcs)
def is_noreturn(fv, seen=()):
    if fv in seen: return False
    e = hack_funcs.get(fv)
    if e is None: return False
    fname, fsz, exits, falls, sec = e
    if falls or any(k in ('ret', 'jrX') for k, *_ in exits) or not exits: return False
    for k, t in exits:
        if fv <= t < fv + fsz: return False
        if t in hack_funcs:
            if not is_noreturn(t, seen + (fv,)): return False
        elif t in real_starts: return False
    return True
noreturn = {fv for fv in hack_funcs if is_noreturn(fv)}
def final_targets(fv, seen=()):
    """The retail addresses a never-returning helper finally jumps to (through other hack helpers)."""
    out = set()
    for k, t in hack_funcs[fv][2]:
        if t in hack_funcs and t not in seen: out |= final_targets(t, seen + (fv,))
        else: out.add(t)
    return out
# Only a helper that jumps to the call site's own return point (jal pc + 8) "returns by jump".
# One that jumps into the body of a DIFFERENT function is calling the original code, whose
# `jr $ra` comes back to the hook (0x8003C500 -> 0x8003C588 -> 0x80009F4C): leave that jal alone.
def returns_by_jump(t, pc): return t in noreturn and final_targets(t) == {pc + 8}
# every jal / slot-jalr to a noreturn function, in all mapped code
patches = []
for n, r, vr, s, fs in secs:
    for fname, fv, fsz in fs:
        for pc in range(fv, fv + fsz, 4):
            w = W(r + (pc - vr))
            if (w >> 26) == 3:
                t = 0x80000000 | ((w & 0x3FFFFFF) << 2)
                if returns_by_jump(t, pc): patches.append((fname, pc, 0x08000000 | (w & 0x3FFFFFF), f'jal->j {t:08X} (helper never returns)'))
            elif (w & 0xFC00003F) == 0x9 and ((w >> 21) & 0x1F) == 25:   # jalr $t9
                w1, w2 = W(r + (pc - 8 - vr)), W(r + (pc - 4 - vr))
                if (w1 >> 26) == 0xF and (w2 >> 26) == 0x23 and ((w2 >> 21) & 0x1F) == 25:
                    imm = w2 & 0xFFFF; slot = (((w1 & 0xFFFF) << 16) + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
                    t = slots.get(slot)
                    if t is not None and returns_by_jump(t, pc): patches.append((fname, pc, 0x03200008, f'jalr->jr $t9 (slot {slot:08X} -> {t:08X} never returns)'))
toml = re.sub(r'\n\[\[patches\.instruction\]\]\nfunc = "\w+"\nvram = 0x[0-9A-F]+\nvalue = 0x[0-9A-F]+  # \[noreturn_hooks\][^\n]*\n', '', open('vpw2.toml').read())
added = 0
for fname, pc, val, why in patches:
    if f'func = "{fname}"\nvram = 0x{pc:08X}\n' in toml: continue
    toml += f'\n[[patches.instruction]]\nfunc = "{fname}"\nvram = 0x{pc:08X}\nvalue = 0x{val:08X}  # [noreturn_hooks] {why}\n'; added += 1
open('vpw2.toml', 'w').write(toml)
print(f'{len(noreturn)} never-returning hack helpers; {len(patches)} call sites; {added} patches added')
for fv in sorted(noreturn)[:12]: print('  noreturn', hack_funcs[fv][0], 'exits', [(k, hex(t)) for k, t in hack_funcs[fv][2]])

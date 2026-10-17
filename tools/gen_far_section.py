#!/usr/bin/env python3
"""Write the hack_far section (the hack's code block, rom 0x2FA1704 -> ram 0x80364B30,
0x25380 bytes) into syms/dump.toml: one function per run of decodable instructions (data
tables, strings and long zero runs are left out), plus every computed-jump target from
tools/find_far_funcs.py as a mid-entry. Branches between runs are resolved by the recompile
loop's mid-entry injection. Idempotent."""
import re, struct, subprocess, sys
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS64, CS_MODE_BIG_ENDIAN
NAME, ROM, RAM, SZ = 'hack_far', 0x2FA1704, 0x80364B30, 0x25380
if len(sys.argv) == 5:   # another CPU-copied code block: gen_far_section.py <name> <rom> <ram> <size>
    NAME = sys.argv[1]; ROM, RAM, SZ = (int(x, 16) for x in sys.argv[2:5])
md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_BIG_ENDIAN)
d = open('vpw2.z64', 'rb').read()
words = [(d[o:o+4], o) for o in range(ROM, ROM + SZ, 4)]
def bogus_jump(w, pc):
    """j/jal whose target lies outside RDRAM, or a branch that leaves the block: a data word."""
    v = int.from_bytes(w, 'big'); op = v >> 26
    if op in (2, 3): return not (0x80000000 <= (0x80000000 | ((v & 0x3FFFFFF) << 2)) < 0x80400000)
    if op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17):
        t = pc + 4 + (struct.unpack('>h', w[2:])[0] << 2)
        return not (RAM <= t < RAM + SZ)
    return False
ok = [w == b'\0\0\0\0' or (next(md.disasm(w, 0), None) is not None and not bogus_jump(w, RAM + o - ROM)) for w, o in words]
zero = [w == b'\0\0\0\0' for w, _ in words]
def is_flow(w):
    op = int.from_bytes(w, 'big') >> 26; f = int.from_bytes(w, 'big') & 0x3F
    return op in (1, 2, 3, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0 and f in (8, 9))
# break runs at undecodable words and at 16+ consecutive zero words
runs = []; s = None; zrun = 0
for i, v in enumerate(ok):
    zrun = zrun + 1 if zero[i] else 0
    if v and s is None and not zero[i]: s = i
    if (not v or zrun >= 16) and s is not None:
        e = i - (zrun - 1 if zrun >= 16 else 0)
        # a run counts as code only if it is at least 8 words and contains a jump or branch
        if e - s >= 8 and any(is_flow(w) for w, _ in words[s:e]): runs.append((s, e))
        s = None
if s is not None and len(ok) - s >= 8: runs.append((s, len(ok)))
funcs = {}
for a, b in runs: funcs[RAM + 4 * a] = 4 * (b - a)
seeds = '' if NAME != 'hack_far' else subprocess.run([sys.executable, '-I', 'tools/find_far_funcs.py', hex(ROM), hex(RAM), hex(SZ)], capture_output=True, text=True).stdout
for v in re.findall(r'vram = (0x[0-9A-F]+)', seeds):
    v = int(v, 16)
    run = next(((a, b) for a, b in runs if RAM + 4 * a <= v < RAM + 4 * b), None)
    if run and v not in funcs: funcs[v] = RAM + 4 * run[1] - v
# Computed jumps can land on any routine start the hack never spells out as a constant we can
# follow. Cover them: every instruction after an unconditional jump's delay slot, and every
# instruction after two or more nops, inside a code run becomes a mid-entry (sized to the run end).
for a, b in runs:
    i = a
    while i < b - 1:
        v = int.from_bytes(words[i][0], 'big'); op = v >> 26
        uncond = v == 0x03E00008 or (v & 0xFC1F07FF) == 0x8 or op == 2 or (v & 0xFFFF0000) == 0x10000000
        nops = v == 0
        prologue = (v & 0xFFFF8000) == 0x27BD8000   # addiu $sp,$sp,-N
        if uncond:
            nxt = i + 2
        elif nops:
            nxt = i + 1
            while nxt < b and int.from_bytes(words[nxt][0], 'big') == 0: nxt += 1
        elif prologue:
            nxt = i
        else:
            i += 1; continue
        if nxt < b and int.from_bytes(words[nxt][0], 'big') != 0:
            vr = RAM + 4 * nxt
            if vr not in funcs: funcs[vr] = RAM + 4 * b - vr
        i = max(nxt, i + 1)
# Make the section's functions non-overlapping: each routine runs from its start to the next
# start inside the same run (overlapping entries made N64Recomp misplace branch labels here).
def after_call(v):
    """True when v sits right after a jal/jalr/bal and its delay slot: a return point, not a routine."""
    i = (v - RAM) // 4 - 2
    if i < 0: return False
    w = int.from_bytes(words[i][0], 'big'); op = w >> 26
    return op == 3 or (op == 0 and (w & 0x3F) == 9) or (op == 1 and ((w >> 16) & 0x1F) in (0x10, 0x11))
for v in [v for v in funcs if after_call(v)]:
    del funcs[v]
starts = sorted(funcs)
for a, b in runs:
    inrun = [v for v in starts if RAM + 4 * a <= v < RAM + 4 * b]
    for v, nxt in zip(inrun, inrun[1:] + [RAM + 4 * b]):
        funcs[v] = nxt - v
lines = ''.join(f'    {{ name = "func_{v:08X}", vram = 0x{v:08X}, size = 0x{funcs[v]:X} }},\n' for v in sorted(funcs))
sec = f'[[section]]\nname = "{NAME}"\nrom = 0x{ROM:08X}\nvram = 0x{RAM:08X}\nsize = 0x{SZ:X}\n\nfunctions = [\n{lines}]\n\n'
t = open('syms/dump.toml').read()
if f'name = "{NAME}"' in t:
    t = re.sub(r'\[\[section\]\]\nname = "%s".*?\]\n\n' % NAME, sec, t, flags=re.S)
else:
    i = t.index('[[section]]\nname = "ovl_a"'); t = t[:i] + sec + t[i:]
open('syms/dump.toml', 'w').write(t)
# the section is regenerated whole: drop earlier loop injections for it
e = [l for l in open('syms/extra_funcs.txt') if not l.startswith(NAME + ' ')]
open('syms/extra_funcs.txt', 'w').write(''.join(e))
print(f'{NAME}: {len(runs)} code runs, {len(funcs)} functions')

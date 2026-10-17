#!/usr/bin/env python3
"""Discover functions in the hack's far code block (position-independent code loaded into a
game-allocated buffer). Usage: find_far_funcs.py <rom_start> <ram_start> <size>
Seeds: every "pointer at 0x800559F0 + offset" jump in the mapped code (offsets are relative to
rom 0x2F9D7C4, see notes/hack-map.md), then recursive descent inside the block. Prints
dump.toml function lines for a section at <ram_start>."""
import re, struct, sys
d = open('vpw2.z64', 'rb').read()
rom_start, ram_start, size = (int(x, 16) for x in sys.argv[1:4])
P_ROM = 0x2F9D7C4
W = lambda rom: struct.unpack_from('>I', d, rom)[0]
def branch_target(w, rom):
    op = w >> 26
    if op in (2, 3): return None, op == 3  # absolute: handled by caller
    if op in (1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0x11 and (w >> 21) & 0x1F == 8):
        return rom + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2), False
    return None, False
# Seeds: every computed jump "P + offset" where P = the word at 0x800559F0 (the block's anchor,
# 0x80368AF0 = block start + 0x3FC0: the block entry zeroes 0x1AF40 bytes from P and jumps to
# P + 0x1AF40). Evaluate the lui/lw/addiu/lui/ori/addu sequence symbolically up to the jr/jalr.
P_RAM = 0x80368AF0
P_ROM = rom_start + (P_RAM - ram_start)
regions = [(0x1000, 0x4BF40), (0x4BF40, 0x695E0), (0x71A90, 0x7C710), (0x84710, 0xD5840), (0xE11A0, 0x14BCA0),
           (0x2FC6444, 0x2FC6764), (rom_start, rom_start + size)]
seeds = {rom_start}
def eval_seq(o):
    """o = rom offset of `lw rX, 0x59f0(rX)`; follow up to 16 instructions, return jump target rom or None."""
    regs = {}
    rt = (W(o) >> 16) & 0x1F; regs[rt] = ('P', 0)
    for k in range(1, 16):
        w = W(o + 4 * k); op = w >> 26; rs = (w >> 21) & 0x1F; rtt = (w >> 16) & 0x1F; rd = (w >> 11) & 0x1F; imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        if op == 0xF: regs[rtt] = ('K', imm << 16)
        elif op == 0xD and rs in regs: regs[rtt] = (regs[rs][0], regs[rs][1] | imm)
        elif op == 9 and rs in regs: regs[rtt] = (regs[rs][0], regs[rs][1] + simm)
        elif op == 0 and (w & 0x3F) == 0x21 and rs in regs and rtt in regs:  # addu
            a, b = regs[rs], regs[rtt]
            if a[0] == 'P' and b[0] == 'K': regs[rd] = ('P', a[1] + b[1])
            elif a[0] == 'K' and b[0] == 'P': regs[rd] = ('P', a[1] + b[1])
            else: regs.pop(rd, None)
        elif op == 0 and (w & 0x3F) in (8, 9):  # jr / jalr
            r = regs.get(rs)
            return P_ROM + r[1] if r and r[0] == 'P' else None
        elif op in (2, 3): return None
        else:
            if rtt in regs and op in (0x23, 0x20, 0x24, 0x25, 0x21): regs.pop(rtt, None)
            if op == 0 and rd in regs and (w & 0x3F) not in (8, 9): regs.pop(rd, None)
    return None
for a, b in regions:
    for o in range(a, b - 64, 4):
        w = W(o)
        if (w >> 26) == 0x23 and (w & 0xFFFF) == 0x59F0 and ((w >> 21) & 0x1F) == ((w >> 16) & 0x1F):
            t = eval_seq(o)
            if t is not None: seeds.add(t)
# Pointers the hack stores for later (installer tables, `lui rX,hi; ori rX,lo; addu rX,$s0,rX`
# with $s0 = P - 0x7F00 inside the block and the trampoline copy): also code entry points.
for a, b in [(rom_start, rom_start + size), (0x2FC6444, 0x2FC6764)]:
    for o in range(a, b - 16, 4):
        w = W(o)
        if (w >> 26) != 0xF or not (0 <= (w & 0xFFFF) <= 3): continue
        rt = (w >> 16) & 0x1F; w2 = W(o + 4)
        if (w2 >> 26) not in (0xD, 9) or ((w2 >> 21) & 0x1F) != rt or ((w2 >> 16) & 0x1F) != rt: continue
        val = ((w & 0xFFFF) << 16) | (w2 & 0xFFFF)
        for k in (2, 3, 4):
            w3 = W(o + 4 * k)
            if (w3 >> 26) == 0 and (w3 & 0x3F) == 0x21 and {(w3 >> 21) & 0x1F, (w3 >> 16) & 0x1F} == {16, rt}:
                seeds.add(P_ROM - 0x7F00 + val); break
seeds = {s for s in seeds if rom_start <= s < rom_start + size}
funcs = {}; todo = sorted(seeds)
while todo:
    entry = todo.pop()
    if entry in funcs: continue
    pc = entry; maxfwd = entry; end = None
    while pc < rom_start + size:
        w = W(pc); t, _ = branch_target(w, pc)
        if (w >> 26) == 3:  # jal: absolute targets outside the block are game functions
            pass
        if t is not None and t > maxfwd and t < entry + 0x4000: maxfwd = t
        uncond = (w == 0x03E00008) or ((w & 0xFC1F07FF) == 0x00000008) or ((w >> 26) == 2) or (w & 0xFFFF0000) == 0x10000000
        if uncond and pc >= maxfwd: end = pc + 8; break
        pc += 4
    funcs[entry] = (end or pc) - entry
    # callers inside the block use bal/jalr? scan body for 'bal' (regimm 0x11) targets inside block
    for o in range(entry, entry + funcs[entry], 4):
        w = W(o)
        if (w >> 26) == 1 and ((w >> 16) & 0x1F) in (0x10, 0x11):
            t = o + 4 + (struct.unpack('>h', w.to_bytes(4, 'big')[2:])[0] << 2)
            if rom_start <= t < rom_start + size and t not in funcs: todo.append(t)
for r in sorted(funcs):
    v = ram_start + (r - rom_start)
    print(f'    {{ name = "func_{v:08X}", vram = 0x{v:08X}, size = 0x{funcs[r]:X} }},')
print(f'# {len(funcs)} functions from {len(seeds)} seeds', file=sys.stderr)

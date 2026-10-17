#!/usr/bin/env python3
"""Hand-verified corrections to the VPW2 symbol map for the VPW64 Deluxe hack. The hack
rewrote these spots: it shortened or replaced functions and dropped data between them, so the
retail sizes run into garbage and the recompiler would stub the whole function. Idempotent."""
import re, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys; sys.path.insert(0, 'tools')
from recomp_loop import add_func_to_dump
SIZES = {  # name: new size (see notes/hack-map.md)
    'func_80003E88': 0xC0, 'func_80003EB0': 0x98, 'func_80009628': 0x28,
    'func_80030C5C': 0x20, 'func_80030C7C': 0x2C, 'func_80030D44': 0x1C,
    'func_8003C5D0': 0x38,  # text-id hook chain: 0x800E9EE8 -> far 0x803874D0 -> here -> 0x8003C3F0 -> 0x8002C560 -> back
}
ADD = [('main_1050', 0x80030CA8, 0x8), ('main_1050', 0x80030D0C, 0x1C), ('main_1050', 0x80030D28, 0x1C), ('main_1050', 0x80030D60, 0x68),
       ('hack_main', 0x8003C3F0, 0x8), ('main_1050', 0x8002C560, 0x48)]
UNSTUB = ['func_80003E88', 'func_80003EB0', 'func_80009628', 'func_80030C5C', 'func_80030C7C', 'func_80030D44']
s = open('syms/dump.toml').read()
for name, size in SIZES.items():
    s, n = re.subn(r'(name = "%s", vram = 0x[0-9A-F]+, size = )0x[0-9A-F]+' % name, r'\g<1>0x%X' % size, s)
    assert n == 1, name
open('syms/dump.toml', 'w').write(s)
for sec, vram, size in ADD:
    if f'vram = 0x{vram:08X},' not in s: add_func_to_dump(sec, f'func_{vram:08X}', vram, size)
stubs = [l for l in open('syms/manual_stubs.txt').read().split('\n') if l.strip() and l.strip() not in UNSTUB]
open('syms/manual_stubs.txt', 'w').write('\n'.join(stubs) + '\n')
# func_8002C580 (dead libultra space) is now the middle of the 0x8002C560 hook; drop it.
s = open('syms/dump.toml').read(); s = re.sub(r'\n *\{ name = "func_8002C580", vram = 0x8002C580, size = 0xCC \},', '', s); open('syms/dump.toml', 'w').write(s)
for p in ['vpw2.toml', 'syms/stub_candidates.txt']:
    s = open(p).read().replace('    "func_8003C5D0",\n', ''); open(p, 'w').write(s)
print('map fixes applied; manual stubs now:', stubs)

# The hack saves the return address in a scratch register (`move $t9,$ra` ... `jr $t9`).
# N64Recomp does not keep return addresses in $ra, so make those jumps ordinary returns
# (`jr $ra`, which the recompiler emits as a C return). Instruction patches in vpw2.toml.
PATCHES = [('func_80006BEC', 0x80006C10)]   # 0x8000724C is handled by tools/hand_edits.py (setjmp/longjmp)
t = open('vpw2.toml').read()
for func, vram in PATCHES:
    if f'vram = 0x{vram:08X}' in t: continue
    t += f'\n[[patches.instruction]]\nfunc = "{func}"\nvram = 0x{vram:08X}\nvalue = 0x03E00008  # jr $ra (was jr $t8/$t9: saved return address, see notes/hack-map.md)\n'
open('vpw2.toml', 'w').write(t)
print('instruction patches:', len(PATCHES))

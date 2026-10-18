#!/usr/bin/env python3
"""Hand edits to the generated C that no map entry or instruction patch can express.
Re-applied after every regen (tools/regen.sh); idempotent; fails loudly if an anchor moved.

1. The hack's text codec at 0x80007070 saves $ra in $t9 and its bit-reader/-writer subroutines
   (called with jal) bail out of the WHOLE routine with a branch to `jr $t9` at 0x8000724C.
   N64Recomp turns jal into a C call, so that bail-out must unwind the C frames: setjmp at the
   routine's entry, longjmp at every copy of the exit."""
import glob, re, sys
edited = 0
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    if '0x8000724C: jr' not in s and 'RECOMP_FUNC void func_80007070(' not in s: continue
    if 'vpw64dx_t9_exit' in s: continue
    s, n_hdr = re.subn(r'(#include "funcs\.h"\n)', r'\1#include <setjmp.h>\nextern jmp_buf vpw64dx_t9_exit;\n', s, count=1)
    assert n_hdr == 1, fn + ': no funcs.h include'
    s, n_exit = re.subn(r'(// 0x8000724C: jr[^\n]*\n(?:[^\n]*\n){0,2}?)(?:    LOOKUP_FUNC\(ctx->r25\)\(rdram, ctx\);\n)?    return;',
                        r'\1    longjmp(vpw64dx_t9_exit, 1);', s)
    s, n_entry = re.subn(r'(RECOMP_FUNC void func_80007070\(uint8_t\* rdram, recomp_context\* ctx\) \{\n[^\n]*\n    int c1cs = 0;\n)',
                         r'\1    if (setjmp(vpw64dx_t9_exit)) return;   /* bail-out from the bit subroutines */\n', s)
    assert n_exit >= 1 and n_entry == 1, f'{fn}: exits={n_exit} entry={n_entry}'
    open(fn, 'w', encoding='utf-8').write(s); edited += 1
    print(f'{fn}: {n_exit} exits -> longjmp, setjmp at func_80007070')
if edited == 0: print('hand edits already present')

# 2. hack_far is mapped as non-overlapping pieces (routine starts). A piece whose last
#    instruction is not an unconditional jump falls through into the next piece on hardware;
#    the generated C would just return. Append a tail call to the next piece.
import struct
rom_data = open('vpw2.z64', 'rb').read()
BLOCKS = [(0x2FA1704, 0x80364B30, r'803[6-8]'), (0x2F1A9D4, 0x801BB3A0, r'801B[BC]')]   # hack_far, hack_match
def uncond(w):
    return w == 0x03E00008 or (w & 0xFC1F07FF) == 0x8 or (w >> 26) == 2 or (w & 0xFFFF0000) == 0x10000000
chained = 0
dump_text = open('syms/dump.toml').read()
for ROM, RAM, pat in BLOCKS:
    far = sorted((int(v, 16), int(s, 16)) for v, s in re.findall(r'name = "func_(?:%s[0-9A-F]+)", vram = (0x[0-9A-F]+), size = (0x[0-9A-F]+)' % pat, dump_text))
    starts = {v for v, s in far}
    for v, s in far:
        end = v + s
        if end not in starts: continue
        last = struct.unpack_from('>I', rom_data, ROM + (end - 8 - RAM))[0]
        if uncond(last): continue
        for fn in glob.glob('RecompiledFuncs/*.c'):
            src = open(fn, encoding='utf-8', errors='replace').read()
            sig = f'RECOMP_FUNC void func_{v:08X}(uint8_t* rdram, recomp_context* ctx) {{\n'
            if sig not in src: continue
            i = src.index(sig); j = src.index('\n;}', i)
            if f'func_{end:08X}(rdram, ctx);' in src[i:j]: break   # already chained
            src = src[:j] + f'\n    func_{end:08X}(rdram, ctx);   /* falls through on hardware */\n    return;' + src[j:]
            open(fn, 'w', encoding='utf-8').write(src); chained += 1; break
print(f'{chained} far-block pieces chained to their successor')

# 3. Cheat hook: "Unlock all wrestlers". func_800F4668(n) is the game's own "is unlock n set in the
#    save" check (bitfield at 0x800A440E); unlocks 0..0x14 are the 21 lockable wrestlers listed in the
#    table at 0x8003FD44 (see notes/ram-map.md). With the cheat on, those answer "unlocked"; the save
#    itself is never written, so switching the cheat off locks them again.
hooked = 0
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    sig = 'RECOMP_FUNC void func_800F4668(uint8_t* rdram, recomp_context* ctx) {\n'
    if sig not in s or 'vpw64dx_unlock_all_wrestlers' in s: continue
    s, n = re.subn(re.escape(sig) + r'([^\n]*\n    int c1cs = 0;\n)',
                   lambda m: sig + m.group(1) + '    { extern int vpw64dx_unlock_all_wrestlers(void);\n'
                   '      if (vpw64dx_unlock_all_wrestlers() && (uint32_t)ctx->r4 <= 0x14u) { ctx->r2 = 1; return; } }\n', s)
    assert n == 1, fn + ': func_800F4668 entry not found'
    open(fn, 'w', encoding='utf-8').write(s); hooked += 1
print(f'unlock-all hook in {hooked} file(s)' if hooked else 'unlock-all hook already present')

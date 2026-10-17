#!/usr/bin/env python3
"""Bring-up diagnostic: every hack-section function records its name in a global on entry
(ring of the last 8), which the crash handler prints. Regen wipes it; apply on demand."""
import re, glob
names = set(re.findall(r'name = "(func_(?:803[6-8]|8003[A-F]|800[9A]0|801B[BC])[0-9A-F]+)"', open('syms/dump.toml').read())) | {'func_80023254', 'func_800231DC', 'func_80023100', 'func_800230A8', 'func_8003B268'}
n = 0
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    if 'vpw_note_piece(' in s: continue
    def rep(m):
        return m.group(0) + f'    vpw_note_piece("{m.group(1)}", (uint32_t)ctx->r16, (uint32_t)ctx->r29);\n' if m.group(1) in names else m.group(0)
    s2, k = re.subn(r'RECOMP_FUNC void (\w+)\(uint8_t\* rdram, recomp_context\* ctx\) \{\n[^\n]*\n    int c1cs = 0;\n', rep, s)
    if 'vpw_note_piece(' in s2:
        s2 = s2.replace('#include "funcs.h"\n', '#include "funcs.h"\nvoid vpw_note_piece(const char*, uint32_t, uint32_t);\n', 1); n += s2.count('vpw_note_piece("')
        open(fn, 'w', encoding='utf-8').write(s2)
print('piece markers added:', n)

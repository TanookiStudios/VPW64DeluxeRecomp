#!/usr/bin/env python3
"""Bring-up diagnostic (wiped by tools/regen.sh): make every translated function record its name, $s3 and
$sp on entry (main thread only, see vpw_note_piece in src/game/recomp_api.cpp; the crash handler prints the
last 128), and arm a tripwire at the main loop head (func_80023100) that fires the first time it is entered
with $s3 different from the loop's own value (0x80047CD0). Use it to see the exact path into a corrupted
main-loop restart."""
import glob, re
n = 0
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    if 'vpw_note_piece(' in s: continue
    out = []
    for m in re.finditer(r'RECOMP_FUNC void (\w+)\(uint8_t\* rdram, recomp_context\* ctx\) \{\n[^\n]*\n    int c1cs = 0;\n', s):
        extra = ''
        if m.group(1) == 'func_80023100':
            extra = ('    { extern void vpw_tripwire(const char*, uint32_t, uint32_t, uint32_t, uint32_t);\n'
                     '      if ((uint32_t)ctx->r19 != 0x80047CD0u) vpw_tripwire("func_80023100 entered with bad s3", '
                     '(uint32_t)ctx->r19, (uint32_t)ctx->r29, (uint32_t)ctx->r31, (uint32_t)ctx->r16); }\n')
        out.append((m.end(), extra + f'    vpw_note_piece("{m.group(1)}", (uint32_t)ctx->r19, (uint32_t)ctx->r29);\n'))
        n += 1
    for at, txt in reversed(out): s = s[:at] + txt + s[at:]
    s = s.replace('#include "funcs.h"\n', '#include "funcs.h"\nvoid vpw_note_piece(const char*, uint32_t, uint32_t);\n', 1)
    open(fn, 'w', encoding='utf-8').write(s)
print(f'trace markers in {n} functions')

# --returns: also check $sp at every return (functions that return with a moved stack pointer).
import sys
if '--returns' in sys.argv:
    r = 0
    for fn in glob.glob('RecompiledFuncs/*.c'):
        s = open(fn, encoding='utf-8', errors='replace').read()
        if 'vpw_ret_check' in s: continue
        s = re.sub(r'(RECOMP_FUNC void \w+\(uint8_t\* rdram, recomp_context\* ctx\) \{\n[^\n]*\n    int c1cs = 0;\n)',
                   r'\1    uint32_t vpw_sp0 = (uint32_t)ctx->r29;\n', s)
        s, k = re.subn(r'(\n\s*)return;', r'\1{ vpw_ret_check(__func__, vpw_sp0, (uint32_t)ctx->r29, (uint32_t)ctx->r19); return; }', s)
        s = s.replace('#include "funcs.h"\n', '#include "funcs.h"\nvoid vpw_ret_check(const char*, uint32_t, uint32_t, uint32_t);\n', 1)
        open(fn, 'w', encoding='utf-8').write(s); r += k
    print(f'return checks: {r}')

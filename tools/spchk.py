#!/usr/bin/env python3
"""Bring-up diagnostic: wrap every non-tail call in the generated C with a stack-pointer
balance check that prints the first function whose callee returns with a different $sp.
Applied on demand (not part of regen); regen wipes it."""
import re, glob
total = 0
pat = re.compile(r'^    (func_[0-9A-F]+|static_[0-9]+_[0-9A-F]+|[A-Za-z0-9_]+_recomp|LOOKUP_FUNC\([^)]*\))\(rdram, ctx\);\n(?!    return;)', re.M)
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    if '[spchk]' in s: continue
    if '#include <stdio.h>' not in s: s = s.replace('#include "funcs.h"\n', '#include "funcs.h"\n#include <stdio.h>\n', 1)
    def rep(m):
        return f'    {{ unsigned _spb = (unsigned)ctx->r29; {m.group(1)}(rdram, ctx); if ((unsigned)ctx->r29 != _spb) fprintf(stderr, "[spchk] %s: sp %08X -> %08X after {m.group(1)}\\n", __func__, _spb, (unsigned)ctx->r29); }}\n'
    s2, n = pat.subn(rep, s); total += n
    open(fn, 'w', encoding='utf-8').write(s2)
print('stack checks added:', total)

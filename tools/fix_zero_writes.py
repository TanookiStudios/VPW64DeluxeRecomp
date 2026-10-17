#!/usr/bin/env python3
"""The hack left `add $zero,$zero,$zero` words (0x00000020) inside two functions. N64Recomp
emits them as `0 = ADD32(0, 0);`, which does not compile; on hardware a write to $zero is a
no-op, so drop the statement."""
import glob, re
n = 0
for fn in glob.glob('RecompiledFuncs/*.c'):
    s = open(fn, encoding='utf-8', errors='replace').read()
    s2, k = re.subn(r'^(\s*)0 = [^\n]*;', r'\1/* write to $zero dropped */', s, flags=re.M)
    if k: open(fn, 'w', encoding='utf-8').write(s2); n += k
print(f'{n} writes to $zero dropped')

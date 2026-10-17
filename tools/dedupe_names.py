#!/usr/bin/env python3
"""Functions in syms/dump.toml must have unique C names across sections. Mid-entries added
for co-resident overlays reuse the same func_XXXXXXXX name in several sections; the linker
then keeps one copy and every overlay's table points at it. Rename later duplicates with the
section name as a suffix. Idempotent; run before the recompiler."""
import re
t = open('syms/dump.toml').read()
out = []; seen = {}; sec = None; renamed = 0
for line in t.split('\n'):
    m = re.match(r'name = "(\w+)"$', line)
    if m: sec = m.group(1)
    f = re.search(r'\{ name = "(\w+)", vram = (0x[0-9A-Fa-f]+), size', line)
    if f:
        name = f.group(1)
        base = re.sub(r'_(entry|main_1050|hack_main|hack_tramp|hack_far|hack_match|ovl_[a-d])$', '', name)
        if base in seen and seen[base] != sec:
            new = f'{base}_{sec}'
            if name != new:
                line = line.replace(f'name = "{name}"', f'name = "{new}"'); renamed += 1
        else:
            seen.setdefault(base, sec)
    out.append(line)
open('syms/dump.toml', 'w').write('\n'.join(out))
print(f'{renamed} duplicate function names made unique')

#!/usr/bin/env python3
"""Find RAM addresses from whole-memory snapshots (VPW_RAM_SNAP in src/main/main.cpp).

  tools/ram_find.py delta <a.bin> <b.bin> <min> <max> [width]   values that grew by min..max between a and b
  tools/ram_find.py same  <a.bin> <b.bin> <value> [width]        values equal to <value> in both
  tools/ram_find.py read  <a.bin> <addr> [count]                 dump words at an address

Snapshots are the N64's 8 MB of memory in the runtime's layout (big-endian words), so a
16-bit value at address A lives at bytes (A^2, A^2+1) and a byte at A^3. width: 1, 2 or 4.
Prints N64 addresses (0x80xxxxxx). A candidate only counts as found once VPW_POKE at that
address visibly changes the screen (notes/ram-map.md keeps the proof)."""
import struct, sys

def load(p): return open(p, 'rb').read()
def val(d, off, w):
    if w == 4: return struct.unpack_from('>I', d, off)[0]
    if w == 2: return struct.unpack_from('>H', d, off ^ 2)[0]
    return d[off ^ 3]
def main():
    cmd = sys.argv[1]
    if cmd == 'delta':
        a, b = load(sys.argv[2]), load(sys.argv[3]); lo, hi = int(sys.argv[4]), int(sys.argv[5]); w = int(sys.argv[6]) if len(sys.argv) > 6 else 2
        hits = []
        for off in range(0, len(a) - 4, w if w > 1 else 1):
            d = val(b, off, w) - val(a, off, w)
            if lo <= d <= hi: hits.append((off, val(a, off, w), val(b, off, w)))
        for off, x, y in hits[:200]: print(f'0x{0x80000000 + off:08X}  {x} -> {y}  (+{y - x})')
        print(f'{len(hits)} candidates')
    elif cmd == 'same':
        a, b = load(sys.argv[2]), load(sys.argv[3]); v = int(sys.argv[4], 0); w = int(sys.argv[5]) if len(sys.argv) > 5 else 2
        hits = [off for off in range(0, len(a) - 4, w if w > 1 else 1) if val(a, off, w) == v and val(b, off, w) == v]
        for off in hits[:200]: print(f'0x{0x80000000 + off:08X}')
        print(f'{len(hits)} candidates')
    elif cmd == 'read':
        a = load(sys.argv[2]); addr = int(sys.argv[3], 16) & 0x7FFFFF; n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
        for i in range(n): print(f'0x{0x80000000 + addr + 4 * i:08X}: {val(a, addr + 4 * i, 4):08X}')
    else: sys.exit(__doc__)
if __name__ == '__main__': main()

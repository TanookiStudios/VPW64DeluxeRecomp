# RAM map for cheats (with proof)

Method: `VPW_RAM_SNAP=ms,ms,...` writes the whole 8 MB of game memory at those times
(`src/main/main.cpp`, `ram_diagnostics`); `tools/ram_find.py delta a.bin b.bin min max width`
lists addresses whose value grew by min..max between two snapshots. A candidate counts as
found only when `VPW_POKE=addr:w=val` (from `VPW_POKE_AFTER=ms`) visibly changes the screen.

Snapshots come from the scripted match run (`tools/capture.sh`, Start at 24 s, A to the
match card, Start/B/A from 58 s; the bell rings about 91 s after launch).

## Match clock

- Every counter in memory ticks 64 per real second in this build (512 per 8 s), not 60.
- Candidates that grow 512 per 8 s (16-bit): 0x8007DF00, 0x8007DF40 (7747 at 96 s: a global
  counter, running since long before the match), 0x8009F118 (same), **0x800DD4A0** (260 at 96 s,
  772 at 104 s, 1284 at 112 s: matches the bell at ~92 s, so this is the match's own frame counter).
- 0x800DD4A0 RULED OUT: holding it at 0 kills the audio microcode task even when the poke starts
  after the bell (`VPW_POKE_AFTER=97000`, work/run88): it is part of the audio command list, and
  its +512/8 s is the audio sequencer's own tick, not the match clock.
- Dead ends: no byte, halfword or word anywhere holds the displayed seconds (5 → 13 → 21) or
  counts down from the 30-minute limit in frames.

## Spirit (PROVEN)

- Player slots: four blocks of 0x314 bytes from 0x8016C440. The game's own init loop
  (`0x8012A5FC`-`0x8012A684` in ovl_c: `addiu $s0,$s0,0x314` over four slots) gives the stride.
- Spirit byte at slot +0x3B: P1 = 0x8016C47B (also the GameShark "P1 spirit" address on cheat
  sites), P2 = 0x8016C78F, P3 = 0x8016CAA3, P4 = 0x8016CDB7. Normal range about 0..0x60;
  0xFF lights the SPIRIT bar red (special ready).
- Proof: `VPW_POKE=8016C47B:b=255` from 98 s: P1's bar full and red all match (work/run102);
  `VPW_POKE=8016C78F:b=0`: the CPU's bar empty, blue stub, sluggish wrestler (work/run105);
  both through the real Game-tab switches: notes/cheats-proof.png (work/run111).
- In-match gate (the blocks hold other data outside a match): slot0+0x24 == 0xFFFF,
  +0x62 == 0x0800, +0x7E == 0x0600 during every match snapshot; 0x8016/0xC198/0 at the title,
  the wrestler select and the ring entrance (work/run110, work/run80).
- Memory snapshots are host-order words: the first search used the wrong byte order and chased
  float fragments for an hour. `tools/ram_find.py` and the poke code are fixed.

## CPU control (NOT found)

- Slot bytes that differ between a human 2P and the CPU: +0x14..0x17 (word: 1 for P1, 0 for 2P,
  -1 for CPU), +0x62 (flags, 8 for CPU), +0x73 (1 vs 0x81), +0x87/+0x95/+0x99 (0 vs 1), +0x2DD.
  Writing +0x73 = 1, the +0x14 word = 0, or +0x87/+0x95/+0x99 = 0 changed nothing; writing +0x62 = 0
  or the halfword at +0x2E = 0 froze the game. The AI runs from somewhere else. A "1P vs 2P" match
  with nobody on pad 2 is the built-in way to get an opponent who never fights back.

## Match clock (NOT found)

See above: nothing in memory holds the displayed seconds or a 60-per-second frame count.

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

## Spirit (player 1)

Not found yet. The bar stays full while the CPU opponent is passive; snapshots after the first
exchanges are needed (`work/run88`), then a decreasing 8/16-bit value near player 1's data.

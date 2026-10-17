# Gate 2 report: Virtual 64 Pro Wrestling Deluxe on Mac

Date: 2026-10-17. Nothing is pushed; local commits only.

## What works (proof in `notes/`)

Every run below was unattended: `tools/capture.sh` boots the game from the ROM, feeds a scripted
controller, takes window screenshots at fixed times, and quits.

| Proof | Screenshot |
|---|---|
| Boots to the title screen (about 24 s after launch) | `notes/title-first-boot.png` |
| Attract-mode demo matches run 90 s without a crash | `notes/demo-match-1.png`, `notes/demo-match-2.png` |
| Start at the title, then A through mode, match type, promotion, wrestler select | `notes/promotion-select.png`, `notes/wrestler-select.png` |
| Costume screen and match card (Misawa vs Misawa, 30 minutes 1 fall) | `notes/match-card.png` |
| Ring entrance | `notes/ring-entrance.png` |
| Match running: timer, spirit bars, lock-up in the corner | `notes/match-0004.png`, `notes/match-0012.png` |

Controller input is proven by the menus: nothing past the title happens without the scripted
presses. In the match the scripted moves (left, up, A, right, B) are consistent with what the
screenshots show, but I have not isolated player movement from the CPU opponent yet.

Build and run, from the repo root with the ROM at `rom/vpw64deluxe.z64`:

```bash
./setup.sh
tools/regen.sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build --target VPW64Deluxe -j10
tools/capture.sh work/proof 105 "24000:start;24400:;28000:a;28400:" 30 60 90
```

The script that reaches a match: Start at 24 s, A every 3 s from 28 s to 52 s, then
Start / B / A one second apart from 58 s (the match card needs that combination; A alone
does not advance it).

## What is broken or unverified

1. Pressing Start while the demo match is loading (not at the title) crashed in hack code
   (`func_80104D40`, a nil pointer). Seen in an earlier session, not re-tested since.
2. Quitting the game crashes on the way out (the menu library's shutdown; harmless but ugly).
3. The costume screen earlier showed garbled labels. The cause (a text lookup the mod rerouted
   through four hops, one of which my tools had stubbed) is fixed, but I have no screenshot of
   the costume screen after the fix.
4. The match-time code block the mod loads is mapped at a fixed address (0x801BB3A0). If another
   match type lands it elsewhere, the log will say `Failed to find function at 0x801B....`.
5. Audio, saving (SRAM), performance, and any match type other than Single are untested.
6. `icons/` is jessetbh's game-logo art and is git-ignored; we need our own icon and art.
7. The repo must be GPL-3.0 because the map and fixup tools come from jessetbh/VPW2Recomp.
8. Windows and Linux builds do not exist yet.

## Mod structure, for the record

See `notes/hack-map.md`. The mod keeps all retail code in place and adds: an entry cave, a code
block in the fixed segment's data area, 41 trampolines copied into memory at boot, a 0x25380-byte
block loaded in 0x100-byte pieces at boot, and a 0x1100-byte block loaded for each match.
Three recompiler hazards cost most of the time: helpers that return by jumping, helpers that
jump *into* another function's body (a call, not a return), and the mod's jump tables that
look like data.

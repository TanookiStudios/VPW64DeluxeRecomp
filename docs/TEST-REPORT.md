# Test report: what has been played on the Mac build

Date: 2026-10-18. Every run was unattended (`tools/explore.sh`, `tools/capture.sh`), muted, and used a
throwaway save folder. "OK" means no crash, no missing translated code, and the game's sound pipeline kept
running to the end of the run (a frozen game stops producing sound).

## Match types (Exhibition)

| Match | Result | Seen |
|---|---|---|
| Single | OK | full match with a CPU opponent, cheats on and off |
| Tag | OK | 2 vs 2 wrestler select, tag match underway |
| 3 Way | OK | three wrestlers in the ring, match clock running |
| Battle Royale | OK | four wrestlers, title selection screen first |
| Elimination | OK | four wrestlers in the ring |

## Modes (main menu)

| Mode | Result | Seen |
|---|---|---|
| Royal Road | OK | entrance curtain, a full match |
| League | OK | 12-player setup, wrestler select |
| Tournament | OK | title selection, wrestler select |
| Event | OK | event name, date, arena setup screen |
| Ranking | OK | single-ranking arena and the rankings list |
| Edit Mode | OK | wrestler editor: profile, appearance, moves, parameters, name entry |
| Options | OK | difficulty, spirit meter, referee, sound, controller setup, data |

## Other checks

- **Sound:** recorded with `VPW_AUDIO_DUMP`: real stereo, played at the game's own rate (28805 Hz, so speed and
  pitch are right), zero dropouts in two minutes.
- **Saves:** a counter in the save goes up by one on every launch across ten launches, so the game reads its save
  back each time.
- **Pause menu** in a match: continue, rematch, quit match, spirit meter, referee, replay.

## Second round (2026-10-18 evening)

- **Two controllers:** a 1P vs 2P match with two scripted pads. Pad 2 walked its wrestler across the ring
  while pad 1 stood still, then pad 1 walked the other wrestler to the far ropes. Both pads are assigned
  and drive their own wrestler.
- **Long Tournament run (15 minutes):** found a real crash. Choosing **Quit Match** from the pause menu
  crashed the game every time (the menus reloaded without part of the mod's code). Fixed; after the fix,
  quitting returns to the Tournament bracket, Skip Match advances the bracket and Watch starts the next match.
  Replay, Referee and Rematch from the pause menu were already fine.
- **Linux:** booted the Linux download in an Ubuntu 22.04 container on a virtual screen with software
  graphics (`tools/linux_smoke.sh`). Found a real bug: the window was not created for Vulkan graphics, so the
  Linux build crashed about a second after starting. Fixed; it now reaches the title screen and quits cleanly.

## Third round

- **A match ending by pinfall crashed the game** on the three-count (the longer runs had never finished a
  match). Fixed (a mod hook unwound the stack twice; notes/hack-map.md). Verified: the match ends and the game
  plays its post-match replay (notes/match-end-replay.png).
- **Unlock all wrestlers** cheat proven: the hidden Legends 3 group appears only with the switch on.
- **Can't be hurt** proven: under the same CPU attacks player 1's condition stays at 255 (it falls to 60 normally).
- **Triple damage** proven: the same opening hits take an idle opponent to 201 instead of 237 (three times the drop).

## Fourth round (2026-10-19)

- **Against an N64 emulator** (mupen64plus, same ROM, no input): the port shows the same opening screens in
  the same order and for the same time: the memorial screen about 6 s, the notice screen about 6 s, the logos
  about 5 s, then the title for about 31 s before the attract demo. Text, logos, the blinking PRESS START and
  the DEMO overlay all match. Which demo match plays is picked at random, so the wrestlers differ between runs.
  Sheets: notes/accuracy-port.png, notes/accuracy-emulator-opening.png, notes/accuracy-emulator-title-demo.png.
- **Watch mode** (CPU vs CPU) played a match to its finish and the game carried on; the match clock runs at
  real-time speed.
- **Every call from the original game into the mod's code** was checked for the kind of bug that crashed the
  match ending. Only that one call had it, and it is fixed.
- **Edit Mode saves:** put a mask on M. Misawa, accepted, left Edit Mode, quit, and started again keeping the
  save. Misawa still had the mask (notes/editmode-save-proof.png).

## Not tested yet

- Playing a Royal Road, League or Tournament through to the very end. The Tournament bracket advanced through
  skips and a watched match; my scripted presses on the bracket screen are sensitive to its animation timing,
  so I could not reliably drive it to a champion.
- Using an edited wrestler in a match (the edit itself saves and survives a restart).
- Linux on a real computer with a graphics card; Windows (built on a Windows PC from the build kit).

Testing note: the game repeats a held button after about a quarter second, so scripted presses must be short
taps (100 ms) or they count twice.

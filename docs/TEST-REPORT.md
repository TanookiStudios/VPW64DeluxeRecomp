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

## Not tested yet

- Finishing a whole Royal Road, League or Tournament run (each needs many matches).
- Every Edit Mode screen saving a new wrestler and using it in a match.
- Two real controllers at once.
- Linux and Windows builds on real machines.

Testing note: the game repeats a held button after about a quarter second, so scripted presses must be short
taps (100 ms) or they count twice.

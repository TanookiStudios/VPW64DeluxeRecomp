#!/usr/bin/env bash
# Make the release screenshots in docs/screenshots/ with nobody at the keyboard. The game
# window appears on screen for about two and a half minutes in total (four short launcher
# runs, then one run through to a match). Needs build/ and the ROM copy that tools/capture.sh
# uses. Fails loudly if any picture is missing.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=docs/screenshots
TMP=work/shots
rm -rf "$TMP"; mkdir -p "$TMP" "$OUT"; touch "$TMP/.start"
# (The copy must sit one folder below the repo root: capture.sh finds the repo from its own location.)
sed 's/WCW_AUTOBOOT="$rom" //' tools/capture.sh > work/capture_launcher.sh; chmod +x work/capture_launcher.sh

# Launcher pages: the scripted pad moves the highlight and presses A.
work/capture_launcher.sh "$TMP/l1" 14 "" 12 > /dev/null 2>&1 || true
cp "$TMP/l1/shot-12s.png" "$OUT/launcher-main.png"
work/capture_launcher.sh "$TMP/l2" 14 "8000:down;8300:;9000:a;9300:" 12 > /dev/null 2>&1 || true
cp "$TMP/l2/shot-12s.png" "$OUT/launcher-game.png"
work/capture_launcher.sh "$TMP/l3" 14 "8000:down;8300:;8600:down;8900:;9500:a;9800:" 12 > /dev/null 2>&1 || true
cp "$TMP/l3/shot-12s.png" "$OUT/launcher-settings.png"
work/capture_launcher.sh "$TMP/l4" 15 "8000:down;8300:;8600:down;8900:;9200:down;9500:;10000:a;10300:" 13 > /dev/null 2>&1 || true
cp "$TMP/l4/shot-13s.png" "$OUT/launcher-about.png"

# Title, menus, match card, entrance, the match, and this port's in-game menu (Back button).
s="24000:start;24400:"
# A short Down tap on the "1P vs 2P / 1P vs CPU / Watch" screen picks the CPU opponent.
for ((t=28000;t<=52000;t+=3000)); do [ $t -eq 37000 ] && s="${s};36500:down;36600:"; s="${s};${t}:a;$((t+400)):"; done
for ((t=58000;t<=64000;t+=3000)); do s="${s};${t}:start;$((t+400)):;$((t+1000)):b;$((t+1400)):;$((t+2000)):a;$((t+2400)):"; done
s="${s};86000:b;86300:;90000:b;90300:;94000:a;94300:;100000:back;100300:"
tools/capture.sh "$TMP/g" 106 "$s" 22 44 56 70 84 92 103 > /dev/null 2>&1 || true
cp "$TMP/g/shot-22s.png" "$OUT/title.png"
cp "$TMP/g/shot-44s.png" "$OUT/wrestler-select.png"
cp "$TMP/g/shot-56s.png" "$OUT/match-card.png"
cp "$TMP/g/shot-70s.png" "$OUT/ring-entrance.png"
cp "$TMP/g/shot-84s.png" "$OUT/match-1.png"
cp "$TMP/g/shot-92s.png" "$OUT/match-2.png"
cp "$TMP/g/shot-103s.png" "$OUT/ingame-menu.png"

MISSING=""
for n in launcher-main launcher-game launcher-settings launcher-about title wrestler-select match-card ring-entrance match-1 match-2 ingame-menu; do
    [ -s "$OUT/$n.png" ] && [ "$OUT/$n.png" -nt "$TMP/.start" ] || MISSING="$MISSING $n"
done
[ -z "$MISSING" ] || { echo "FAIL: screenshots missing or stale:$MISSING" >&2; exit 1; }
echo "11 screenshots in $OUT"

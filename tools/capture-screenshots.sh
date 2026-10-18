#!/usr/bin/env bash
# Make the release screenshots in docs/screenshots/ with nobody at the keyboard. The game
# window appears on screen for about two and a half minutes in total (four short launcher
# runs, then one run through to a match). Needs build/ and the ROM copy that tools/capture.sh
# uses. Fails loudly if any picture is missing.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=docs/screenshots
TMP=work/shots
rm -rf "$TMP"; mkdir -p "$TMP" "$OUT"
sed 's/WCW_AUTOBOOT="$rom" //' tools/capture.sh > "$TMP/capture_launcher.sh"; chmod +x "$TMP/capture_launcher.sh"

# Launcher pages: the scripted pad moves the highlight and presses A.
"$TMP/capture_launcher.sh" "$TMP/l1" 9 "" 7 > /dev/null 2>&1 || true
cp "$TMP/l1/shot-7s.png" "$OUT/launcher-main.png"
"$TMP/capture_launcher.sh" "$TMP/l2" 9 "4000:down;4300:;5000:a;5300:" 8 > /dev/null 2>&1 || true
cp "$TMP/l2/shot-8s.png" "$OUT/launcher-game.png"
"$TMP/capture_launcher.sh" "$TMP/l3" 9 "4000:down;4300:;4600:down;4900:;5500:a;5800:" 8 > /dev/null 2>&1 || true
cp "$TMP/l3/shot-8s.png" "$OUT/launcher-settings.png"
"$TMP/capture_launcher.sh" "$TMP/l4" 10 "4000:down;4300:;4600:down;4900:;5200:down;5500:;6000:a;6300:" 9 > /dev/null 2>&1 || true
cp "$TMP/l4/shot-9s.png" "$OUT/launcher-about.png"

# Title, menus, match card, entrance, the match, and this port's in-game menu (Back button).
s="24000:start;24400:"
for ((t=28000;t<=52000;t+=3000)); do s="${s};${t}:a;$((t+400)):"; done
for ((t=58000;t<=64000;t+=3000)); do s="${s};${t}:start;$((t+400)):;$((t+1000)):b;$((t+1400)):;$((t+2000)):a;$((t+2400)):"; done
s="${s};86000:a;86300:;90000:a;90300:;100000:back;100300:"
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
    [ -s "$OUT/$n.png" ] && [ "$OUT/$n.png" -nt "$TMP" ] || MISSING="$MISSING $n"
done
[ -z "$MISSING" ] || { echo "FAIL: screenshots missing or stale:$MISSING" >&2; exit 1; }
echo "11 screenshots in $OUT"

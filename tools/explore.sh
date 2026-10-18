#!/usr/bin/env bash
# Unattended smoke test of one menu path: boot, press Start at the title, play a scripted path from
# the main menu, then keep pressing A (and occasionally Start/B) to push through whatever screens
# follow. Reports CRASH (a native crash or a missing translated function), FROZEN (no sound
# batches in the last 15 s), or OK, and keeps screenshots every 12 s.
#
#   tools/explore.sh <name> <seconds> "<menu path>"
#     menu path: comma-separated pad buttons pressed 1.5 s apart from the main menu, e.g. "down,a"; "wait" skips a beat
#
# The game window is on screen for <seconds>.
set -euo pipefail
cd "$(dirname "$0")/.."
name=$1; secs=$2; path=${3:-}
out=work/explore/$name; rm -rf "$out"; mkdir -p "$out"
s="24000:start;24400:"
t=28000
IFS=',' read -ra steps <<< "$path"
# "wait" is a 1.5 s pause (screens drop presses while they animate in).
for b in ${steps[@]+"${steps[@]}"}; do [ "$b" = wait ] || s="${s};${t}:${b};$((t + 100)):"; t=$((t + 1500)); done
# Then push through: A every 2.5 s; every 4th press a Start, B, A sequence (the match card needs it).
k=0
for ((t = t + 1500; t < secs * 1000 - 3000; t += 2500)); do
    if (( k % 4 == 3 )); then s="${s};${t}:start;$((t + 250)):;$((t + 900)):b;$((t + 1150)):;$((t + 1700)):a;$((t + 1950)):"
    else s="${s};${t}:a;$((t + 300)):"; fi
    k=$((k + 1))
done
shots=(); for ((x = 20; x < secs; x += 12)); do shots+=("$x"); done
sed 's/WCW_AUTOBOOT=/WCW_AUDIO_LOG=1 WCW_AUTOBOOT=/' tools/capture.sh > work/capture_explore.sh; chmod +x work/capture_explore.sh
work/capture_explore.sh "$out" "$secs" "$s" "${shots[@]}" > "$out/capture.out" 2>&1 || true
log=$out/run.log
quit_line=$(grep -n 'WCW_QUIT_AFTER' "$log" | head -1 | cut -d: -f1); quit_line=${quit_line:-999999999}
crash=$(awk -v q="$quit_line" 'NR < q && /crash: SIG|Failed to find function|Unhandled jump target|Exiting with exit status/' "$log" | head -3)
last_audio=$(grep -o '^\[audio\] t=[0-9]*' "$log" | tail -1 | grep -o '[0-9]*$' || echo 0)
if [ -n "$crash" ]; then verdict="CRASH: $(echo "$crash" | head -1 | cut -c1-120)"
elif (( last_audio < secs - 15 )); then verdict="FROZEN (last sound batch at ${last_audio}s of ${secs}s)"
else verdict="OK"; fi
echo "$name: $verdict" | tee "$out/verdict.txt"

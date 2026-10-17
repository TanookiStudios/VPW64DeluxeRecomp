#!/usr/bin/env bash
# Unattended proof run: boot the game straight from the ROM, play a scripted set of
# controller presses, grab window screenshots at the named times, then quit.
# The window appears on screen for the whole run (about a minute); nobody has to touch it.
#
#   tools/capture.sh <out dir> <seconds> "<input script>" <shot times (seconds, space separated)>
#
# The input script format is documented at update_scripted_pad() in src/main/main.cpp.
set -euo pipefail
cd "$(dirname "$0")/.."
out=${1:?out dir}; secs=${2:?seconds}; script=${3:-}; shift 3 || true
shots=("$@")
mkdir -p "$out"
# The program runs from a copy outside Documents/Downloads (macOS asks for permission every
# time a freshly built program touches those folders), with the ROM copy in ~/Claude/vpw64-rom.
run=$HOME/Claude/vpw64-run; rom=$HOME/Claude/vpw64-rom/VPW64Deluxe.z64
[ -x build/VPW64Deluxe ] || { echo "build first: cmake --build build --target VPW64Deluxe" >&2; exit 1; }
[ -f "$rom" ] || { echo "ROM copy missing: $rom" >&2; exit 1; }
pkill -f "$run/VPW64Deluxe" 2>/dev/null || true; sleep 0.5
mkdir -p "$run" && rm -f "$run/VPW64Deluxe" && cp build/VPW64Deluxe "$run/" && rm -rf "$run/assets" && cp -R build/assets "$run/assets" && cp build/recompcontrollerdb.txt "$run/"
exe=$run/VPW64Deluxe
log=$(cd "$out" && pwd)/run.log; rm -f "$log"
(cd "$run" && VPW_TRACE_LOOKUP=1 WCW_AUTOBOOT="$rom" WCW_QUIT_AFTER="$secs" VPW_INPUT_SCRIPT="$script" \
    "$exe" > "$log" 2>&1) &
pid=$!
start=$(date +%s)
winid=""
for want in ${shots[@]+"${shots[@]}"}; do
    while [ $(( $(date +%s) - start )) -lt "$want" ]; do
        kill -0 $pid 2>/dev/null || { echo "game exited early; see $out/run.log" >&2; exit 1; }
        sleep 0.5
    done
    [ -n "$winid" ] || winid=$(swift tools/winid.swift VPW64Deluxe 2>/dev/null || true)
    if [ -z "$winid" ]; then echo "no window at ${want}s" >&2; else
        screencapture -x -o -l "$winid" "$out/shot-${want}s.png" && echo "shot-${want}s.png"
    fi
done
wait $pid || echo "game exit code $? (see $out/run.log)"
grep -E 'Failed to find function|vpw64dx|error|Error' "$out/run.log" | head -40 || true

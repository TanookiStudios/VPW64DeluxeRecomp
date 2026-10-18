#!/usr/bin/env bash
# Runs INSIDE the Linux test container (tools/linux_smoke.sh starts it). Boots the packaged Linux
# build on a virtual screen (Xvfb) with software Vulkan (Mesa lavapipe), presses Start at the
# title, and saves screenshots. No GPU or real display needed; slow, but it proves the program
# starts, renders and takes input on Linux.
set -euo pipefail
cd /pkg
export DISPLAY=:99
Xvfb :99 -screen 0 1280x960x24 >/tmp/xvfb.log 2>&1 &
sleep 2
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json
export SDL_AUDIODRIVER=dummy
export VPW_MUTE=1
touch portable.txt
secs=${SECS:-150}
if [ -n "${GDB:-}" ]; then
    WCW_AUTOBOOT=/rom/VPW64Deluxe.z64 WCW_QUIT_AFTER=$secs VPW_INPUT_SCRIPT="${SCRIPT:-60000:start;60400:}" \
        gdb -batch -ex "handle SIGSEGV stop" -ex run -ex "thread apply all bt 25" -ex "info registers rip" ./VPW64Deluxe > /out/gdb.log 2>&1
    exit 0
fi
WCW_AUTOBOOT=/rom/VPW64Deluxe.z64 WCW_QUIT_AFTER=$secs VPW_INPUT_SCRIPT="${SCRIPT:-60000:start;60400:}" \
    ./VPW64Deluxe > /out/run.log 2>&1 &
pid=$!
for t in ${SHOTS:-40 70 100 130}; do
    while [ $(( $(date +%s) - $(stat -c %Y /out/run.log) )) -ge 0 ] && [ "$(ps -o etimes= -p $pid 2>/dev/null | tr -d ' ')" != "" ] && [ "$(ps -o etimes= -p $pid | tr -d ' ')" -lt "$t" ]; do sleep 1; done
    kill -0 $pid 2>/dev/null || break
    import -window root /out/shot-${t}s.png 2>/dev/null && echo "shot-${t}s.png"
done
wait $pid || echo "exit code $?"

#!/usr/bin/env bash
# Boot test of the Linux release on this Mac: runs dist/VPW64Deluxe-Linux in an Ubuntu 22.04 x86-64
# container (Colima) on a virtual screen with software Vulkan, presses Start at the title, and writes
# screenshots and the log to work/linux-smoke/. Needs colima running and the ROM copy that
# tools/capture.sh uses. Nothing appears on screen.
set -euo pipefail
cd "$(dirname "$0")/.."
export DOCKER_CONFIG="$PWD/work/docker-config" DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
docker build --platform linux/amd64 -q -t vpw64dx-linux-smoke -f - tools/linux > /dev/null <<'EOF'
FROM --platform=linux/amd64 ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        xvfb mesa-vulkan-drivers libvulkan1 imagemagick libdbus-1-3 libgl1 libx11-6 libxext6 \
        libxrandr2 libxcursor1 libxi6 libxinerama1 libxss1 libxfixes3 libxkbcommon0 procps gdb \
    && rm -rf /var/lib/apt/lists/*
EOF
out=work/linux-smoke; rm -rf "$out"; mkdir -p "$out"
rm -rf work/linux-pkg && cp -R dist/VPW64Deluxe-Linux work/linux-pkg
docker run --rm --platform linux/amd64 \
    -v "$PWD/work/linux-pkg":/pkg -v "$HOME/Claude/vpw64-rom":/rom:ro -v "$PWD/$out":/out \
    -v "$PWD/tools/linux/smoke.sh":/smoke.sh:ro \
    -e GDB="${GDB:-}" -e SECS="${SECS:-150}" -e SHOTS="${SHOTS:-40 70 100 130}" -e SCRIPT="${SCRIPT:-60000:start;60400:}" \
    vpw64dx-linux-smoke bash /smoke.sh
ls "$out"

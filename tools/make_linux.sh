#!/usr/bin/env bash
# Build the Linux version (64-bit Intel/AMD) in an Ubuntu 22.04 container under Colima, and
# pack dist/VPW64Deluxe-Linux.tar.gz (copied to ~/Downloads).
# Needs: colima running (colima start --vm-type vz --vz-rosetta --arch aarch64), vendor/
# from setup.sh, RecompiledFuncs/ from tools/regen.sh, and your ROM (only to scan the
# package for ROM bytes). SDL2 and FreeType are built from source inside the container and
# linked in statically.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p work/docker-config; [ -f work/docker-config/config.json ] || echo '{}' > work/docker-config/config.json
export DOCKER_CONFIG="$PWD/work/docker-config" DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
docker build --platform linux/amd64 -q -t vpw64dx-linux-build tools/linux > /dev/null
docker run --rm --platform linux/amd64 -v "$PWD":/src vpw64dx-linux-build /src/tools/linux/build.sh > work/build-linux.log 2>&1 \
    || { grep -E "error|FAILED|undefined" work/build-linux.log | head -20 >&2; exit 1; }

OUT=dist/VPW64Deluxe-Linux
rm -rf "$OUT" "$OUT.tar.gz"; mkdir -p "$OUT"
cp build-linux/VPW64Deluxe "$OUT/"
cp -R assets "$OUT/assets"
cp recompcontrollerdb.txt LICENSE THIRD_PARTY_NOTICES.md "$OUT/"
cp assets/icon/vpw64dx-256.png "$OUT/vpw64dx.png"
cp tools/linux/vpw64dx.desktop tools/linux/README-Linux.txt tools/linux/install-shortcut.sh "$OUT/"
rm -rf "$OUT/assets/icon"   # the icon files are for building, not the program

file "$OUT/VPW64Deluxe" | grep -q "ELF 64-bit.*x86-64" || { echo "FAIL: not a 64-bit Intel/AMD program" >&2; exit 1; }
NEEDED=$(docker run --rm --platform linux/amd64 -v "$PWD/$OUT":/pkg vpw64dx-linux-build sh -c 'ldd /pkg/VPW64Deluxe' | awk '{print $1}')
echo "Libraries the program needs:"; echo "$NEEDED" | sed 's/^/  /'
BAD=$(echo "$NEEDED" | grep -v -E '^(linux-vdso\.so\.1|/lib64/ld-linux-x86-64\.so\.2|libc\.so\.6|libm\.so\.6|libdl\.so\.2|libpthread\.so\.0|librt\.so\.1|libstdc\+\+\.so\.6|libgcc_s\.so\.1|libz\.so\.1|libgtk-3\.so\.0|libgdk-3\.so\.0|libglib-2\.0\.so\.0|libgobject-2\.0\.so\.0|libgio-2\.0\.so\.0)$' || true)
[ -z "$BAD" ] || { echo "FAIL: unusual libraries needed:" >&2; echo "$BAD" >&2; exit 1; }
python3 -I tools/release_scan.py "$OUT"

tar -C dist -czf "$OUT.tar.gz" VPW64Deluxe-Linux
# Finished games always go to Downloads.
cp -f "$OUT.tar.gz" "$HOME/Downloads/"
echo "$HOME/Downloads/VPW64Deluxe-Linux.tar.gz"

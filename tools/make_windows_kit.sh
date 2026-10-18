#!/usr/bin/env bash
# Pack everything a Windows PC needs to build the Windows version into one zip:
# the repo's tracked files, the patched engines (vendor/, without their git history), the
# translated game code (RecompiledFuncs/ and rsp/*.cpp, made here from the ROM) and
# tools/windows/build.bat. No ROM goes in. Output: ~/Downloads/VPW64Deluxe-WindowsBuildKit.zip.
# The kit is carried to the PC by hand (AirDrop, a USB stick); it is never pushed anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d RecompiledFuncs ] && [ -f rsp/vpw2_audio.cpp ] || { echo "run tools/regen.sh first" >&2; exit 1; }
KIT=work/windows-kit/VPW64DeluxeBuildKit
rm -rf work/windows-kit; mkdir -p "$KIT"
git ls-files -z | rsync -a --files-from=- --from0 . "$KIT/"
rsync -a --exclude='.git' --exclude='build' --exclude='build-*' vendor "$KIT/"
rsync -a RecompiledFuncs "$KIT/"
mkdir -p "$KIT/rsp"; cp rsp/*.cpp "$KIT/rsp/"
cp tools/windows/build.bat "$KIT/build.bat"
# Line endings Windows tools are happy with for the double-click file.
perl -pi -e 's/\r?\n/\r\n/' "$KIT/build.bat"
python3 -I tools/release_scan.py --kit "$KIT"
( cd work/windows-kit && rm -f VPW64DeluxeBuildKit.zip && zip -qr VPW64DeluxeBuildKit.zip VPW64DeluxeBuildKit )
cp -f work/windows-kit/VPW64DeluxeBuildKit.zip "$HOME/Downloads/"
du -h "$HOME/Downloads/VPW64DeluxeBuildKit.zip" | cut -f1
echo "$HOME/Downloads/VPW64DeluxeBuildKit.zip"

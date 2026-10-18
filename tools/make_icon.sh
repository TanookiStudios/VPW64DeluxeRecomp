#!/bin/bash
# Rebuilds every icon file in assets/icon/ from tools/make_icon.swift.
# Needs: macOS (swift, iconutil) and python3.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=assets/icon
NAME=vpw64dx
mkdir -p "$OUT"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# macOS layout: rounded square with a margin.
swift tools/make_icon.swift "$OUT/icon-1024.png" 1024
mkdir "$TMP/AppIcon.iconset"
for s in 16 32 128 256 512; do
  swift tools/make_icon.swift "$TMP/AppIcon.iconset/icon_${s}x${s}.png" $s
  swift tools/make_icon.swift "$TMP/AppIcon.iconset/icon_${s}x${s}@2x.png" $((s * 2))
done
iconutil -c icns "$TMP/AppIcon.iconset" -o "$OUT/AppIcon.icns"

# Full-bleed layout for Windows, Linux, the launcher and the README.
for s in 16 24 32 48 64 128 256; do swift tools/make_icon.swift "$TMP/full-$s.png" $s --full; done
cp "$TMP/full-256.png" "$OUT/$NAME-256.png"

# Pack the seven sizes into one .ico (PNG-compressed entries).
python3 - "$TMP" "$OUT/$NAME.ico" <<'PY'
import struct, sys
tmp, out = sys.argv[1], sys.argv[2]
sizes = [16, 24, 32, 48, 64, 128, 256]
data = [open(f"{tmp}/full-{s}.png", "rb").read() for s in sizes]
head = struct.pack("<HHH", 0, 1, len(sizes))
offset = 6 + 16 * len(sizes)
entries = b""
for s, d in zip(sizes, data):
    entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(d), offset)
    offset += len(d)
open(out, "wb").write(head + entries + b"".join(data))
PY

printf '// Windows program icon (assets/icon/%s.ico): shown by Explorer and the taskbar.\n1 ICON "%s.ico"\n' "$NAME" "$NAME" > "$OUT/$NAME.rc"
echo "icons written to $OUT"

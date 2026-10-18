#!/usr/bin/env bash
# Build "VPW64 Deluxe.app" for every Mac (Apple chips and Intel, macOS 13+), signed with the
# Developer ID, and zip it as VPW64Deluxe-Mac.zip. Copies the zip (and the app) to ~/Downloads.
#
#   tools/make_app.sh            build + sign + zip
#   tools/make_app.sh --notarize also notarize with Apple and staple, then zip
#
# Needs: vendor/ from setup.sh, RecompiledFuncs/ from tools/regen.sh (your ROM is needed to
# make it, and again here to scan the finished app for ROM bytes), a "Developer ID
# Application" certificate (without one the app is signed ad-hoc and says so), and for
# --notarize the notarytool keychain profile "notarytool". The app contains no ROM data: the
# launcher asks for the ROM. SDL2 and FreeType are built from source (tools/build_deps.sh)
# and linked in statically, so nothing from Homebrew ends up in the app.
#
# The program inside is named VPW64Deluxe because on a Mac the settings folder is
# ~/Library/Application Support/<program name>/.
set -euo pipefail
cd "$(dirname "$0")/.."
NOTARIZE=0; [ "${1:-}" = "--notarize" ] && NOTARIZE=1
ID="Developer ID Application"
NAME="VPW64 Deluxe"
EXE=VPW64Deluxe
DEPS=$PWD/work/deps-mac
mkdir -p work dist
[ -f "$DEPS/lib/libSDL2.a" ] || tools/build_deps.sh "$DEPS" -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0

# Homebrew is hidden from CMake: its libraries are Apple-chip-only and other Macs do not have them.
cmake -S . -B build-mac -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0 \
    -DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew:/usr/local -DCMAKE_DISABLE_FIND_PACKAGE_PkgConfig=ON \
    -DSDL2_DIR="$DEPS/lib/cmake/SDL2" \
    -DFREETYPE_LIBRARY="$DEPS/lib/libfreetype.a" -DFREETYPE_INCLUDE_DIRS="$DEPS/include/freetype2" \
    -DRT64_WCW_TESTS=OFF > work/configure-mac.log 2>&1 || { tail -30 work/configure-mac.log >&2; exit 1; }
cmake --build build-mac --target VPW64Deluxe --parallel 8 > work/build-mac.log 2>&1 || { grep -E "error|Undefined|FAILED" work/build-mac.log | head -20 >&2; exit 1; }

APP="dist/$NAME.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
# Only the program goes in MacOS; everything it reads goes in Resources (code signing treats
# folders there as code). The program finds its files through the bundle's Resources folder.
cp "build-mac/$EXE" "$APP/Contents/MacOS/$EXE"
cp -R assets "$APP/Contents/Resources/assets"
rm -rf "$APP/Contents/Resources/assets/icon"   # the icon files are for building, not the program
cp recompcontrollerdb.txt "$APP/Contents/Resources/"
cp assets/icon/AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"
cp LICENSE THIRD_PARTY_NOTICES.md "$APP/Contents/Resources/"
VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || true)
VERSION=${VERSION:-$(tr -d '[:space:]' < VERSION)}
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>$NAME</string>
  <key>CFBundleDisplayName</key><string>$NAME</string>
  <key>CFBundleIdentifier</key><string>com.tanookistudios.vpw64deluxerecomp</string>
  <key>CFBundleExecutable</key><string>$EXE</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSApplicationCategoryType</key><string>public.app-category.sports-games</string>
</dict></plist>
PLIST

# Checks before signing: both chips, nothing but system libraries, no ROM data.
BIN="$APP/Contents/MacOS/$EXE"
ARCHS=$(lipo -archs "$BIN")
case "$ARCHS" in *arm64*x86_64*|*x86_64*arm64*) ;; *) echo "FAIL: app is not universal (got: $ARCHS)" >&2; exit 1;; esac
BAD=$(otool -L "$BIN" | grep '^[[:space:]]' | awk '{print $1}' | grep -v -E '^(/usr/lib/|/System/Library/)' || true)
if [ -n "$BAD" ]; then echo "FAIL: app needs libraries other Macs do not have:" >&2; echo "$BAD" >&2; exit 1; fi
python3 -I tools/release_scan.py "$APP"

if [ -n "$(security find-identity -v -p codesigning | grep "$ID")" ]; then
    codesign --force --deep --options runtime --timestamp --sign "$ID" "$APP" >/dev/null
    echo "Signed with: $ID"
else
    codesign --force --deep --sign - "$APP" >/dev/null
    echo "WARNING: no Developer ID certificate in the keychain; signed AD-HOC." >&2
    [ "$NOTARIZE" = 1 ] && { echo "FAIL: --notarize needs the Developer ID certificate" >&2; exit 1; }
fi
codesign --verify --deep --strict "$APP"

ZIP=dist/VPW64Deluxe-Mac.zip
rm -f "$ZIP"
if [ "$NOTARIZE" = 1 ]; then
    ditto -c -k --keepParent "$APP" "$ZIP"
    xcrun notarytool submit "$ZIP" --keychain-profile notarytool --wait
    xcrun stapler staple "$APP"
    rm -f "$ZIP"
    ditto -c -k --keepParent "$APP" "$ZIP"
    spctl --assess --type execute --verbose "$APP"
else
    ditto -c -k --keepParent "$APP" "$ZIP"
    echo "NOT notarized: other Macs will show a Gatekeeper warning. Run with --notarize for release."
fi

# Finished games always go to Downloads.
cp -f "$ZIP" "$HOME/Downloads/"
rm -rf "$HOME/Downloads/$NAME.app"
cp -R "$APP" "$HOME/Downloads/"
echo "$HOME/Downloads/VPW64Deluxe-Mac.zip"
echo "$HOME/Downloads/$NAME.app"

#!/bin/sh
# Adds VPW64 Deluxe to the application menu for this user only.
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/256x256/apps"
cp "$here/vpw64dx.png" "$HOME/.local/share/icons/hicolor/256x256/apps/vpw64dx.png"
sed "s|^Exec=.*|Exec=\"$here/VPW64Deluxe\"|" "$here/vpw64dx.desktop" > "$HOME/.local/share/applications/vpw64dx.desktop"
echo "Added VPW64 Deluxe to your application menu."

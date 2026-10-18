#!/usr/bin/env bash
# Build the two libraries the program needs that are not in the engine checkouts, SDL2 and
# FreeType, from source as STATIC libraries, so a release carries no Homebrew or distro
# library the player may not have. Output goes to <prefix>; pass it to CMake as
#   -DSDL2_DIR=<prefix>/lib/cmake/SDL2 -DFREETYPE_LIBRARY=<prefix>/lib/libfreetype.a
#   -DFREETYPE_INCLUDE_DIRS=<prefix>/include/freetype2
#
#   tools/build_deps.sh <prefix> [extra cmake args, e.g. -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"]
set -euo pipefail
cd "$(dirname "$0")/.."
PREFIX=$(mkdir -p "$1" && cd "$1" && pwd); shift
SDL2_VER=2.30.11
FT_VER=2-13-3
SRC=$PREFIX-src; mkdir -p "$SRC"   # one source tree per target (the Linux container cannot overwrite the Mac one)
fetch() { [ -f "$SRC/$2" ] || curl -fsSL "$1" -o "$SRC/$2"; }
fetch "https://github.com/libsdl-org/SDL/releases/download/release-$SDL2_VER/SDL2-$SDL2_VER.tar.gz" sdl2.tar.gz
fetch "https://github.com/freetype/freetype/archive/refs/tags/VER-$FT_VER.tar.gz" freetype.tar.gz
rm -rf "$SRC/SDL2-$SDL2_VER" "$SRC/freetype-VER-$FT_VER"
tar -xzf "$SRC/sdl2.tar.gz" -C "$SRC" --exclude="*/android-project*"   # (symbolic links the container mount refuses)
tar -xzf "$SRC/freetype.tar.gz" -C "$SRC"

cmake -S "$SRC/SDL2-$SDL2_VER" -B "$SRC/SDL2-$SDL2_VER/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" -DSDL_SHARED=OFF -DSDL_STATIC=ON -DSDL_TEST=OFF -DSDL_STATIC_PIC=ON "$@" > /dev/null
cmake --build "$SRC/SDL2-$SDL2_VER/build" --parallel 8 > /dev/null
cmake --install "$SRC/SDL2-$SDL2_VER/build" > /dev/null

# FreeType with none of its optional libraries (zlib, png, brotli, harfbuzz, bzip2): the UI
# only renders the two bundled TrueType fonts.
cmake -S "$SRC/freetype-VER-$FT_VER" -B "$SRC/freetype-VER-$FT_VER/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DFT_DISABLE_ZLIB=ON -DFT_DISABLE_BZIP2=ON -DFT_DISABLE_PNG=ON -DFT_DISABLE_HARFBUZZ=ON -DFT_DISABLE_BROTLI=ON "$@" > /dev/null
cmake --build "$SRC/freetype-VER-$FT_VER/build" --parallel 8 > /dev/null
cmake --install "$SRC/freetype-VER-$FT_VER/build" > /dev/null
ls "$PREFIX/lib/libSDL2.a" "$PREFIX/lib/libfreetype.a" > /dev/null
echo "deps in $PREFIX"

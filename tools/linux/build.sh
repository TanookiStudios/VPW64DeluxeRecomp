#!/usr/bin/env bash
# Runs INSIDE the build container (tools/make_linux.sh starts it). Builds SDL2 and FreeType
# as static libraries, then the game into build-linux/.
set -euo pipefail
cd /src
# Static SDL2/FreeType so the player needs no extra packages (the only libraries left are
# the ones every desktop has: libc, libstdc++, libm, X11/Wayland bits SDL opens at run time).
[ -f work/deps-linux/lib/libSDL2.a ] || tools/build_deps.sh work/deps-linux -DCMAKE_C_COMPILER=clang-15 -DCMAKE_CXX_COMPILER=clang++-15
cmake -S . -B build-linux -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=clang-15 -DCMAKE_CXX_COMPILER=clang++-15 -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld-15" \
    -DSDL2_DIR=/src/work/deps-linux/lib/cmake/SDL2 \
    -DFREETYPE_LIBRARY=/src/work/deps-linux/lib/libfreetype.a -DFREETYPE_INCLUDE_DIRS=/src/work/deps-linux/include/freetype2 \
    -DRT64_WCW_TESTS=OFF
cmake --build build-linux --target VPW64Deluxe --parallel "$(nproc)"

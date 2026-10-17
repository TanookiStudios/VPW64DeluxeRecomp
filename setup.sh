#!/usr/bin/env bash
# Fetch the engines into vendor/ at the versions this port was tested with, then apply our
# local changes to them (patches/). vendor/ is not committed: anything changed there must
# live in patches/.
set -euo pipefail
cd "$(dirname "$0")"
N64RECOMP_COMMIT=ffb39cdad1da5de07eaaa48bd1db4a89a7986771            # N64Recomp/N64Recomp
N64MODERNRUNTIME_COMMIT=69acee8ad23586d96d46910af8ee367ab8b3c2ba     # jessetbh/N64ModernRuntime, branch wcw
RECOMPFRONTEND_COMMIT=20292e53512dd3195e72356c574b451351bcdb9f       # jessetbh/RecompFrontend, branch wcw
RT64_COMMIT=0e55be1279befb6d9bebfa6841595f4b256db828                 # jessetbh/rt64, branch wcw
fetch() {  # fetch <url> <dir> <commit>
    if [ ! -d "vendor/$2/.git" ]; then
        git clone -q "$1" "vendor/$2"
        git -C "vendor/$2" checkout -q "$3"
        git -C "vendor/$2" submodule update -q --init --recursive
    fi
}
fetch https://github.com/N64Recomp/N64Recomp.git N64Recomp "$N64RECOMP_COMMIT"
fetch https://github.com/jessetbh/N64ModernRuntime.git N64ModernRuntime "$N64MODERNRUNTIME_COMMIT"
fetch https://github.com/jessetbh/RecompFrontend.git RecompFrontend "$RECOMPFRONTEND_COMMIT"
fetch https://github.com/jessetbh/rt64.git rt64 "$RT64_COMMIT"
apply() {  # apply <dir> <patch>
    if git -C "vendor/$1" apply --check "../../$2" 2>/dev/null; then
        git -C "vendor/$1" apply "../../$2" && echo "applied $(basename "$2")"
    else
        echo "$(basename "$2") already applied (or does not fit: check vendor/$1)"
    fi
}
for p in patches/n64recomp-*.patch; do [ -f "$p" ] && apply N64Recomp "$p"; done
for p in patches/rt64-*.patch; do [ -f "$p" ] && apply rt64 "$p"; done
for p in patches/runtime-*.patch; do [ -f "$p" ] && apply N64ModernRuntime "$p"; done
for p in patches/runtime-lib-*.patch; do [ -f "$p" ] && apply N64ModernRuntime/N64Recomp "$p"; done   # the runtime's own copy of the recompiler headers
for p in patches/frontend-*.patch; do [ -f "$p" ] && apply RecompFrontend "$p"; done
# The recompiler itself (run once per ROM; its output is never committed).
if [ ! -x N64Recomp ]; then
    cmake -S vendor/N64Recomp -B vendor/N64Recomp/build -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
    cmake --build vendor/N64Recomp/build --target N64RecompCLI RSPRecomp
    cp vendor/N64Recomp/build/N64Recomp vendor/N64Recomp/build/RSPRecomp .
fi
[ -f rom/vpw64deluxe.z64 ] || echo "Put your VPW64 Deluxe .z64 at rom/vpw64deluxe.z64 (SHA-1 2ad9eb023a93f74c4f77e313a8bd583cec0c53d9)"
ln -sf rom/vpw64deluxe.z64 vpw2.z64   # the symbol tools (from VPW2Recomp) read this name
true

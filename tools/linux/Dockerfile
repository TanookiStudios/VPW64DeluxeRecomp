# Build machine for the Linux release: Ubuntu 22.04 (glibc 2.35), so the program runs on
# Linux desktops from 2022 on. Players need none of this; it only builds.
FROM --platform=linux/amd64 ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git build-essential ninja-build pkg-config python3-pip file \
        clang-15 lld-15 \
        libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxinerama-dev libxss-dev \
        libxfixes-dev libxtst-dev libxkbcommon-dev libwayland-dev wayland-protocols \
        libegl1-mesa-dev libgl1-mesa-dev libgles2-mesa-dev libdecor-0-dev \
        libasound2-dev libpulse-dev libdbus-1-dev libudev-dev libdrm-dev libgbm-dev \
        libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir cmake==3.31.6
ENV CC=clang-15 CXX=clang++-15

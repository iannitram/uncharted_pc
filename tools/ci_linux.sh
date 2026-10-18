#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Linux build and test run, as CI does it (.github/workflows/ci.yml): the GPU library, bb-probe,
# the C test programs, the C++ GPU tests (on lavapipe, Mesa's software Vulkan) and the Python
# tests. Needs no game files and no GPU.
#
#   bash tools/ci_linux.sh --deps   # Ubuntu 24.04: install packages, build the missing ones
#   bash tools/ci_linux.sh          # build and test
#
# Ubuntu 24.04 lacks SDL3 and a recent enough Vulkan-Headers, robin-map and VMA;
# --deps builds the pinned versions below into /usr/local (sudo when not root).
set -euo pipefail
cd -- "$(dirname -- "$0")/.."

SDL_TAG=release-3.2.24
VULKAN_HEADERS_REV=c46850864f4661461b0f6cb9922c058ffea4915e   # Vulkan-Docs 1.4.365
ROBIN_MAP_REV=91362aab8f2c63ef90bf7c21fb2c3283ded5ae48
VMA_REV=bfb2ca99e1e7e9684dc06546b552ee3eff4b10aa

sudo_if_needed() { if [[ $(id -u) == 0 ]]; then "$@"; else sudo "$@"; fi; }

fetch_rev() { # url rev dir
    git init -q "$3"
    git -C "$3" fetch -q --depth 1 "$1" "$2"
    git -C "$3" checkout -q FETCH_HEAD
}

if [[ ${1:-} == --deps ]]; then
    sudo_if_needed apt-get update -q
    sudo_if_needed apt-get install -y -q --no-install-recommends \
        build-essential clang cmake ninja-build pkg-config python3 git ca-certificates \
        libvulkan-dev mesa-vulkan-drivers glslang-tools \
        libboost-dev libfmt-dev libzydis-dev libxxhash-dev libx11-dev \
        libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev libxss-dev libxkbcommon-dev \
        libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libswresample-dev
    deps=$(mktemp -d)
    git clone -q --depth 1 -b "$SDL_TAG" https://github.com/libsdl-org/SDL.git "$deps/sdl"
    cmake -S "$deps/sdl" -B "$deps/sdl/b" -G Ninja -DCMAKE_BUILD_TYPE=Release -DSDL_TESTS=OFF \
        -DSDL_EXAMPLES=OFF >/dev/null
    ninja -C "$deps/sdl/b" >/dev/null
    sudo_if_needed ninja -C "$deps/sdl/b" install >/dev/null
    fetch_rev https://github.com/KhronosGroup/Vulkan-Headers.git "$VULKAN_HEADERS_REV" "$deps/vkh"
    fetch_rev https://github.com/Tessil/robin-map.git "$ROBIN_MAP_REV" "$deps/robin"
    fetch_rev https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator.git "$VMA_REV" "$deps/vma"
    for d in vkh robin vma; do
        cmake -S "$deps/$d" -B "$deps/$d/b" >/dev/null
        sudo_if_needed cmake --install "$deps/$d/b" >/dev/null
    done
    sudo_if_needed ldconfig
    rm -rf "$deps"
    exit 0
fi

# Submodules and this port's FSR-Vulkan patches, as build.sh does.
if [[ ! -f gpu/third_party/fsr-vulkan/CMakeLists.txt || ! -f gpu/third_party/imgui/imgui.h ]]; then
    git submodule update --init --recursive
fi
for patch in gpu/patches/fsr-vulkan/*.patch; do
    if ! git -C gpu/third_party/fsr-vulkan apply --reverse --check "$PWD/$patch" 2>/dev/null; then
        git -C gpu/third_party/fsr-vulkan apply "$PWD/$patch"
    fi
done

echo '== GPU library'
cmake -S gpu -B out/gpu -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBB_PGO=off -DBB_LTO=OFF \
    -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -Wno-dev >/dev/null
if ! ninja -C out/gpu bbgpu > out/gpu-build.log 2>&1; then
    grep -v '^\[' out/gpu-build.log | tail -60 >&2
    exit 1
fi

echo '== bb-probe and the C tests'
read -r -a includes <<< "$(pkg-config --cflags vulkan sdl3)"
read -r -a libraries <<< "$(pkg-config --libs vulkan sdl3)"
gpu=(-Lout/gpu -lbbgpu -Wl,-rpath,"$PWD/out/gpu" -rdynamic)
runtime=(src/runtime*.c)
CC=${CC:-gcc}
mkdir -p out/atrac9
for source in third_party/LibAtrac9/C/src/*.c; do
    "$CC" -std=c99 -O2 -g -w -c "$source" -o "out/atrac9/$(basename "${source%.c}").o"
done
ar rcs out/libatrac9.a out/atrac9/*.o
warn=(-std=c11 -O2 -g -Wall -Wextra -Werror -pthread)
"$CC" "${warn[@]}" -no-pie "${includes[@]}" -I. -Isrc src/probe.c "${runtime[@]}" src/vulkan_smoke.c \
    out/libatrac9.a -lm "${gpu[@]}" "${libraries[@]}" -o out/bb-probe
"$CC" "${warn[@]}" "${includes[@]}" -I. -Isrc tests/test_pad.c "${libraries[@]}" -o out/pad-test
"$CC" "${warn[@]}" -I. -Isrc tests/test_runtime.c "${runtime[@]}" out/libatrac9.a -lm "${gpu[@]}" \
    "${libraries[@]}" -o out/runtime-test
"$CC" "${warn[@]}" -Isrc tests/test_file_mods.c -o out/file-mods-test
"$CC" "${warn[@]}" -I. -Isrc tests/test_sema.c "${runtime[@]}" out/libatrac9.a -lm "${gpu[@]}" \
    "${libraries[@]}" -o out/sema-test
"$CC" -std=c11 -D_GNU_SOURCE -O2 -g -Wall -Wextra -Werror -I. -Isrc tests/test_content.c \
    src/runtime_content.c -o out/content-test
for test in pad runtime file-mods sema content; do
    echo "-- $test-test"
    out/$test-test
done

echo '== C++ GPU tests (lavapipe)'
gpu_tests=(motion-history-test motion-shader-test ui-composition-test scene-resolution-test
           taa-shader-test camera-motion-test upscaler-support-test)
ninja -C out/gpu "${gpu_tests[@]}" > out/gpu-tests-build.log 2>&1 ||
    { grep -v '^\[' out/gpu-tests-build.log | tail -60 >&2; exit 1; }
for test in "${gpu_tests[@]}"; do
    echo "-- $test"
    if ! out/gpu/$test > "out/$test.log" 2>&1; then
        tail -40 "out/$test.log" >&2
        exit 1
    fi
    grep -E 'PASS' "out/$test.log" | tail -1 || true
done

echo '== Python tests'
python3 -m unittest discover -s tests -p 'test_*.py'

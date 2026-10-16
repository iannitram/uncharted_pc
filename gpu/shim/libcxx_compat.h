// SPDX-License-Identifier: GPL-2.0-or-later
// bbport (Windows): current MSYS2 clang with libc++ no longer includes common standard
// headers transitively. The vendored code (FidelityFX in FSR-Vulkan, sirit, shadPS4) relied on
// that, and stops on std::abort, placement new, log2, swprintf_s, MSVC's _countof and
// similar. This header is force-included into every C++ file on Windows (CMakeLists.txt),
// so they build unchanged. The _countof guard keeps the C runtime's definition where it has
// one.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <memory>
#include <new>
#include <string>
#include <utility>
#ifndef _countof
#define _countof(array) (sizeof(array) / sizeof((array)[0]))
#endif

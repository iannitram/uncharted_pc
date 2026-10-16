// SPDX-License-Identifier: GPL-2.0-or-later
// bbport (Windows): the AMD FidelityFX sources in FSR-Vulkan were written against MSVC and
// rely on headers that older libc++ pulled in transitively: placement new (<new>), log2
// (<cmath>), swprintf_s (<cwchar>) and MSVC's _countof. Current MSYS2 clang and libc++ no
// longer do, so this header is force-included into the FSR-Vulkan targets only
// (CMakeLists.txt). The _countof guard keeps the C runtime's definition where it has one.
#pragma once
#ifdef __cplusplus
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <new>
#else
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#endif
#ifndef _countof
#define _countof(array) (sizeof(array) / sizeof((array)[0]))
#endif

// SPDX-License-Identifier: GPL-2.0-or-later
// bbport (Windows): the AMD FidelityFX sources in FSR-Vulkan use MSVC's _countof. With
// current MSYS2 clang and libc++ it is no longer declared by the headers they include, so
// this fallback is force-included into that subdirectory (CMakeLists.txt). The guard keeps
// the C runtime's own definition wherever <stdlib.h> provides one.
#pragma once
#ifndef _countof
#define _countof(array) (sizeof(array) / sizeof((array)[0]))
#endif

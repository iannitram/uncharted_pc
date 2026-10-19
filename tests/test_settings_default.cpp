// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: anti-aliasing defaults to Off on a driver FSR 3.1 has not been checked on (noise on
// RADV PHOENIX, 2026-10-19); the player's ini or BB_UPSCALER choice is kept.
#include <cstdio>
#include <cstdlib>

#include "gpu/shim/bbport_settings.h"

using namespace BbSettings;

static int failures = 0;
static void Check(bool ok, const char* what) {
    std::printf("%s: %s\n", ok ? "ok" : "FAIL", what);
    if (!ok) ++failures;
}

int main() {
    Check(DriverDefaultUpscaler(UpscalerFsr3, false, false) == UpscalerOff,
          "default FSR 3.1 on an unchecked driver becomes Off");
    Check(DriverDefaultUpscaler(UpscalerFsr3, false, true) == UpscalerFsr3,
          "default FSR 3.1 on a checked driver stays on");
    Check(DriverDefaultUpscaler(UpscalerFsr3, true, false) == UpscalerFsr3,
          "FSR 3.1 the player chose stays on an unchecked driver");
    Check(DriverDefaultUpscaler(UpscalerFsr4, false, false) == UpscalerFsr4,
          "another upscaler is not touched");
    Check(DriverDefaultUpscaler(UpscalerOff, false, false) == UpscalerOff, "Off stays Off");

    // Through Load(): no ini, no BB_UPSCALER -> not chosen; BB_UPSCALER=fsr3 -> chosen
    setenv("BB_CONFIG", "/nonexistent/bbport-test.ini", 1);
    unsetenv("BB_UPSCALER");
    Load();
    Check(!Get().upscaler_chosen && Get().upscaler == UpscalerFsr3, "no ini: FSR 3.1, not chosen");
    ConfigureDriverDefault(3 /* VK_DRIVER_ID_MESA_RADV */, "test GPU, driver test");
    Check(Get().upscaler == UpscalerOff && Get().startup_upscaler == UpscalerOff,
          "an unchecked driver turns the default Off (and the startup value)");
    Get().upscaler = UpscalerFsr3;
    Get().startup_upscaler = UpscalerFsr3;
    setenv("BB_UPSCALER", "fsr3", 1);
    Load();
    ConfigureDriverDefault(3, "test GPU, driver test");
    Check(Get().upscaler_chosen && Get().upscaler == UpscalerFsr3, "BB_UPSCALER=fsr3 is kept");
    return failures ? 1 : 0;
}

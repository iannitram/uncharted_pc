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
    // Measured devices, by name (driver ids can't tell AMD GPUs apart)
    Check(FsrDeviceValidated("AMD Ryzen Z1 Extreme (RADV PHOENIX), driver 26.1.99"), "PHOENIX is on the list");
    Check(FsrDeviceValidated("AMD Radeon 8060S Graphics (RADV STRIX_HALO), driver 26.1.99"), "STRIX_HALO is on the list");
    Check(!FsrDeviceValidated("AMD Radeon 610M (RADV RAPHAEL_MENDOCINO), driver 26.2.4"), "an unmeasured AMD GPU is not");
    Check(!FsrDeviceValidated(nullptr), "no name: not on the list");
    Get().upscaler = UpscalerFsr3;
    Get().upscaler_chosen = false;
    ConfigureDriverDefault(3, "AMD Ryzen Z1 Extreme (RADV PHOENIX), driver 26.1.99");
    Check(Get().upscaler == UpscalerFsr3, "PHOENIX keeps the FSR 3.1 default");
    ConfigureDriverDefault(3, "AMD Radeon 610M (RADV RAPHAEL_MENDOCINO), driver 26.2.4");
    Check(Get().upscaler == UpscalerOff, "an unmeasured AMD GPU still defaults to Off");
    return failures ? 1 : 0;
}

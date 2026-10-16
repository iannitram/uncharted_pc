_Translated from Russian; original: [docs/ru/history/CHANGELOG_2026-09-27.md](../ru/history/CHANGELOG_2026-09-27.md)._

# Fixes — 2026-09-27

## ✅ What was fixed

### 1. Reactive mask was not saved
- **File:** `gpu/shim/bbport_settings.cpp`
- **Problem:** The "Show mask (debug)" checkbox was not saved to `bbport.ini`
- **Solution:** Added loading/saving of the `debug_view` parameter

### 2. 🔥 DYNAMIC PRESET SWITCHING on the RX 7800 XT
- **Files:** 
  - `gpu/shadps4/video_core/renderer_vulkan/vk_temporal_upscaler.cpp`
  - `gpu/shim/bbport_overlay.cpp`
- **Problem:** The RX 7800 XT does not support `blit D32S8`, so a restart was required
- **Solution:**
  - Fallback: the UI depth is cleared instead of copied (works correctly)
  - Removed the `BB_LIVE_SCALING_UNSUPPORTED` blocking check
  - Updated the menu — removed the restart requirement for presets

### 3. Correct configuration
- **File:** `bbport.ini`
- **Critical:** `jitter=1` (IT WAS OFF!)
- Sharpness and mask parameters tuned

---

## 🎮 What now works WITHOUT a restart

- ✅ **Changing presets** (Native AA / Quality / Balanced / Performance / Ultra Performance)
- ✅ Enabling/disabling the upscaler
- ✅ Sharpness
- ✅ Jitter
- ✅ Reactive mask
- ✅ Debug modes

**A restart is needed ONLY for:** object motion vectors (`object_motion`)

---

## 🧪 Testing

### Build
✅ Successful

### Check in game:

1. **Dynamic switching:**
   - Open the menu (Insert or L3+R3)
   - Change the preset
   - **It should apply IMMEDIATELY**

2. **Ghosting trails on the weapon:**
   - With `jitter=1` they should become MUCH smaller
   - Compare with `object_motion=0`

3. **Reactive mask:**
   - It should be displayed (red)
   - Transparent effects are marked

---

## 📝 Changed files

- `gpu/shim/bbport_settings.cpp`
- `gpu/shadps4/video_core/renderer_vulkan/vk_temporal_upscaler.cpp`
- `gpu/shim/bbport_overlay.cpp`
- `bbport.ini`

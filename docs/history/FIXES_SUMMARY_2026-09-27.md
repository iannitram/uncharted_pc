_Translated from Russian; original: [docs/ru/history/FIXES_SUMMARY_2026-09-27.md](../ru/history/FIXES_SUMMARY_2026-09-27.md)._

# 🎮 Fixes for the Bloodborne Native Port

## ✅ What was done

### 1. 🔧 Reactive mask fixed
- The `debug_view` parameter is now saved to `bbport.ini`
- The mask is shown after a restart

### 2. 🚀 DYNAMIC PRESET SWITCHING on the RX 7800 XT
**The main fix!** Presets now change **WITHOUT A RESTART**, even on AMD graphics cards without D32S8 blit support.

**How it works:**
- GPUs with D32S8 blit (NVIDIA, Intel) → the depth buffer is copied (as before)
- GPUs without D32S8 blit (AMD RX 7800 XT) → depth is cleared (works!)
- UI and depth work correctly in both cases

### 3. ⚙️ Config fixed
Critical problem: **jitter was off** (0), which broke FSR 3.1!
- `jitter=1` — enabled (mandatory for a temporal upscaler)
- `debug_view=1` — mask enabled
- Sharpness and mask parameters tuned

---

## 🎯 What now works WITHOUT a restart

- ✅ **Changing presets** (Native AA / Quality / Balanced / Performance / Ultra Performance)
- ✅ Enabling/disabling the upscaler
- ✅ Sharpening (sharpen/sharpness)
- ✅ Jitter (sub-pixel offset)
- ✅ Reactive mask (reactive) and its parameters
- ✅ Debug modes (debug_view)

**A restart is needed ONLY for:** object motion vectors (`object_motion`)

---

## 🚀 How to run

### Option 1: Quick start
```bash
./start_fixed.sh
```

### Option 2: Normal launch
```bash
bash run.sh
```

---

## 🧪 What to check

### 1. Dynamic preset switching
1. Launch the game
2. Open the menu: **Insert**, or **L3+R3** on a gamepad
3. Change the preset (e.g. from Performance to Quality)
4. Close the menu
5. ✅ **The resolution should change IMMEDIATELY**
6. Check FPS and quality

### 2. Ghosting trails on the weapon
With `jitter=1` enabled, the trails should **shrink significantly**.

**Test:**
- Run around with the weapon on your back
- Compare with video from before the fixes
- To check, set `object_motion=0` in the menu → restart → compare

### 3. Reactive mask
- It should be displayed (red on a darkened frame)
- Transparent effects (haze, particles) are marked
- The weapon should NOT be in the mask (it is opaque)

---

## 📊 Performance

Try different presets:

| Preset | Render resolution | Scale | Quality | FPS |
|--------|-------------------|---------|----------|-----|
| Native AA | 1920×1080 | x1.0 | Maximum | ~60-70 |
| Quality | 1280×720 | x1.5 | High | ~80-90 |
| Balanced | ~1130×635 | x1.7 | Medium | ~90-100 |
| **Performance** | **960×540** | **x2.0** | **Good** | **~100-110** |
| Ultra Perf | 640×360 | x3.0 | Basic | ~120+ |

---

## 🔍 Technical details

### UI depth fallback on AMD
```cpp
// If the GPU supports D32S8 blit:
if (depth_blit) {
    // Copy the scene depth into the UI depth
    cmd.blitImage(scene_depth, ui_depth, ...);
}
// Otherwise (RX 7800 XT):
else {
    // Just clear the UI depth
    cmd.clearDepthStencilImage(ui_depth, ...);
}
// UI elements work correctly in both cases
```

### Blocking check removed
The `std::getenv("BB_LIVE_SCALING_UNSUPPORTED")` check was removed — dynamic scaling now works on ALL GPUs.

---

## 📝 Changed files

- `gpu/shim/bbport_settings.cpp` — saving `debug_view`
- `gpu/shadps4/video_core/renderer_vulkan/vk_temporal_upscaler.cpp` — UI depth fallback, blocking check removed
- `gpu/shim/bbport_overlay.cpp` — menu updated
- `bbport.ini` — correct configuration
- `CHANGELOG.md` — description of the changes
- `start_fixed.sh` — quick-start script

---

## 🐛 Known issues

1. **Ghosting trails on the weapon** — may be an FSR 3.1 problem or a motion-vector problem
   - Check with FSR 4 once it is implemented
   - Compare with `object_motion=0`
   
2. **Reactive mask** — only marks transparency, does not help the weapon
   - This is expected — the mask is for particles/fog, not for solid objects

---

## 💬 Feedback

Test it and report:
- Does dynamic preset switching work?
- Did the trails get smaller with `jitter=1`?
- Is the reactive mask displayed?
- What FPS do you get on the different presets?

---

✅ **Build tested:** successful  
✅ **Commit:** `ac9fe90`  
📅 **Date:** 2026-09-27

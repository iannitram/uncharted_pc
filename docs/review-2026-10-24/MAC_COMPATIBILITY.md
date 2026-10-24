# Mac compatibility bundle feasibility

Follow-up assessment, 2026-10-24. This approach has not been tested on a Mac.

A Mac app bundling the Windows release with a macOS-compatible Wine runtime is plausible. Proton targets Linux and is not a drop-in macOS runtime. The proposed path is Windows Uncharted PC -> Wine Vulkan interface -> MoltenVK -> Metal. Apple Silicon also requires compatible x86-64 translation, typically Rosetta 2 for supported host code. Its compatibility with the project's dynamically mapped and patched guest code must be demonstrated.

Test the existing build in a maintained CrossOver/Wine environment first. Check image mappings, guest TLS, required instructions, exceptions and threading before testing the Vulkan renderer. Inventory required Vulkan features and extensions against MoltenVK; a Vulkan version label alone cannot establish compatibility. Reaching gameplay is a separate gate from device creation.

Start with AA/frame generation disabled. Verify U1/U2/U3 gameplay, audio, controls, save/load, executable switching and restart on physical hardware. Run cold/warm shader checks and 30-minute soaks with frame-time and memory measurements. Evaluate FSR independently. NVIDIA DLSS is unavailable on Apple GPUs. Keep Intel and Apple Silicon results separate.

If these gates pass, scope an experimental app with a private Wine prefix, persistent saves/configuration, an update-recovery path, dependency/license manifest and signing/notarization checks. Confirm redistribution rights for the selected runtime; do not assume CrossOver or Apple translation components can be bundled freely. Include no game files.

Roadmap: in window 2, deliver a reproducible configuration, startup logs, feature inventory and architecture-specific go/no-go report. If successful, consider an experimental compatibility bundle in window 4. Native Darwin runtime development remains a separate workstream. This is a candidate route, not a promise of playable performance.

_Translated from Russian; original: [docs/ru/history/object_motion_notes_2026-09-26.md](../ru/history/object_motion_notes_2026-09-26.md)._

The first version of object motion vectors is built, the game launched, and there are no errors at startup. But I have not checked it in the game itself yet: the G-buffer shaders with the new code are compiled only when a level loads, so the main check is still ahead.

How it works:
- The vertex shader of every draw into the G-buffer saves the final vertex positions and reads the positions of the same vertices from the previous frame.
- The pixel shader writes the difference into an additional G-buffer target.
- Where an object moved, FSR gets this vector; everywhere else, the camera vector.
- Positions are saved only for moving draws: those whose vertex shader constants (object matrix, bones) changed. Static geometry costs no memory.
- This covers any animation computed by the vertex shader: skinning, weapons, cloth, enemies.

Please load into the game and write "ready". I will check the log: how many draws are moving and how many of them found previous-frame positions. Then run around with the saw on your back. For comparison, I can turn object vectors off on the fly, leaving only camera vectors.

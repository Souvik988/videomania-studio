# Google Flow prompts: <project id>

For the user to generate in Google Flow (prompt-sheet mode). Settings for every clip: **model Omni
Flash** (never Veo 3.1) · **aspect <9:16 | 16:9>** · duration as listed. Save each download with the
file name shown, unchanged (no cropping, no edits), and give the files back to the session.

Shared identity sentence (paste into every clip with this person, word for word):
"<…>"

---

## G1 · <beat name> · <t start–t end s in the edit> · <4 | 6 | 8> s · save as `G1.mp4`
**Why this beat needs real footage:** <one line>

**Prompt (copy all):**
```
<shot size and subject using the identity sentence, the one action, the setting, camera described as
framing (never "static" or "tripod"), lens, light, colour, "photoreal", where to keep clean space>
```
**Avoid:** text, letters, signage writing, logos, extra fingers, distorted hands, morphing face, flicker, cuts

---
(repeat per clip)

## After generating
Put the files in `projects/<id>/assets/flow/incoming/` (or attach them) and say "clips ready".
The session ingests them with `flow_ingest.py --file …`, checks every frame and continues the build.

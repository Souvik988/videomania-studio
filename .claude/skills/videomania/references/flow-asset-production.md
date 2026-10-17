# Flow asset production — generated clips and stills for an edit

The installed `google-flow` MCP server (Souvik988/google-flow-mcp, user scope, CDP mode, **watermark
removal ON**) drives Google Flow in the user's signed-in profile. These rules are the
user's standing instructions and override the server's own defaults.

## Non-negotiable user rules
1. **Video model: Omni Flash only** (server enum `gemini-omni-flash`; Flow's model menu may label
   it "Omni Flash" or "Gemini Omni Flash 1.1"). **Never Veo 3.1** (fast or quality). If Flow's
   model menu does not offer Omni Flash, stop and tell the user — never substitute.
2. **Aspect ratio: 16:9 or 9:16, as the user says for that request.** If the user did not say, ask
   before planning shots. All clips in one edit use the same ratio unless the user says otherwise.
3. **One explicit approval per generation.** The user may approve several sheet IDs in one message
   ("approve G1, G3"); each approved ID = exactly one "Start generation" click. No retries, no
   extra takes, no batches beyond what was approved. A previous approval never carries over.
4. **Server code stays unmodified.** The server fills Flow's composer; the single generation click
   is a real mouse click made only after approval.
5. **Deliver Flow plates without the sparkle badge** (user instruction 2026-10-17). Engine finishing
   runs `auto`: alpha-unblend, then OpenCV inpaint, then ffmpeg delogo. Verify it on a cropped corner
   frame — unblend has been observed to register 0.0 on Omni Flash and delogo smears textured
   backgrounds, so check the result rather than trusting the flag. If a soft ghost remains, reframe or
   cover it in the composition and say so. Always label AI footage in the delivery notes.
6. **One generation at a time** (Flow's composer is a single shared surface).

Images (stills) use Flow's image mode (default model shown in the panel, e.g. Nano Banana 2.1);
the Omni-only rule is for video. Same approval rule applies.

## The generation sheet (show this before anything is generated)

Write `storyboard/generation_sheet.md` and present it to the user:

| ID | beat / t | purpose in the edit | type | model | aspect | dur | prompt | avoid | credits | status |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | S02 3.3–7.3 s | atmosphere behind the "wait" list | video | Omni Flash | 9:16 | 6 s | … | text, logos, … | read from panel | pending |

- Generate only what code can't make (people, nature, physical objects, light, cities, weather).
  Text, UI, numbers, charts and logos are always coded, never generated.
- Duration = on-screen time + 0.5–1 s handle, rounded up to 4 / 6 / 8 / 10 s.
- Credits: Flow shows "Generating will use N credits" in the settings panel; record the real number
  at execution time and tell the user. Never invent a price.

## Prompt craft for Omni Flash clips

One shot, one action, one camera move. Structure:
`[shot size + subject + wardrobe/identity] [action, direction of travel] [environment, time of day]
[camera: height, lens feel, movement, speed] [light: key, rim, colour] [texture: grain, dust, depth
of field] [continuity: same subject/clothes as G#] [mood]`
Avoid list (negative prompt): text, captions, logos, watermarks of brands, extra limbs, distorted
hands or faces, morphing, flicker, sudden cuts, cartoon look (unless intended).
Keep identity consistent across clips by repeating the same subject description verbatim.
Leave composition room where graphics will sit (e.g. "subject in the right third, clean sky above").

## Execution (proven path, one approved ID)

1. `flow_browser_check_session` → must be logged in (if not: `flow_browser_login`, the user signs
   in themselves in the Chrome window and closes it).
2. `generate_video` with the sheet's prompt, `model: "gemini-omni-flash"`, `aspectRatio`,
   `duration`, `negativePrompt`, `idempotencyKey: "<project>-<ID>"`, `waitForCompletion: false`.
   The server sets up a new Flow project and fills the composer. **With Omni Flash the server's own
   submit works**: the job reaches `COMPLETED` by itself (≈1 min) and the file appears at
   `mcp/google-flow-mcp/outputs/<job>/final/video.mp4`. So **always poll `get_video_job` first;
   never click while the job is still pending or generating** — a click then makes a second, paid
   generation. Steps 3–5 are only the fallback when the job ends `SUBMISSION_FAILED` (or
   `FLOW_UI_CHANGED`) with the composer still filled; the user's approval of the ID covers that
   one fallback click, never both.
3. Verify the composer: `node scripts/flow_once.mjs inspect` → prompt present, mode Video, model
   Omni Flash, ratio, duration, credits text, nothing already generating. If anything is wrong,
   fix only settings (never generate) or stop and report.
4. Click once: `node scripts/flow_once.mjs click --expect-model "omni" --id G1 --approval "<user's words>"`.
   It refuses if the state is not as expected, clicks once, and appends to the ledger.
5. Observe only: `node scripts/flow_once.mjs watch` until the tile appears (Omni Flash is usually
   1–3 min).
6. Retrieve: `node scripts/flow_once.mjs fetch --out <project>/assets/flow/G1` → Flow's
   "Download batch" (no extra credits) → zip lands in `%USERPROFILE%\Downloads` → copied into
   the asset folder. Then `python scripts/flow_ingest.py --dir <project>/assets/flow/G1 --id G1`
   → safe extract, probe (codec, size, fps, duration, cropdetect, loudness), `qc/contact_sheet.png`,
   full-res frames, `provenance.json` joined with the click-ledger entry.
7. QC before use: contact sheet, full-res frames at 25/50/75 %, check faces, hands, limbs,
   continuity, flicker, text artefacts. If it fails, report and ask — never auto-regenerate.
8. Close the Flow Chrome window when the session's generations are done (its debugging port exposes
   the profile to local programs).

## After retrieval
- Record in `artifacts/asset_manifest.json`: id, type, path, `source_tool: google-flow`,
  model, prompt, job id, ratio, duration, credits, licence note ("per Google Flow terms").
- Compositing rules (grade match, 720p upscale honesty, watermark, muted audio): see
  `editor-doctrine.md` §8.

## Known behaviour (measured, 2026-10)
- Image test: Nano Banana 2.1, 1024×1024 JPEG, visible sparkle mark bottom-right.
- Video test (Veo 3.1 Quality — now banned by the user): 720×1280 H.264 24 fps + AAC, 8.0 s,
  active picture 720×1104 with 88 px bars, "Veo" mark inside the bottom bar, near-silent audio
  (−36 LUFS); Flow stated 100 credits.
- Omni Flash (Flow labels it "Omni 1.1 Flash"), project recovery-agent, 4 clips: 720×1280 H.264
  24 fps, durations 8.0 / 6.0 / 4.0 / 4.0 s, full-frame picture (no bars), sparkle mark
  bottom-right at ≈(600,1160) of 720×1280, near-silent audio (−21 to −45 LUFS). Flow's panel showed
  12 credits for an 8 s clip. Same-person continuity across clips held well with a repeated
  identity sentence.
- **The server's prompt compiler appends camera lines.** "Static camera" became "Locked tripod
  camera…", and the model drew a literal camera tripod in frame (G2, unusable). Never write
  "static", "tripod", "locked-off" or other camera-gear words; describe the framing instead
  ("steady eye-level medium close-up").
- **"Leave clean space in the upper third" was taken literally:** the model painted a flat cream
  panel over the top 314 px of the frame (G3). `cropdetect` does not catch light panels. Check
  full frames, not only cropdetect; prefer "uncluttered background in the upper third".
- AI text artefacts: posters/signs get pseudo-Devanagari even when the prompt says "no writing".
  Keep signage out of the prompt or plan to cover/cut it.

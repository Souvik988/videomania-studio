# House rules: the user's notes, turned into permanent rules

Every note the user gives about a film becomes a rule here (and, where it can be measured, a check
in `qa.py`), so the same note is never needed twice. Read this file before every edit; it overrides
any general default in the other references. Add new rows at the top, with the date and the user's
own words.

| Date | The user's note (their words or close paraphrase) | Rule now | Enforced by |
|---|---|---|---|
| 2026-10-22 | "The background… my focus is going on the background instead of my real video. Upside and downside black only, no frame, no typography outside the video." "The captions are very generic — use typography animation, the best font." | Vertical (9:16 / 4:5) versions of a 16:9 film: the film full width, centred, plain black bars; nothing outside the picture (no plate, frame, headlines or captions). Captions are kinetic type inside the film: condensed display face, words spring in on their spoken time, keywords punch bigger in the accent; heavy soft shadow for contrast instead of a box; hidden where a giant headline already spells the words. This replaces the 2026-10-17 caption-box default for this user | SKILL step 6, this table |
| 2026-10-22 | "If you need any images, any UI element, icons, 3D element, motion graphics element, B-roll image, whatever asset you need, use ChatGPT, which I already logged in on your browser." | Every image asset is generated in ChatGPT (built-in browser), as transparent sticker sheets in one style, sliced, with provenance. Text, numbers, logos and exact UI stay coded. Generated stills always move | SKILL step 4, `chatgpt-asset-production.md`, `chatgpt_slice.py` |
| 2026-10-22 | "The green screen part, you have to do it most precise." | Clean-plate key, previewed at full size and zoomed on edges before the full pass; relight the subject to the plate (grade + warm/cool rims); a still plate always moves (push, parallax, coded light) | `greenscreen-compositing.md`, `greenscreen_key.py`, `greenscreen_relight.py` |
| 2026-10-22 | "Every 2 seconds some new thing has to come out." "Zoom in, zoom out effect" (UGC) | A visible new element or move at least every ~2 s; a talking head gets punch-ins on stressed words and slides aside for content; never a static talking head | `qa.py` cadence gate (2.2 s), editor-doctrine §5 |
| 2026-10-22 | "When I'm telling 50,000 rupees… transaction SFX, money-coming SMS." | Money/price beats: the price tag drops and slams with count-up, ka-ching + coin burst + SMS ding, and an SMS-style banner | SKILL step 5, `sfx_design.py` |
| 2026-10-22 | "The video you generated previously was very generic motion." | Motion is built per word with the motion kit, giant type in the room behind the subject, 3D objects that pay off later, real product recordings in devices; same as the 2026-10-17 rule, applied harder | motion brief, critic |
| 2026-10-17 | "I got Google Flow Ultra." | Flow clips arrive without a visible mark from Flow itself; use them exactly as delivered; never remove, crop or mask marks | SKILL §2, editor-doctrine §8, flow_ingest provenance |
| 2026-10-17 | "The motion graphics you made are very generic." (recovery-agent) | Research real Opus 5.5 motion first; write a motion brief with a concept, central visual rule, bridges between scenes, one object changing shape; no grey placeholder bars, no repeated layouts, every problem graphic pays off | SKILL step 3, `motion-design-playbook.md`, critic prompt, `qa.py` cadence gate |
| 2026-10-17 | "Research these sources and build from them every time." | Each film's `brief/motion_research.md` cites 3–6 references with the technique taken from each | SKILL step 3, critic reads it |
| 2026-10-16 | "Every Flow video generation uses Omni Flash 1.1, never Veo 3.1." | Model `gemini-omni-flash` only; stop if it isn't offered | SKILL §2, `flow-asset-production.md`, `flow_once.mjs --expect-model omni` |
| 2026-10-16 | "Every time I'll tell you 16:9 or 9:16." | Ask for the format when it isn't given; never assume | SKILL §1 |
| 2026-10-16 | "For each generation I'll approve one click." | One explicit approval per Flow generation; no retries or extra takes without new approval | SKILL §2, generation sheet, click ledger |
| 2026-10-16 | Video Mania = Claude as the best After-Effects-grade editor and motion designer, working from a voiceover alone | Claude decides every visual, timing, typography, caption, sound and hook itself | SKILL intro, `editor-doctrine.md` |

## Rules adopted from herk-edit-kit's measured notes (2026-10-17)

These came from another creator's edit rounds (MIT, github.com/nateherkai/herk-edit-kit). They
stand until the user's own notes say otherwise.
- Captions: one look for the whole film, a dark box with a thin light edge; never white on light
  (`qa.py` caption_contrast); never over a mouth; chunk mode for 9:16.
- Every shot moves: no frozen frames. Nothing over 2.2 s without a visible change outside a
  declared hold (`qa.py` cadence).
- Video beats images: a *frozen* AI still used as B-roll is a build error. ChatGPT stills (the
  user's 2026-10-22 rule above) are welcome as elements and plates, as long as they always move.
- Sound: soft taps, dry clicks, paper, air; no laser zaps, pitch-drop plops or a whoosh on every
  cut. Delivered true peak ≤ −1.5 dBTP, measured on the encoded file (`qa.py` loudness).
- Speech is cut between phrases, never inside one; never sped up (`cut_speech.py`).
- The first 3 seconds give a specific reason to stay; three openings are drafted and compared
  (`storyboard/open_loops.json`, `qa.py` open_loops).

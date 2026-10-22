# Video Mania typography engine

Seven font roles, eight pairings, ten presets, 23 text animations and a rhythmic caption engine,
rendered on the same HyperFrames timeline as the rest of the film. The judgement (which face, how
big, where, when) is in `../references/typography-and-captions.md`; this folder is the machinery.

```
config/font-registry.json      7 roles: requested font, OFL fallback, licence, usage, animations, readability
config/pairing-presets.json    8 pairings (helvetica_garamond … impact_helvetica_garamond)
config/typography-presets.json 10 presets (CLEAN_TALKING_HEAD … MULTI_FONT_STORYTELLING), read by type-kit.js
config/local.json              (git-ignored) licensed user fonts, e.g. {"licensed_user_fonts": {"Blacksword": "fonts/private/Blacksword.otf"}}
fonts/open-source/             OFL files + OFL.txt each + MANIFEST.json (sha256, source URL at a pinned google/fonts commit)
fonts/private/                 your licensed fonts; git-ignored, never copied into deliveries
src/typography.py              resolver (6 states), selector, measurement / wrap / fit, glyph coverage, script detection
src/type-kit.js                browser runtime TK: style, depth, 23 anims, title, extrude, captions
scripts/setup_fonts.py         download + verify the OFL faces (idempotent, offline afterwards)
scripts/audit_fonts.py         resolve the 7 roles on this machine → FONT-LICENSE-REPORT.md
scripts/verify_fonts.py        files, licences, glyphs, real weights, presets wiring (exit 0 = all pass)
scripts/select_type.py         the selector from the command line
scripts/build_typekit.py       install TK into a composition (new_composition.py runs it)
tests/                         python -P -m unittest discover -s typography/tests; node typography/tests/type-kit.test.cjs
```

## States

`EXACT_AVAILABLE` (installed here, used in place through CSS `local()`), `LICENSED_USER_FONT`,
`OPEN_SOURCE_INSTALLED` (the requested font is itself OFL: Cormorant Garamond), `FALLBACK_ACTIVE`,
`LICENSE_REQUIRED` (Blacksword: commercial licence needed; Italianno renders), `UNAVAILABLE`.
A fallback is never reported as the original. On this Windows machine (2026-10-22): Impact exact;
Helvetica→Inter, Garamond→EB Garamond, Rockwell→Arvo, Snell Roundhand→Great Vibes fallbacks;
Cormorant Garamond exact (OFL); Blacksword licence required → Italianno.

## Commands

```bash
python -P typography/scripts/setup_fonts.py            # install / verify the open-source faces
python -P typography/scripts/audit_fonts.py --refresh  # after installing or buying a font
python -P typography/scripts/verify_fonts.py --text "Har creator ye font use karta hai"
python -P typography/scripts/select_type.py --text "ONLY ₹50,000" --video-type promo --scene price
python -P typography/scripts/select_type.py --pairing helvetica_garamond
python -P typography/scripts/build_typekit.py --src projects/ID/source   # existing film
python scripts/new_composition.py --project ID --look dark-lit --format 9:16 --duration 30   # new film: TK included
python scripts/caption_track.py --project ID --mode type --friction cart,wait --go dashboard,offer
```

## In a composition

```js
TK.init({ W, H, fps: 30 }); await TK.load();
TK.captions(tl, "#captions", window.CUES, { preset: "MULTI_FONT_STORYTELLING", scale: 1.3,
  skip: (c) => CAP_OFF.some(([a, b]) => c.s >= a && c.s < b),
  layout: (c, i) => CAP_PLAN[c.s] || { x: W / 2, y: H - 60, align: "center", style: i % 2 ? "line" : "stack" } });
const [hai] = TK.title(tl, "#front", [{ text: "HAI?", role: "impact_hook", px: 400, x: 930, y: 570,
  color: "#ff4a3d", depth: "hard", tint: "74,11,6", anim: "punchIn", at: 22.72 }], 22.72);
TK.extrude(tl, hai, 22.72, { layers: 5, dy: 3, back: "74,11,6" });
TK.out(tl, [hai], 23.0, "fastDrop");
```

Cue words carry `c: "a"|"go"` (Garamond payoff) or `c: "r"|"fr"` (Impact punch); one key word per cue.

## Licences

Every bundled face is SIL OFL 1.1 (texts kept beside each file and copied into each project's
`fonts/vm/`). System fonts are referenced, never copied. Blacksword: buy at
https://youssef-habchi.com/license, put the file in `fonts/private/`, name it in `config/local.json`.
Credits: timing tables after iart-ai/kinetic-typography-skills (MIT) and josiahsiegel/claude-plugin-marketplace
ffmpeg-kinetic-captions; 3D layers after heygen-com/hyperframes `rules/3d-text-depth-layers.md`.

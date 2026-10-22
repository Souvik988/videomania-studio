# Typography and captions

Read this before placing any word on screen. The engine is `typography/` (README there); this file is
the judgement: which face, how big, where, when and how it moves. The user's notes in
`house-rules.md` override anything here.

## 1. The seven roles (typography/config/font-registry.json)

| Role | Requested | Renders here when absent | Voice | Use for | Never |
|---|---|---|---|---|---|
| `impact_hook` | Impact | Anton | shout | hooks, problem words, prices, CTAs, KYA? / PROBLEM-style beats | paragraphs, body captions |
| `clean_caption` | Helvetica | Inter | say | every ordinary caption word, explanations, lower thirds | the payoff word |
| `classical_highlight` | Garamond | EB Garamond | savour | the ONE payoff word beside Helvetica, set italic 600 | more than one word per cue |
| `luxury_serif` | Cormorant Garamond | (bundled, exact) | luxury | premium titles, the "customized"-style middle word of a CTA stack | under ~72 px (hairlines vanish) |
| `editorial_slab` | Rockwell | Arvo | state | editorial headlines, business storytelling lines | — |
| `elegant_script` | Snell Roundhand | Great Vibes | feel | one emotional / festive word ("Diwali"), title accents | per-letter animation |
| `expressive_script` | Blacksword | Italianno (LICENSE_REQUIRED) | flourish | one artistic accent per scene | ads, unless the user holds a commercial licence |

Run `typography/scripts/audit_fonts.py` on the rendering machine; it writes `FONT-LICENSE-REPORT.md`.
A fallback is always named as a fallback (report, labels, delivery notes). Proprietary fonts are used
in place via CSS `local()`; their files are never copied, bundled or committed.

## 2. Choosing (typography/src/typography.py `select()`; `scripts/select_type.py`)

- Talking head → `clean_caption` + `classical_highlight` (pairing helvetica_garamond).
- Promo / SaaS talking head (the user's default) → MULTI_FONT_STORYTELLING: Helvetica says, Garamond
  italic savours the payoff word, Impact shouts the problem word.
- Hook, price, CTA → Impact (VIRAL_IMPACT_HOOK); an ad hook may sit over a Rockwell line (IMPACT_ROCKWELL_AD).
- Luxury / premium → Cormorant Garamond (+ Helvetica for facts, or a script accent for the title).
- Cinematic storytelling → Rockwell or Cormorant, script accent.
- Emotional highlight → clean caption + one script word (Blacksword only when licensed).
- Festive / emotional word inside a hook → script word beside an Impact word (impact_snell): "Diwali" + OFFER.
Three faces in one frame only with a clear hierarchy and room; never force every font into a scene.

## 3. Hierarchy and contrast (the user, 2026-10-22: "tall then short… make the contrast")

- Contrast comes from changing **one** variable hard: face (sans → italic serif), case (lower → UPPER
  Impact), or size (1 : 2+). Two weak differences read as a mistake; one strong one reads as design.
- Size ratio inside a cue: body 1 : payoff 2.0–2.2 : punch 2.0–2.3. One key word per cue (TK enforces it).
- Alternate cue shapes: a **stack** (small line, key word on its own line, small line) then a **line**
  (one row, key word inline at ~0.6× its stack size). Tall/short rhythm, never the same shape twice running.
- Tracking: display −0.01 to −0.03 em (video softens letter detail); Impact +0.005 em; small caps +0.12–0.18 em.
- Light-on-dark reads heavier: body 600–700 is enough; keep line-height ≥ 1.05 on stacked rows.

## 4. Placement: rhythmic, subject-aware (house rule 2026-10-22)

- Captions live in the **open third opposite the subject**. They switch side only when the subject
  moves (scene change), so placement reads as rhythm, not randomness.
- Inside one scene: alternate tiers (low ↔ mid) or call-and-response sides (under the device ↔ across
  the presenter's lap) when the frame allows; the lower-middle is home when the subject is centred.
- Never over the face or mouth. Giant words behind the subject only while ≥ 75 % of the letters stay
  visible; otherwise put them **in front, below the chin** (the PATA HAI fix).
- Never where a chip, device or headline already sits: plan slots from snapshots of the film without
  captions (`npx hyperframes snapshot --at <cue mids>`), then fill `CAP_PLAN` / `layout(cue)`.
- When a giant headline already spells the words (SALE SHURU, PROBLEM, COMPLETE SYSTEM) the caption
  steps aside (`CAP_OFF`); when a caption says what a chip says, change or drop the chip.
- Safe zones: 9:16 Reels/Shorts keep text between y 250 and y 1420 and out of the right 120 px. A
  16:9 film that will be cut to 9:16 is shown 1080 wide (×0.5625): design its captions at
  `scale: 1.3` so body ≥ 34 px and key words ≥ 70 px in the vertical cut.
- Vertical cut of a 16:9 film: full width, centred, pure black bars, nothing outside the picture.
  Encode with `setsar=1`, `-aspect 9:16`, BT.709 tags, AAC (some phone players squash a file without them).

## 5. Sizes (px at a 1080 short side; TK scales by min(W,H)/1080)

| Element | 9:16 native | 16:9 (also cut to 9:16) | min |
|---|---|---|---|
| Body caption (Inter 700) | 56–64 | 60 (scale 1.3) | 40 |
| Payoff word (Garamond italic 600) | 120–140 | 130 | 56 |
| Punch word (Impact) | 120–150 | 135 | 64 |
| Hero word (Impact) | 220–420 | 300–420 | — |
| Script word (Great Vibes; Italianno ×1.35) | 150–270 | 250 | 90 / 110 |
| Luxury title (Cormorant 500–600) | 140–160 | 150 | 72 |

Max ~6 words on screen; ≤ 2 body lines; ≤ 20 characters per second over the displayed time.

## 6. Sync (the PATA HAI lesson)

- Words appear on their spoken time minus 0.04 s; a punch lands on the stressed syllable; giant type
  arrives with its word, never before it.
- Before placing a big word, check its transcript confidence. Below ~0.6, or a word that "lasts"
  over 0.8 s, re-align it: plot the RMS envelope (20 ms hops) and re-transcribe that 5–7 s window
  with word timestamps and an initial prompt of the expected words. In the Shotlin film whisper put
  "pata hai" 1.2 s early and dropped "kaun repeat purchase kar raha hai" entirely.
- Every spoken line gets a caption unless a headline spells it.

## 7. Motion (TK.anim, 23 presets; timings after iart-ai/kinetic-typography-skills, MIT, and josiahsiegel's ffmpeg-kinetic-captions)

| Role | Enter | Timing |
|---|---|---|
| Impact | punchIn (scale 1.55→1 + blur, expo.out), scalePop, impactBounce, kineticWords | 0.2–0.28 s; Reels pops 120–180 ms, max scale 115–120 % |
| Helvetica | cleanWordReveal (rise 38 % + blur 6→0), minimalFade, captionSlide, activeHighlight | 0.24–0.3 s per word, on spoken time |
| Garamond | editorialHighlight (mask rise + tracking settle), elegantFade, serifAccent | 0.45–0.5 s |
| Cormorant | luxuryReveal (tracking +0.32 em → 0 + blur), cinematicLetters, softTitle | 0.8–1.0 s |
| Scripts | handwriting (clip wipe), writeOn (soft mask edge), gracefulFade, scriptFloat, expressiveReveal | 0.5–1.4 s by length; whole word only |
| Rockwell | editorialSlide, staggeredHeadline, structuredReveal | 0.42–0.55 s |

- Granularity: lines (calm, premium) 60–100 ms stagger; words 40–70 ms; characters 20–40 ms and only
  on short strings; cap a whole reveal near 0.8 s. Enter with expo.out; exits are faster than
  entries (0.14–0.2 s, last word first).
- Not every word animates hard: body words reveal quietly; only the key word gets the big entrance.
- Every caption block drifts ~1 % while it reads (never frozen).

## 8. Depth (the user, 2026-10-22: "a little shadow on the font gives depth")

- `TK.depth("soft")` on every caption word: a 4-layer em-based shadow (contact line + soft falloff).
  `strong` for busy plates, `hard` (tinted extrusion line) for Impact punch words, `glow` for scripts.
- Side-placed caption blocks tilt 6–8° toward the subject (`rotateY`): a quiet 3D plane.
- `TK.extrude(tl, el, t)`: 4–6 stacked DOM layers at 1–3 px for ONE hero Impact word (after
  hyperframes-animation `rules/3d-text-depth-layers.md`); the depth grows on entry. Heavy faces only.
- Type behind the keyed subject (`#behind`) is the strongest depth cue: use it for scene titles while
  the subject leaves room (§4); in front for questions and punches.
- No boxes behind captions for this user; contrast comes from the shadow and a dimmed plate.
- More: hyperframes-animation `rules/kinetic-beat-slam.md`, `depth-of-field-blur.md`,
  `gradient-text-sweep.md`; hyperframes-creative `references/typography.md` (video sizes, dark-background weight).

## 9. Multilingual

Romanised Hinglish uses the seven faces directly. Devanagari and Bengali glyphs fall through
`unicode-range` faces inside every role family to Noto Sans Devanagari / Hind Siliguri (bundled, OFL),
so there are no tofu boxes. Check with `verify_fonts.py --text "<line>" --role <role>`. Label caption
files as transcription, transliteration or translation.

## 10. Caption track and gates

- `caption_track.py --mode type` (default for new films): 3–6-word cues split on phrase boundaries;
  `--friction` words become Impact punches, `--go` words Garamond payoffs, one key word per cue.
  `--mode phrase|chunk` keep the older single-face boxes.
- `qa.py`: `captions_structure`, `captions_reading_speed` (≤ 20 cps), `caption_glyphs`, `caption_contrast`.
- Review on real frames: snapshot every cue's midpoint; check slot, overlap, face/mouth, sync on the
  key word, and the phone-size read in the vertical cut.

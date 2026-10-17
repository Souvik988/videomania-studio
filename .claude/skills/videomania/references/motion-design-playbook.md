# Motion design playbook: how Opus 5.5 work stops looking generic

Distilled on 2026-10-17 from the sources in `motion-research-sources.md`: 703 prompts behind real
Opus 5.5 videos, Charlie Hills' motion-graphics skill pack (16 effect recipes plus the review
rules from his rejected drafts), the Jitter AI, Swishy and AutoAE template catalogues, and two
prompt-craft guides. Read this before you design any coded scene. `editor-doctrine.md` decides
WHAT the viewer sees on each line; this file decides HOW it moves so it looks expensive.

Lesson that triggered this file: the recovery-agent ad (2026-10-16) timed well but its motion
graphics read as generic. They had skeleton grey bars, three near-identical "?" cards, scene
changes by fade or slide, one layout repeated for 8 s, and ticks that paid off nothing. Every rule
below exists to stop one of those.

## 1. Concept first: one line and one central visual rule

The best briefs name the concept in ONE sentence and give the film ONE rule that every scene obeys:
- "One pencil line gets promoted three times (graphite on paper, wire on a blueprint, light on black)
  and never leaves the screen."
- "Words have physical roles: WAIT is a lintel, VOICE is a support, FLOOR is a platform. The roles
  come from the letterforms themselves, not from illustrations behind them."
- "The whole video happens inside the period of the wordmark."
- "One shape is never cut: the hero object morphs into every UI component."

Write `concept:` and `central visual rule:` at the top of the motion brief. A beat that cannot
be expressed through the rule needs a reason to break it, written down.

## 2. Continuity: every scene grows out of the last

This is the single biggest difference between premium and generic work.
- **Nothing cuts and nothing crossfades** inside a coded sequence. Instead: shapes morph, a colour
  floods the frame and contracts into the next scene, an object lifts into an orb that the next
  scene opens inside, a period irises open, a bezel grows out of a screen edge.
- **Shared elements move; they are never duplicated.** A title travels from the card into the window
  bar. A number travels from the chart into the price tag.
- Hard cuts are kept for footage/graphics boundaries and for comic or impact beats (a "Kya?" punch).
  Even then, carry ONE element across the cut (a colour, a shape, a position) so the eye has a bridge.
- Plan the chain before building. In the edit map, add a `bridge` column naming what carries each
  scene into the next.

## 3. The premium move: one object changing shape

"Make it premium" means one object turning into another: a button into a player, bars into a
line, a card into a window, a tab pill stretching to the next tab. A fade from one picture to
another looks cheap every time. Supporting rules:
- **Ghost of the start state.** Leave a faint (dashed or 15–25% opacity) outline where the object
  began, so the eye can follow the change.
- **Contents wait for room.** The shell grows first; its contents fade in only after it is past
  halfway. Old labels fade out in the first quarter of the move.
- **Brackets before the move.** Accent corner brackets snap around "this one" (about 0.3 s) before
  it lifts out.
- **Values never change during a morph.** The same six numbers are bars, then a line.

## 4. Timing and easing grammar

- **Springs, not tweens,** for UI objects: tightly damped with a small settle (overshoot 2–6 %).
  Give stacked items **different damping** (back heavy, front light) so the top one leads.
  Width and height spring on their own curves.
- **Signature curve.** One custom cubic-bezier for every morph in the film, for example
  `(.45,0,.15,1)` gliding 0.6–0.8 s. Make the camera ride the same curve.
- **Stagger by a beat, never all at once.** Rows, letters, slats and dots start 40–90 ms apart, in
  reading order. Everything moving together reads as a slide transition.
- **The hold must stay alive.** Under narration a finished state holds, but one small thing keeps
  moving: a progress bar creeping, a cursor drifting, a second wave of light, a slow 1.03–1.07 push.
  There is only ever ONE focus.
- **Camera never stops** on full-frame graphics: a slow push or drift per scene. "Screen-studio"
  zooms reframe so each UI moment fills the frame, and the cursor scales with it.
- **No dead time and no long holds.** Over 1.5 s with nothing changing means a beat is missing.
  The exception is the final lockup, held at least 2 s.
- **Work motion out from the film clock.** If an object re-opens before it has finished closing,
  it continues from where it is. Per-scene tweens jump.
- **Under a voiceover use hold mode, not loops.** Take only the active move (about 1.4 s) of an
  effect, landed on the word, then hold. Never let a loop reset mid-sentence.

## 5. Type system: three roles, never one font for everything

1. **Display** (1–4 words): heavy or condensed grotesque (Barlow Condensed 800, Archivo Black/900,
   Geist 900). Tracking −40 to −80. Hero word 120 px or more on 1080-wide frames.
2. **Secondary** (stacked lines, UI titles): grotesque 600–800 (Inter, Geist, Syne).
3. **Labels and crumbs** (timestamps, kickers, mono tags): monospace or small caps, 24–34 px,
   tracked +0.14 to +0.3 em, 18 characters or fewer.
- **Letters rise through a mask line** one by one. Nothing pops in from nothing, and there are no
  typewriter reveals on headlines; typing belongs only inside an input box.
- At most about 5 words on screen per beat besides captions. Labels are never under 34 px in a 9:16
  film, so they read at phone size.
- Load every font explicitly before frame 0, so the first frame never paints in a fallback.

## 6. Palette and finish

- **Roles, not colours:** ground, surface, ink, muted, accent, second accent. Use one or two accents
  per piece. An accent can hand off between acts: each stage's accent becomes the next stage's
  ground.
- **One saturated hero colour** can be the film's signature (one embossed button, one tag). The rest
  stays neutral.
- **Finish, chosen once per film:**
  - paper grain with halftone and fine film grain;
  - fresh grain every frame with halation on bright edges, a soft vignette and warm lifted blacks;
  - colour fringing at the frame edges only;
  - frosted glass with a 1 px bright rim, the blurred image behind the panel and a soft shadow that
    grows with height.
- **Render styles that read as handmade:**
  - pencil lines resampled and pushed off true by slow sine waves (phase changing about 8 times a
    second), stroked twice (full width at 90 %, half width at 40 % with more wobble);
  - hatching instead of flat fills;
  - stepped motion "on twos" (hold each pose for 2 frames at 24 fps) for documentary or Vox looks;
  - torn paper cards with small shadows;
  - die-cut stickers with a white border.
- Pick ONE look per film and write it into the motion brief. Mixing four looks is how films start
  to look like templates.

## 7. Content: real words, not grey bars

- **Never grey placeholder bars** in hero UI. Put the VO's own words into the UI: names of the
  modules it lists, the price it says, the action it describes. Where a number is needed and the
  user gave none, either cut the number or show a clearly labelled sample (`example` or
  `illustrative` chip on every frame it appears). Never invent a metric or a testimonial.
- **Every result carries one real word or number,** never filler.
- **UI that is drawn should look like real software:** consistent icon stroke, real spacing,
  squircles, and states that respond (hover, press, check).
- A question or problem beat must **pay off with the same graphic later.** If the cart icon was the
  problem, the dashboard's cart module shows that cart recovered. A row of ticks alone is not a
  payoff.

## 8. Effect recipes (16) and when to use them in a voiceover film

`python scripts/motion_refs.py --effects` lists them; `--effect "<name>"` prints the full recipe
(start state, end state, timing inside the move, the premium detail).

| Need in the VO | Effect |
|---|---|
| a product "doing" something | 01 button→player · 02 search→results · 03 card→workspace |
| comparing options or plans | 04 tabs→panels (stretching pill) |
| a result or trend | 05 chart morph · 06 dashboard zoom (brackets, lift from real slot) |
| three offers or examples | 07 spring stack (per-card damping, ghost of rest angle) |
| tools or integrations | 08 magnetic dock (bell-curve swell under cursor) |
| headline or name reveal | 09 masked type · 10 elastic type · 11 text→layout |
| product photo or footage reveal | 12 image reveal (slats with light edges, in sequence) |
| layers or how it works | 13 perspective shift (one vanishing point) |
| one line that matters | 14 glass focus (lens, 1.1× sharp text, chromatic copies) |
| one input feeding many outputs | 15 flowing paths (pulses draw the line; nodes answer with rings) |
| ending on a mark | 16 particle logo (seeded scatter, grid inside real shape) |

Also worth borrowing from the template catalogues (Jitter, Swishy, AutoAE), as code:
- notification stacks sliding in on springs;
- an iMessage/WhatsApp thread with typing dots;
- a cursor click with ripple;
- a counter or odometer roll, and years rolling as text;
- a calendar grid drop;
- a rotating card ring or carousel of footage;
- a 3D laptop opening;
- an Apple folder opening with images popping out;
- stretched or repeated type, a type trail, squiggle-flow text;
- halftone, dither, threshold, CRT and pixel-dissolve transitions;
- a fluted-glass background;
- a gooey blob morph.

## 9. Structure: build on the narration's beats

- In a voiceover film the beat grid is the **word timings** (and the music's downbeats when a track
  is supplied). Something lands on every stressed word. Map 1 beat to 1 visual change.
- Opening: the first 3 seconds would stop your own thumb, or they get rebuilt. Say the hook BIG,
  and show the first surprise within 5 seconds.
- Funnel for ads: problem → product → proof → CTA. The CTA holds at least 3 s; the brand lands at
  the end, ideally with a 1 s or longer hold.
- No two consecutive beats share a layout (variety), but all of them share the type system, palette
  and signature curve (consistency).
- For a big film, build the first 10 seconds in 2–3 looks, pick one, then build the rest.

## 10. The banned list (paste into every motion brief, trim per film)

Crossfades between coded scenes · blur-ins and "developing" brightness fades · pop-in slams from
zero (except deliberate comic punches) · bouncy, loose springs · beat-snapped rotations · particles
and glows used as decoration · gradients on text or UI chrome · grey placeholder bars in hero UI ·
generic dashboard layouts · stock icons, emoji or clip art · small objects floating in empty space
· the same layout twice in a row · holds over 1.5 s without a living element · cropped type ·
typewriter headlines · invented numbers, logos or testimonials · real third-party UI or logos
redrawn from memory.

## 11. Self-check before showing anything

- Snapshot a still every 1 s (`npx hyperframes snapshot --at ...`) and judge each one as a design
  director. Then look at the contact sheet at about 200 px wide: anything generic, cheap, too small
  or empty fails.
- Freeze test: pause mid-hold. The point of the beat reads from that single frame.
- Continuity test: for every scene change, can you name the element that carried the eye across?
  If the answer is "it faded", rebuild that transition.
- Brand test: every colour and font on screen is in the motion brief.
- Fix one thing at a time once it is close, keeping the motion and timing you already liked.

## 12. Looks: pick ONE per film, then obey its rules

The banned list (§10) is the default. A look can lift specific bans, but only when it is chosen
on purpose in the motion brief. Starting palettes for all of them are under
`research/herk-edit-kit/.agents/skills/hyperframes/palettes/` (bold-energetic, clean-corporate,
dark-premium, jewel-rich, monochrome, nature-earth, neon-electric, pastel-soft, warm-editorial).
Restyle a palette to the brief; never ship it unchanged.

| Look | Feel | Lifts from §10 | Core recipe |
|---|---|---|---|
| **Warm editorial** | paper, print, Vox-like | nothing | paper grain + halftone, torn cards with real edges and contact shadows, stepped on-twos motion for documentary beats, condensed display type |
| **Apple product** | tactile, precise, light | nothing | light ground, layered soft shadows, frosted glass with a 1 px bright rim, squircles, springs with a tiny settle, one or two system accents |
| **Dark lit** ("Infinite" spot) | premium, cinematic, black canvas | glows and halos, chrome gradient text, motion-blur whips | see below |
| **Minimal dimensional** | objects with real thickness | nothing | readable silhouettes, bevelled edges, occlusion, directional light, soft contact shadows; real 3D (CSS 3D or pre-rendered) when the camera turns |

### Dark lit, the recipe (from herk-edit-kit `MOTION_PHILOSOPHY.md`)
- About 90 % of every frame is black or near-black; negative space is the design. **Light is the
  brand, not colour**: chrome gradients, halos, light beams, vignettes.
- **Always on:** a perspective grid floor (`perspective(900px) rotateX(60deg)`, two
  `repeating-linear-gradient` axes at about 5 % white, `background-position` drifting), a radial
  vignette and grain. Crosshair `+` marks are the unifying texture.
- **Type is a character**, carrying about 60 % of the storytelling. Words scale up to 8×, and
  headlines use a chrome gradient (`#fff → #999 → #ccc`, `background-clip: text`) with a soft halo
  on the emphasis word. For a chrome sweep use 8 stops with dark bookends and tween
  `background-position` 100 % → 0 % over 0.6 s.
- **Word-reveal carrier:** the first word slides about 360 px with `expo.out` over 0.33 s; the
  following words decay 120 → 60 → 25 → 12 px with `power2.out` over 0.2 s. On punchlines, lead the
  picture about 0.2 s ahead of the word so it reads as inevitable.
- **Palette is symbolic:** at most 5 active hues, each owning one meaning (red = broken, teal =
  working, …). If you can't name a colour's meaning, it hasn't earned its place.
- **Transitions:**
  - the light-streak whip (a blurred white bar crossing at the cut; the next scene starts at the
    streak's peak);
  - the "cut-the-curve" vertical whip: exit `y −150` + `blur 30px` over 0.33 s with `power2.in`,
    entry from `y +150` + `blur 30px` over 1.0 s with `power2.out`, same direction on both sides;
  - a colour recolour through CSS variables (same DOM, new meaning);
  - flash-through-white only for act breaks.
- **Pacing:** 1.0–2.0 s scenes; holds of 1.5–2 s on the logo and 4–6 s on the CTA; a 1 s rest after
  every 7–8 s of density.

## 13. HyperFrames craft laws (framework-critical; from herk-edit-kit, verified against HF behaviour)

1. **Timelines must fill their slots.** HyperFrames hides a sub-composition the moment
   `timeline.duration()` is shorter than its `data-duration`, which flashes a black frame. End every
   sub-composition timeline with `tl.to({}, { duration: SLOT_DURATION }, 0)`. (A single
   proxy-driven `render(t)` timeline, as Video Mania usually builds, already spans the film.)
2. **Bracket every `<video>` with stills.** Videos can flicker on their first frame and go black
   after the source ends. Add a poster image hidden at the video's start and a last-frame image
   shown from the video's end (`ffmpeg -ss 0 … poster.jpg`, `ffmpeg -sseof -0.04 … lastframe.jpg`).
3. **Name the seam.** Every entry or exit tween's comment names the matching tween in the adjacent
   beat ("ENTRY: blur 22→0 matches the outgoing beat's 22 px exit"). If you can't name it, the seam
   isn't designed.
4. **Snap tween ends to frame boundaries** (multiples of 1/fps). Steep-tail eases (`expo.in`,
   `power4.in`) alias at sub-frame ends.
5. **Animate transforms** (x, y, scale), not `top` or `left`, except for clip boxes the layout needs.
6. **No `Math.random()` or `Date.now()`**; use seeded PRNGs or harmonic hashes. Live WebGL can stall
   headless renders, so ship a Canvas 2D fallback.
7. **Captions live outside sub-composition timelines** as root-level siblings, so a retimed scene
   never strands a caption.
8. **Registry blocks give speed; hand-built gives reference quality.** Benchmark pieces install no
   blocks. Use blocks and library cards (§14) as structural donors, restyled to the brief.

**GSAP dictionary (ease and duration):**

| Purpose | Ease | Duration |
|---|---|---|
| word reveal | `expo.out` | 0.20–0.33 s |
| generic enter / exit | `power2.out` / `power2.in` | 0.2–0.5 s / 0.2–0.33 s |
| whip exit / whip entry | `expo.in` / `expo.out` | 0.2–0.33 s / 0.5–1.0 s |
| camera pan between stops | `power2.inOut` | 1.2–2.3 s |
| card settle | `back.out(1.2–1.5)` | 0.3–0.5 s |
| UI overshoot | `elastic.out(1, 0.3–0.4)` | 0.2 s |
| breathe / drift | `sine.inOut`, yoyo | 2–4 s |

Declare the ease and duration on every tween; don't use `gsap.defaults()`.

**Transition catalogue:** `research/herk-edit-kit/.agents/skills/hyperframes/references/transitions/catalog.md`
plus the `css-*.md` files (3D, blur, cover, destruction, dissolve, distortion, grid, light,
mechanical, push, radial, scale). Read the one that matches the bridge planned in the motion brief.

## 14. Card donor library (406 cards; herk-edit-kit style-library)

`motion_refs.py --cards "<purpose or words>" [--tier tier1|tier2] [--style vox-explainer|kallaway]`
lists cards with their named slots and durations; `--card <id>` shows one card's markup.
- **tier1** cards are full-screen takeovers (thesis, stat, section, quote, overview). **tier2** cards
  support footage without covering a face (label, list, equation, definition, lower third).
- They are **drafts at 1920×1080 in their creators' palettes** (Vox-like paper, and the dark
  "aurora glass" Kallaway look). Use them as **structural donors**: take the layout logic, slot
  structure and timing idea, then rebuild at the film's size with the motion brief's tokens, type
  system and signature curve. Never ship a card unchanged, never mix two donor looks, and never let
  a donor's look replace the film's chosen look.
- A good donor answers a layout problem the edit map already has ("two numbers compared",
  "a five-step flow", "an agenda"). Don't browse cards for ideas before the edit map exists.

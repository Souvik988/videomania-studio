# Vox poster system (colour), the user's reference look

Built 2026-10-23 for a 53 s 9:16 Hinglish ad, after the user rejected a warm-paper sticker collage
as "cheap and minimal" and sent a reference reel (a black-and-white editorial portrait edit) as
the "Vox style". They then said: **not black and white**. This is the look, the build recipe and
what the independent critic (3 passes, 60 to 66/100) still found wrong, so the next film starts
ahead. Reference code: `templates/vox-poster/scenes_vox.reference.js`.

## The look

Every frame is a **designed poster**, not a slide with captions:

- **Persistent chrome**: micro-type header (brand mark, a tiny paragraph, an issue counter such as
  `00004` that increments per scene) and a spec footer (year chip, crossed box, barcode, mark,
  the film's question). Chrome flips dark/light with the ground.
- **Grounds**: white/cream satin with leaf shadow, navy velvet, cobalt grid paper, electric cobalt.
  One dominant ground per beat, switched behind a transition. Slow drift so no ground is frozen.
- **Palette** (this film; choose a new bold one per film): cream, navy, cobalt, tangerine, butter
  yellow, mint. Colour is the point: never fall back to monochrome.
- **Cut-out photos breaking out of colour frames** (subject overlaps the frame edge) plus 3D
  colour objects with a dotted orbit ring. Many more assets than feels necessary, used
  aggressively: grounds, photos, 3D objects, device mockups, icons.
- **Mixed kinetic type in one top zone** (the caption home): sans words + a script payoff word +
  a bold extended word + a giant Didone hero (stripes + RGB fringe). Fonts: Bodoni Moda, Pinyon
  Script, Archivo (extended), Inter/clean sans, JetBrains Mono, Unbounded.
- **Product-label spec cards** (barcode, QR pattern, arrows, globe) for every feature or price.
- **Transitions**: focus pulls (blur + 3.5% scale, 0.17 s in / 0.38 s out), circle irises, colour
  flashes, letterbox bars. Grain and chromatic aberration on everything.

## Build recipe

1. Generate the asset library first (ChatGPT, one thread per look; see
   `chatgpt-asset-production.md`): colour cut-outs of the real subject, grounds, 3D objects,
   icon sheets. Slice with `scripts/chatgpt_slice.py`.
2. One stage node holds ground + world + scenes so a focus pull blurs everything at once.
3. Chrome and the kinetic line are separate fixed layers above the scenes (z 35/36).
4. Each scene = ground + frame + cut-out + 1 to 3 objects + one spec card or device; the through
   object (a receipt, a cart) recurs and pays off.
5. Real product recordings go in device shells (`phone()`); never redraw the product from
   imagination. Brand the mockups (a generic "YOUR STORE" was a critic defect).
6. Run `template_lint.py`, then render a draft and have the independent critic score it.

## Lessons from the critic (66/100 at v4); fix these by construction next time

1. **Frame 0 must already be alive.** v4 opened on empty velvet (luma 3.5) and had a dead stretch
   0.9 to 2.77 s. Show the subject and the stake at frame 0, no fade-in; keep something moving
   every 0.5 s; make the hook question the biggest type in the frame, not 30 px mono.
2. **Close every open loop.** A bill set up as "PAID BY ? ? ?" was never torn or answered; the
   planned tear was never drawn and the payoff was a different object. Reopen the *same* object
   at the end and pay it off visibly (strike rows, restamp, answer the question).
3. **Inventory once.** The same feature list was told three times (deck, devices, checklist).
   One recap object only.
4. **Dead holds over 1.5 s** (a static page, a static portrait) read as stalls; run a live colour
   wipe, a dolly, or slide-in screens during the hold.
5. **Placeholder-looking transitions** (a smeared blue rectangle at a focus pull, a blurred empty
   box) look like missing assets. Pull focus on the real cut-out or use an iris.
6. **Props must read**: a "burning paper" for ad spend must be a note or labelled; blank paper
   confuses the line "ad ka paisa gaya".
7. **Contrast**: script type on cream at ratio 1.08 fails (`caption_contrast.py` found 45 samples).
   Put kinetic lines on a plate or add a 2 px navy stroke. No type over the footer chrome.
8. **Do not invent claims**: a price card that said "one-time" when the VO never said so was
   flagged. Only what the VO or brief states.
9. **SFX density**: 95 cues and 9 booms in 53 s. Cap booms at one per 10 s and avoid 50 ms stacks.
10. **Subject scale**: the reference holds the subject at 45%+ of frame width and a hero word
    across the full width by 0.33 s; ours were small. Go bigger.
11. **Measure motion**: 54% of frames changing vs 81% in the reference. Run `analyze_video.py` on
    the reference and the draft and beat the reference number.

## When to choose this look

Narrated explainers and ads for D2C / creator audiences who respond to editorial energy. Not for
calm corporate pieces. Pair with the story engine in `editorial-collage-and-diorama.md`.

# Green-screen compositing (self-shot talking head onto a set)

Built on the Shotlin promo (2026-10-22): a lime screen, a gaming chair, a white mic cable, soft
shadows beside the body, composited into a dark neon room plate.

## Pipeline
1. **Probe** the footage. Keep the source fps and decimate to 30 fps by taking every 2nd frame of
   60 fps. Never resample.
2. **Preview the key first:** `greenscreen_key.py --src IN --out key --preview 4 --room plate.jpg`.
   Look at the composites at full size and zoomed (cap edge, hair, fingers, cable, chair edges).
   - It builds `key/plate.png`, a clean plate of the empty screen, as a median over frames where
     each pixel is surely screen.
   - Alpha comes from Vlahos against the plate (1 − k/k_plate, with k = g − max(r, b)). Screen in
     the subject's cast shadow is caught by chromaticity matching. Deep pockets the plate never saw
     are caught by brightness-relative greenness.
   - Within ~17 px of the edge, chroma-subsampling bleed is removed by plate distance.
   - Then: islands removed, pinholes < 120 px filled (never real screen slivers), a guided-filter
     edge, sliver removal, choke, un-mix against the plate, and a spill clamp in both directions
     (no green, no magenta).
3. **Full key in parallel:** 3 workers with `--range a:b` (start on even source frames), then concat.
   About 7 minutes for 46 s at 1080p on the user's machine.
4. **Relight:** `greenscreen_relight.py part.webm lit.webm` on each part, then concat into
   `source/media/presenter.webm`.
   - It grades the subject toward the plate (darker, warmer, lower body into shadow).
   - It adds inner-edge rim light: warm from the plate's warm side, cool from its cool side, a faint
     top light.
   - Tune GRADE and the rim strengths per plate.
5. **In HyperFrames**, the VP9-alpha WebM plays natively in `<video>` (verified with v0.8.162).
   - Layer stack: plate (soft, slightly blurred) → giant type BEHIND the subject → the subject →
     devices and icons → captions.
   - Wrap the video in a non-timed div and animate the wrapper (punch-ins, slides) with
     `transform-origin` at the frame's bottom centre, so the cut-off body never shows an edge.
   - A still plate still lives: a slow camera push, parallax against the subject (the plate moves
     about 25 % opposite), and coded light (neon flare, dim, flicker).

## Rules
- The background the user supplies is used as delivered. If the video version carries a mark,
  prefer the clean still of the same set (with coded motion) over cropping the mark.
- Giant type behind the subject must still read. Split words around the head ("PATA | HAI?"), or
  move the subject aside. If the subject covers more than ~30 % of a word, it moves in front.
- Judge the key on real frames at full size after every change. "Looks fine at 600 px" is not a pass.

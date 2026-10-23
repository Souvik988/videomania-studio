# Editorial collage (Vox) and paper diorama

Two house looks for explainers and narrated pieces, adapted from the user's `vox-motion-graphics`
skill (2026-10-23) to Video Mania's tools: coded collage in HyperFrames (`MKS.paperGround`,
`paperCut`, `doodleBoil`, `headlineWall`), ChatGPT for cut-outs and props, Google Flow (Omni Flash
only, one approval per generation) for moving diorama shots. Higgsfield is not part of this setup.

## The story engine (applies to every narrated film)

- **One through-line object** travels through every scene and escalates (a fuse burning across all
  beats, a balloon pumped toward a needle, the abandoned cart that comes back). Design it before
  writing any beat; the finale pays it off. (Video Mania's "one object changing shape", playbook §3.)
- **A question hook answered last**: put the question on a prop or in giant type in beat 1
  ("PATA HAI?", "WHO PAYS?"); the narration withholds the answer until the kicker.
- **Fake-oner**: every scene enters and leaves in full motion (dive, whip, flare, fall) so hard cuts
  read as one unbroken shot; `MKS.zoomThrough`, whip pans and blur transitions do this in code.
- **An impact every ~3 s** (slam, stamp, shockwave, snap) and one speed change per beat (hold → whip).
  Alternate extreme macro and wide; whiplash the scale.
- **One reveal shot** the film is remembered by (a crowd forming a silhouette, a crane-up reveal,
  the pullback from one row to the whole dashboard).
- Script shape for explainers: cold-open fact → stakes → evidence beats (one number each) → the turn
  ("but here's the thing") → kicker that reframes the opening. Never script from memory: verify every
  number with two sources and keep a Sources list.

## Look A: mixed-media collage (flat, bright, editorial)

- Archival photo cut-outs with rough white paper borders drifting or snapping over flat colour fields
  (warm yellow, off-white paper, deep navy, coral red; one dominant colour per beat).
- Paper grain, halftone dots, torn edges, tape strips, soft drop shadows: `MKS.paperGround`,
  `MKS.paperCut` (torn polygon, white border, tape, stop-motion on twos).
- Hand-drawn annotations: marker circles, underlines, arrows, scribbles that draw themselves and boil:
  `MKS.doodleBoil`. Abstract data graphics (bars growing, lines drawing): `MKS.chartGrid`, `MKFX.chartMorph`.
- Redaction/highlight bars sliding over areas; spotlight dimming the rest (`MK.spotlight`).
- Motion: snappy ease-out entrances with slight overshoot, slow push-ins on "listen to this" beats,
  whip-pans or page-flips between ideas, parallax between collage layers; only one loud thing at a time.
- Typography: captions per `typography-and-captions.md` (bottom-centre subtitles); display words in
  Impact or Garamond italic, never AI-generated lettering inside images.

ChatGPT cut-out prompt (transparent sticker sheets, same chat thread for one look):
"Transparent-background sticker sheet, 3×2, archival photo cut-outs with rough white paper borders,
halftone print texture, editorial collage style, no text, no letters, no logos: [six objects from the
script]." Slice with `chatgpt_slice.py`.

## Look B: paper-diorama documentary (cinematic, sepia, one accent)

For geopolitics, money, power, investigations, or when the user says "cinematic":
aged sepia newsprint worlds, monochrome archival cut-out figures with black censor bars over the eyes,
ONE burnt-orange accent, distressed letterpress, warm tungsten light, macro tilt-shift, film grain,
stop-motion paper feel. Short letterpress words may sit ON props (one label per scene: "EXPIRED",
"WHO BLINKS?"); nothing else readable.

Flow prompt template (Omni Flash, 8 s; one approval per generation, `flow-asset-production.md`):

```
Cinematic vintage paper diorama, aged sepia newsprint world, monochrome halftone print, archival
cut-out figures with black censor bars over their eyes, single burnt-orange accent, distressed
letterpress, warm tungsten light, macro tilt-shift shallow depth of field, film grain, handcrafted
stop-motion paper feel, non-photorealistic — shot as ONE continuous FPV camera move with speed ramps.
The shot: [emerges from motion blur] … [one impact: slam / stamp / rip] … [ends mid-dive, motion-blurred].
No text anywhere except "<LABEL>". No gibberish letters, no captions, no watermark, no live-action.
```

Moderation lessons from the source skill: named politicians and close-up recognisable faces fail on
video models; mid-shot descriptions with censor bars pass; "mushroom cloud" flags (use an hourglass).

## Sound for these looks

Paper rustles, tape rips, stamp thumps, marker squeaks, page flips, a low pulse bed; one impact sound
per impact beat; true peak ≤ −1.5 dBTP (synthesised hits overshoot between samples: roll off highs and
limit on true peak, not sample peak).

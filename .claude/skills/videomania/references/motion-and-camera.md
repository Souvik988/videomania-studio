# Motion, camera and transitions

## Deterministic motion (HyperFrames)
- One paused GSAP timeline on `window.__timelines[<composition-id>]`.
- For complex worlds use the **render(t) pattern**: one proxy tween `{t: 0 → DUR}` whose
  `onUpdate` calls a pure `render(t)` that computes every attribute from `t`. Benefits: exact seek
  determinism, any easing math, path morphs, camera rigs. Verified with `seek_test.py` (pixel
  hashes identical across shuffled seek orders).
- Never in render(t): `Date.now`, `performance.now`, unseeded `Math.random`, network, DOM
  measurement (`getTotalLength`, `getBBox`, `getBoundingClientRect`) — use `pathLength="1"` and
  analytic geometry. Seed procedural noise (mulberry32).
- Never tween `.clip` visibility; no CSS transform + GSAP tween on the same property.

## Easing and timing
- Entrances ease out (power3.out), exits accelerate (power2.in), moves power3.inOut.
- Median move ≈ 10 frames at 30 fps; hops 0.25–0.35 s; big reveals 0.8–1.0 s.
- Land the *peak velocity* on the word onset: start ~0.12 s before.
- Overshoot (`back.out`) at most once per film, on the payoff. No bounce on every word.
- Closed-form spring when needed: x(t) = 1 − e^(−ζωt)(cos ω_d t + ζ/√(1−ζ²) sin ω_d t)
  (underdamped), 1 − e^(−ωt)(1+ωt) (critical); never accumulate state frame to frame.

## Camera
- A camera is a transform on the world group: `translate(W/2,H/2) scale(s) translate(-x,-y)`,
  keyframes `[t, x, y, s]` with per-segment easing; blend in a follow-track for tracking shots.
- Push-in = attention, pull-back = context/reveal, punch-in on the stressed word, whip to the next
  beat. Add a slow breathing drift (≈1–1.5 % scale) so holds are alive.
- Velocity trails (5 ghost copies at −12 ms steps, opacity ∝ speed) approximate shutter blur for
  fast moves. For true subframe blur render at a higher fps and average N subframes with
  `ffmpeg tmix` only when timing is verified; otherwise prefer the trail.

## Transitions (choose per boundary)
Hard cut on action · match cut (shape/position) · object morph (path interpolation) · carried
object continues · camera-through-object · foreground wipe · text-to-object. Default is NOT a
crossfade. Two text cues never cross-dissolve in the same place.

## HyperFrames skills to load on demand
`/hyperframes-core` (contract), `/hyperframes-animation` (rules, blueprints, adapters),
`/hyperframes-keyframes` (camera moves, SVG morph/draw), `/hyperframes-registry` (named effects —
check before hand-building), `/hyperframes-creative` (palettes, frame presets with OFL fonts).

# 5. Animator: make it move like a designer made it

**Job.** Build the composition from the shot list with the style's kit, so motion, camera and timing
are right on every frame.

**Read first.** `storyboard/shots.json`, `brief/motion_brief.md` · `references/motion-kit.md` ·
`references/motion-design-playbook.md` §11–13 · `references/motion-and-camera.md` · the picked
engine's entry pages (`pocket.py show <id>`), and for HyperFrames `/hyperframes-core`.

## Do

1. **Scaffold.** `new_composition.py --project ID --look <look> --format <16:9|9:16> --duration <s>`
   (or the picked engine's own starter). One paused timeline, built after fonts load.
2. **Build from the kit first.** For each shot use the kit part the motion brief names (a blueprint,
   `MK` / `MKFX` / `MKS` parts, a style kit such as `templates/voxel-diorama/`). Fill it from
   `shots.json`. Write new code only for the film's signature moment.
3. **Timing.** Every entrance, exit, camera move and word starts from a time in `shots.json`. Convert
   seconds to frames once and round.
4. **Motion rules** (measured from professional work):
   - Entrances slow and decisive (0.7–1.3 s, `power4.out`); exits quick (0.35–0.55 s, `power2.in`).
   - Stagger siblings 40–90 ms; never start everything on one frame.
   - One easing language per film; springs for objects with weight; nothing linear except counters.
   - The camera is moving at every cut. A move that eases from A to B and stops is a slide.
   - Something changes on screen at least every 2.2 s; nothing rests over 1.5 s unless the hold is planned.
   - Squash and stretch on impacts for 2–3 frames; overshoot then settle.
4b. **The cast acts.** A character that only stands and points is a presenter, not a cast. In every film the
   lead does at least three different actions (walk or run in, a jump or a flight, a sit, a wave, a
   reaction) and at least one that could not happen in real life. Actions go in the shot list as `acts`
   (kit README, "Actions"); a new character comes from one picture through `scripts/sprite_import.py`.
5. **Seek-safe.** Every value is a pure function of time. No free-running loops, no `repeat:-1`, no
   random without a seed. Frame 0 shows the first scene (inline `opacity:1`, `immediateRender:true` for
   tweens starting at 0).
6. **Look as you go.** After each scene, snapshot stills at its start, middle and end and compare with
   the storyboard and the look test.

## Hand over

The composition in `source/`.

## Check

- `npx hyperframes check` reports 0 errors.
- `template_lint.py <source dir>` passes (no slide deck, no single transition everywhere, no miniature
  subject, a persistent hero).
- `seek_test.py` passes: frames rendered out of order match frames rendered in order.
- The choreography audit (`animation-map.mjs`, command in `references/motion-kit.md`) shows no dead
  zone, no identical ease and stagger repeated across scenes.

## Never

- Opacity-only scene changes. The world or the camera moves, or an object carries over.
- Ken Burns on a still as the only motion.
- Two renders at once on this machine.

## Inside the take (2026-11-14)
Tools for change without a cut: `cam.keys` (Catmull-Rom camera path), `wash: [{t,color,k,dur}]`, `flicker` looks, cast `dissolve: [t]` and `acts`, `type.compose` with per-word `C(x,y,{size,rot,tilt,skew,arc})`. Frame the subject on a third; words on the other side; never on the face. See `references/rhythm-and-direction.md`.

## Acting the line (2026-11-14)
Pick each pose from the acting table in `references/mascot-from-photo.md` section 5 (making or building: sit_code; the file: hold_doc; a myth: shrug...), 2-4 acts per long take, a `dissolve` on every pose change, the Claude robot doing its own action at the same time. Depth type: `type.depth`, word `from: "deep" | "near" | "side"`, `z`.

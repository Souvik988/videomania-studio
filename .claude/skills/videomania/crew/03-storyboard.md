# 3. Storyboard artist: every phrase gets a picture, on its word

**Job.** Turn the narration and the direction into a timed shot list the Animator can build without
making story decisions.

**Read first.** `brief/direction.md` · `transcript/` (words with times) ·
`references/storyboard-and-shot-grammar.md` · `references/editor-doctrine.md` §2–5 · the picked style
card's shot grammar (e.g. `references/styles/voxel-diorama.md` §3–4).

## Do

1. **Edit map.** One row per phrase: the idea, the feeling, the stressed word, what the viewer SEES,
   the element type (character, prop, UI, number, type-only, footage, insert), where it comes from, and
   the bridge into the next beat. Save `storyboard/edit_map.json`.
2. **Open loops.** `storyboard/open_loops.json` from `templates/open_loops.json`: the reason to stay
   and the main loop, each with the object that plants it and the object that closes it.
3. **Shots.** One shot per beat, 2–4 s each (0.8 s minimum, 5 s maximum, end card excepted). For each:
   - `id`, `start`, `end` from the word times, never by eye;
   - `shot` type from the style's grammar and `where` in the world;
   - `cast`: who is on screen and their pose;
   - `camera`: the move, and that it is already moving at the cut in and out;
   - `words`: the on-screen words with their times, at most 5 visible at once, and exactly one `punch`
     word per beat;
   - `number` if the line has one (it gets its own beat and counts up);
   - `out`: the transition, with a visible trigger.
   Save `storyboard/shots.json`.
3b. **Moves.** For each beat, search the move library for the beat's job
   (`pocket.py search "<job>" --kind move`) and name the move in the shot. A move is chosen for what it does
   for the viewer; at most two per shot; none more than three times in the film; at least six different
   moves in any film over 20 s.
3c. **Why, second by second.** Every shot gets a `why`: what the viewer expects at this second and how the
   shot confirms or breaks it (`references/cinematography.md`). Put the director's choice in the shot list's
   `meta` (`concept, device, hook, signature, structure, constraint`). Then run
   `python scripts/brain.py check <shots.js> > brief/brain_check.txt`: the novelty gate (differ from each of the
   last 10 films on at least 4 of 7 axes), the surprise budget (a world change at least every 8 s, one
   impossible moment per 20 s, no transition or camera three times in a row) and `why` coverage. It must
   end in PASS. `brain.py beats <shots.js>` prints the plan second by second and marks dead stretches.
4. **Rhythm pass.** Mark dense runs (4–6 short shots) and put one 3 s hold after each. Check no two
   neighbouring shots share the same shot type and camera move.
5. **Match-cut pass.** For each cut, note where the eye leaves the outgoing shot (a point on the
   thirds) and make the incoming shot's subject start there.
6. **Asset list.** From the shots, list every sprite pose, prop, UI screen, icon, image and clip that
   must exist. Mark each: kit part, coded, ChatGPT image, Flow clip (needs approval), or user file.

## Hand over

`storyboard/edit_map.json`, `storyboard/open_loops.json`, `storyboard/shots.json`,
`storyboard/assets_needed.json`.

## Check

- `open_loops.py --project ID` passes.
- Every phrase in the transcript is covered by a shot; no gap over 0.3 s.
- Every punch word's time is within 2 frames of its spoken time.
- A hero is present in shots covering more than 60% of the runtime.

## Never

- Place a cue by eye or on a fixed tempo. Words set the time.
- Put a paragraph on screen. Five words at once is the ceiling.
- Use the same transition for more than half the cuts.

## Rhythm (2026-11-14)
Write chapters, not shots: one take per idea of the voiceover, changes inside it on the word, cuts at chapter turns and in 2–4-cut bursts. Read `references/rhythm-and-direction.md`; `brain.py check` enforces median take 2.5–9 s and 8–22 cuts/min.

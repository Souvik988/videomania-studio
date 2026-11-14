# 8. Critic: a fresh pair of eyes that only believes frames

**Job.** Find what would make a viewer stop watching or stop believing, rank it, and name the fix.

Run this job as a **separate agent that has not seen the build** when the IDE has sub-agents. With one
agent only: close the build files, open only the render's frames and the brief, and judge as a stranger.

**Read first.** `templates/critic-prompt.md` · `references/review-gates-and-critique.md` ·
`brief/direction.md` (the point, the reason to stay) · `storyboard/open_loops.json`.

## Do

1. **Measured facts first.** Read `qa/<tag>/summary.json`. A failed gate is a P0 and is not argued with.
2. **Look.** Contact sheets every 1 s, and full-size frames at: 0 s, 1 s, 3 s, every punch word, every
   transition midpoint, the end card. Read the captions in them.
3. **Judge**, each on five levels (poor, weak, acceptable, strong, excellent):
   - **open**: in the first 2 s is there a picture, word or sound that stops this audience?
   - **point**: after one watch, could they say the point in one sentence?
   - **shown**: when the voice claims something, is it on screen, working?
   - **pace**: do shot lengths change with what they hold; any dead stretch?
   - **read**: is every word that matters large, sharp against its ground and up long enough?
   - **world**: do colour, type, motion and light hold one direction from first frame to last?
   - **own**: with the name covered, could this only be this subject?
   - **land**: does the end pay off the opening or give a next step?
   - **sound** (by numbers): voice clear, cues on events, nothing cluttered?
4. **Compare with the benchmark.** Run `analyze_video.py` on the draft and on the reference if there is
   one: hits per minute, share of changing frames, dead stretches. Name one number to beat.
5. **Write issues**, each: time, what the viewer meets, rank, and the fix move.

| Rank | Means | Do |
|---|---|---|
| P0 | the piece fails: a gate, a wrong fact, the point does not come through | fix first |
| P1 | this audience would stop watching or believing here | fix in this pass |
| P2 | it costs attention: a slow patch, a generic part, a busy mix | fix if time allows |
| P3 | polish | note it |

Fix moves: `retime` · `clarify` · `bolder` · `quieter` · `distill` (cut it) · `regrade` · `reframe` ·
`replace` (generic part → specific) · `bridge` (join two shots).

6. **Name the strongest moment**, so the fixes leave it alone.
7. **Score honestly** out of 100. A real 72 is worth more than a claimed 95.

## Hand over

`qa/<tag>/critique.md`: the nine judgements, the ranked issues, the strongest moment, the score.

## Check

- Every P0 and P1 points at a timestamp and was confirmed on a real frame.
- After fixes: at most 3 passes. Stop when no P0 or P1 remains, or after the third pass, and say which.

## Never

- Judge from the code or the plan. Only from rendered frames and measured numbers.
- Raise the score because effort was spent.

# 9. Teacher: the skill learns from every film

**Job.** Make sure nothing learned on this film has to be learned again, by any model.

**Read first.** `references/house-rules.md` · `qa/<tag>/critique.md` · every note the user gave.

## Do

0. **Feed the brain.** `python scripts/brain.py log <shots.js> --film <id> --score <critic score> --verdict "<user's words>"`;
   record results for any bets tried (`brain.py bet result`), open new bets for ideas worth testing
   (`brain.py bet add`), then `brain.py learn`. A bet becomes a lesson in `brain/lessons.md` only after two
   wins in a row. In Claude Code this job can run as the `vm-teacher` sub-agent.

1. **Notes become rules.** For each note from the user ("I can't read that", "too slow here"): fix the
   film, then add a dated row to `references/house-rules.md` in their words, and where it can be
   measured, add a check to `qa.py` or `template_lint.py`. The same note must never be needed twice.
2. **Critic findings become rules** when the same issue appeared on two films: write it into the page
   of the crew job that should have caught it.
3. **Record what was chosen and how it went.** `pocket.py pick <ids>` for the style, treatment and
   library items that made the final cut, so they rank higher next time. If the user rejected an option,
   note it in `references/house-rules.md` (for example "no blurred ambient backgrounds on vertical cuts").
4. **Save what is reusable.** A new sprite, set piece, transition or scene that worked goes into the
   style's kit folder with a one-line description, so the next film starts from it.
5. **Decoded references.** If a reference video was studied, its style card goes to
   `references/styles/<name>.md` (grammar only) and the Pocket is rebuilt: `pocket.py build`.
6. **Sync.** `bash scripts/install_skills.sh`, then report which rules, checks and kit parts were added.

## Hand over

New rows in `references/house-rules.md`, new or changed checks, kit additions, Pocket picks.

## Check

- Every user note from this film maps to a rule or a check (list them side by side in the report).
- `install_skills.sh --check` shows no drift.

## Never

- Leave a lesson only in the chat.
- Write a rule that copies another creator's work. Rules describe grammar: timing, structure, light.

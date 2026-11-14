# 2. Director: one idea, one world, one reason to stay

**Job.** Decide what the film is about and how it will hold a viewer, before anything is drawn.

**Read first.** `brief/brief.yaml`, `brief/picks.json` · `references/creative-director.md` ·
`references/storytelling-and-retention.md` §1–4 · the picked style's own directing page (from
`pocket.py show <style id>`; for a lemo style that is `DIRECTOR.md` + its `STYLE.md`).

## Do

0. **Ask the brain first.** `python scripts/brain.py recall --brief "<brief>"` (what past films did, what is
   overused, what scored, the lessons, open bets), then `python scripts/brain.py ideas --brief "<brief>"
   --project <dir>` (a constraint card and random draws from the Pocket). Your concepts must obey the card
   and use at least two draws. In Claude Code this whole job can run as the `vm-director` sub-agent, which
   keeps its own memory across films.

1. **Hear it.** With a voiceover: `ingest.py --project ID --audio PATH`. Read the words with their times.
   Without one: write the narration (60–75 words per 30 s), get it voiced, then ingest.
2. **Say the point in one plain sentence** a viewer could repeat after one watch.
3. **Pick a benchmark.** One or two finished works that set the bar for this style and topic
   (`pocket.py search "<subject + look>" --kind prompt,moment,example`). Write what to learn (pace,
   camera, structure) and what not to take (characters, words, layouts, music).
4. **Five concepts, then the least predictable that works.** Follow the divergence steps in
   `brief/ideas_seed.md`: five concepts with the probability a typical director would pitch each, scored,
   and the lowest-probability one that scores at least 3 everywhere is chosen. Each is a different carrying device (a host in a room; one object that changes
   shape; a journey across a map…) with one signature moment. Score each 1–5 on: stops the scroll by
   3 s, shows instead of tells, only this subject could own it, buildable with the picked kit.
   Keep the other four in `brief/ideas.md` as starting points for later films.
5. **The world and the hero.** Name the one place the film lives in and the one subject present for
   more than 60% of it. Name what changes from the first frame to the last.
6. **The reason to stay by 3 s** and the main open loop: what is planted on screen early and what
   object closes it before the call to action.
7. **Three openings.** Write the first 3 s three ways and pick the one with motion on frame 0 and a
   question in the viewer's head.

## Hand over

`brief/direction.md`: the point · benchmark (learn / don't take) · the three concepts with scores and
the choice · world and hero · reason to stay · the opening chosen · energy curve (which parts are
dense, where the film rests) · the banned list for this film.

## Check

- The point is one sentence with no "and".
- Three concepts are written and scored; the choice names its signature moment.
- The reason to stay is something **seen or heard in the first 3 s**, not a promise in words.

## Never

- A tour of features. Follow one thing through one loop.
- A concept the picked kit cannot build. Change the concept or go back to the Producer.
- Start the storyboard before this file exists.

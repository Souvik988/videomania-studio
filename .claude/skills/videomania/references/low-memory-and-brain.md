# Two standing designs: low memory, and a brain that improves itself

## 1. The low-memory rule (4–6 GB of RAM, no big graphics card)

Video Mania must make a finished film on an ordinary laptop. That decides the architecture:

| Rule | Why | How |
|---|---|---|
| **Think in the cloud, draw locally** | Image, video and 3D generation models need 16–24 GB of graphics memory. A laptop has none to spare | Generation goes to services the user already has: ChatGPT images through the codex bridge, Google Flow clips, optional hosted 3D. Nothing generative runs on the machine |
| **Worlds are data, drawn by code** | A set file is a few kilobytes; a 3D program and its scenes are gigabytes | `sets/<name>.json` + the kit's prefabs, rendered by the browser's own GPU path |
| **One browser, one render** | Each render holds about 1–1.5 GB | Never two renders at once; engines render their shots one after another; the master last |
| **Frames stream to the encoder** | Holding frames in memory is what kills small machines | HyperFrames captures and encodes as it goes; never dump PNG sequences for a whole film |
| **Small local models only** | The search index must not need a server | The Pocket uses a 120 MB sentence model on the CPU; depth maps use the Small depth model (about 100 MB) |
| **Sprites and plates stay small** | Texture memory is the limit on a 4 GB card | Sprites at grid size with nearest filtering; plates at 2048 px wide at most; glow and blur in one pass |
| **Heavy things are optional lanes** | A film must never depend on them | raea, splat worlds, Aseprite and hosted 3D add range; the default lane works without them |

Check a machine with `python scripts/vm_engines.py doctor`.

## 2. The director's brain (design; built in phase 5)

The brain is what makes film 50 different from film 1 and better than it. It is files and scripts, so it
works with any model and survives any session.

```
brain/
  ledger.jsonl        one row per finished film: concept, device, worlds, palette, moves, shot mix,
                      hook, critic scores, the user's verdict and notes, retention numbers if known
  lessons.md          rules the brain wrote for itself, each with its evidence and a confidence
  weights.json        how well each style, treatment, move and structure has scored, by context
  experiments.jsonl   open bets: "try X instead of Y on the next explainer", with the result
  beats/              second-by-second maps of the best films: what happened at 0–3 s, 8 s, 20 s, 45 s
```

### The loop (every film)

1. **Recall.** Before planning: the last 10 ledger rows, the lessons that match this brief, the weights.
2. **Diverge.** Five concepts with a probability each, taken from the unlikely end; three random draws
   from the Pocket; one constraint card. A slate of safe, bold and wild.
3. **Novelty gate** (a script): the plan must differ from the last 10 films on at least 4 of 7 axes.
4. **Second-by-second plan.** For every beat the plan says what changes and **why this, why now**:
   what the viewer expects at this second, and how the film confirms or breaks it. A surprise is
   scheduled, never left to chance: a change of world or palette at least every 8 s on average, one
   impossible moment per 20 s, one broken pattern after every three repeats.
5. **Make, measure, criticise** (the crew).
6. **Learn.** The teacher writes the ledger row, updates the weights from the critic's scores and the
   user's verdict, and proposes at most three lessons.

### Self-improvement with a brake

A brain that rewrites its own rules can also talk itself into nonsense. So:

- A lesson starts as a **bet** in `experiments.jsonl`. It becomes a rule in `lessons.md` only after it
  has won on two films (critic score up, or the user said so). One loss sends it back.
- Every rule keeps its evidence (which films) and can be retired. Rules never delete the user's house
  rules, the Flow rules or the honesty rules: those are outside the brain's reach.
- Every tenth film the brain replays an old brief with its current rules and compares the two films
  with the same critic. If the new one is not better, the last rules added are suspect.
- The brain may add kit parts, moves and checks. It may not weaken a check to make a film pass.

### What "why 47 seconds" means in practice

`beats/` stores, for each strong film, the timeline of events with the critic's and (when the user
gives them) the platform's retention numbers. Planning a 45–50 s stretch then starts from evidence:
which kinds of change held attention at that depth in past films, and which were followed by a drop.

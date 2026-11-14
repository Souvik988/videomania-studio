# The crew

A film is made by nine jobs. Each job has one page here. A page says what to read, what to do, the
exact file to hand over, and the check that must pass before the next job starts.

This is how a model of any size makes a film at the level of a strong one: it never holds the whole
craft in its head. It does one job, with that job's page open, and a script checks the result.

## Order

| # | Job | Page | Hands over | Check |
|---|---|---|---|---|
| 1 | Producer | `01-producer.md` | `brief/brief.yaml`, `brief/picks.json` | the user picked from the menu and approved the one-screen plan |
| 2 | Director | `02-director.md` | `brief/direction.md` | 3 concepts scored, 1 chosen, reason to stay by 3 s written |
| 3 | Storyboard artist | `03-storyboard.md` | `storyboard/edit_map.json`, `storyboard/open_loops.json`, `storyboard/shots.json` | `open_loops.py` passes; every phrase has a picture |
| 4 | Art director | `04-art-director.md` | `brief/motion_brief.md`, assets in `assets/` | every asset has a source; palette and type roles fixed |
| 4b | Set builder | `04b-set-builder.md` | `source/sets/<name>.json`, `compare.jpg` | `set_preview.py` colour difference under 0.12; four depths in the wide view |
| 5 | Animator | `05-animator.md` | `source/` (the composition) | `npx hyperframes check` = 0 errors; `template_lint.py` passes |
| 6 | Editor | `06-editor.md` | a draft render | `qa.py --tag draft` passes cadence and caption gates |
| 7 | Sound designer | `07-sound.md` | `audio/master.wav`, `storyboard/sfx_cues.json` | −14 LUFS ±1, true peak ≤ −1.5 dBTP, density caps |
| 8 | Critic | `08-critic.md` | `qa/<tag>/critique.md` | every P0 and P1 fixed or answered on real frames |
| 9 | Teacher | `09-teacher.md` | rows in `references/house-rules.md`, picks in the Pocket | every user note is a rule or a check |

## Where you are

`python scripts/vm_next.py <project dir>` reads the project's files and prints the next job, what to read,
what to write and the check to run. Run it after every job; a new session starts with it.

## The brain

`scripts/brain.py` is the memory and conscience of the crew: it remembers every film (`recall`), forces
variety (`ideas`), refuses repeats and flat plans (`check`), maps every second (`beats`) and learns
(`log`, `bet`, `learn`). Design: `references/low-memory-and-brain.md` part 2.

## Sub-agents with memory (Claude Code)

`.claude/agents/vm-director.md`, `vm-critic.md`, `vm-teacher.md` in the studio repo are sub-agents with their
own memory notebooks. Other IDEs follow the same pages; the brain's files are their shared memory.

## How to run the crew

- **One agent, any IDE.** Work the table top to bottom. Before each job, open its page and only the
  files it lists. Write the hand-over file. Run the check. Go on only when it passes. Say in one line
  which job you are on.
- **With sub-agents** (Claude Code and others that have them). The Critic (8) always runs as a separate
  agent that has not seen the build. The Animator (5) may split scenes across agents once the
  storyboard and motion brief are fixed: one scene per agent, no two agents on one file. Jobs 1–4 stay
  with the lead agent: they are decisions, and decisions split badly.
- **Short on context.** Finish the current job's hand-over file first. The files are the memory: a new
  session reads the project's `brief/`, `storyboard/` and the last check's output and continues from the
  first job whose check has not passed.

## Rules for every job

1. Read the user's house rules (`references/house-rules.md`) before the job's own page. They win.
2. Take the look, style and treatment from the Pocket picks (`brief/picks.json`). Run
   `pocket.py show <id>` and read the files it lists. Never rebuild a style from memory.
3. Use the kit a style ships with before writing new code. New code is for the film's one signature idea.
4. A check that fails is fixed, not explained away. Quote its numbers in the report.
5. Never invent facts, prices, logos, reviews or statistics. Never copy another creator's characters,
   words or layouts: take the grammar only.
6. Measure, don't claim. You cannot hear: judge sound by numbers. You judge pictures on real frames.

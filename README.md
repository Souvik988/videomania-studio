# videomania-studio

Voiceover in, premium motion-graphics film out, with Claude Code (locally or in a Claude Code cloud
session) using the **Video Mania** skill.

## What's inside

| Path | What it is |
|---|---|
| `.claude/skills/videomania/` | the skill: editing doctrine, motion playbook, storytelling and retention rules, house rules, motion kit (springs, morphs, camera, 11 premium effects, 4 looks), scaffold, QA gates, critic |
| `.claude/skills/hyperframes*`, `media-use`, `motion-graphics`, … | HeyGen's HyperFrames skills (Apache-2.0, `HYPERFRAMES-LICENSE`), vendored unchanged: 22 blueprints, 48 motion rules, registry, CLI |
| `research/` | pinned submodules (MIT): **awesome-opus5-5-videos** (703 Opus 5.5 video prompts), **motion-graphics-skills** (Charlie Hills, 16 effect recipes), **herk-edit-kit** (Nate Herk, editing playbook, 406 donor cards), plus (2026-10-29) **iart-ai/motion-skills**, **bang-motion**, **Barty-Bart/motion-graphics**, **Mort1d/motion-graphics-skills**, **opus-video-skills**, **gsap-skills**; distilled in `references/research-digest-2026-10.md` |
| `scripts/cloud-setup.sh` | one-command setup for a Linux cloud session |
| `projects/<id>/` | one folder per film: `input/` voiceover, `assets/flow/incoming/` your Flow clips, `delivery/` the finished film |

## Make the director film on a new machine (any model: Sonnet 5.5, Opus, Fable)

```bash
git clone https://github.com/Souvik988/videomania-studio && cd videomania-studio
bash .claude/skills/videomania/scripts/install_skills.sh    # copies the skill into ~/.claude/skills (and ~/.qoder)
bash .claude/skills/videomania/scripts/bootstrap.sh         # OpenMontage workbench, Python venv, HyperFrames 0.8.166 (needs git, Node 22+, ffmpeg)
```

Then, in Claude Code with any model: `/videomania <voiceover.mp3>` (or a script text). The skill's first screen is a
route table; for a narrated pixel-world film it sends the model to
`.claude/skills/videomania/references/director-film-runbook.md` (12 steps with exact commands, plus a 10-15 s
short-clip lane tested by Sonnet 5.5). `scripts/new_film.py` sets up a project with the bundled starter assets
(`.claude/skills/videomania/assets/voxel-starter/`: mascot, icons, screens, stage backdrop, plates).

Not in the repo on purpose: video clips, voice recordings, the creator's photo, and songs (commercial tracks;
bring your own licensed or royalty-free ones). Image generation uses the `gpt-image-bridge` skill (codex CLI
logged in with a ChatGPT account); without it the starter assets still cover a film.

## Workflow in a Claude Code cloud session

1. Start a cloud session on this repo and run `bash scripts/cloud-setup.sh --smoke` the first time.
2. Push your voiceover to `projects/<name>/input/` and say:
   `/videomania projects/<name>/input/<file>.mp3 --format 9:16`
3. Claude understands the voiceover, researches the motion and designs the film. It then writes
   **`projects/<name>/storyboard/flow_prompts.md`**: one ready-to-paste Google Flow prompt per clip
   the story needs (Omni Flash, your aspect ratio, duration, file name). Then it stops.
4. On your computer, generate those clips in Google Flow, save them with the names on the sheet,
   push them to `projects/<name>/assets/flow/incoming/`, and tell the session "clips ready".
5. Claude ingests and checks the clips, builds the motion graphics, sound and captions, runs every QA
   gate and the critic, renders, and pushes `projects/<name>/delivery/final.mp4`.
6. Pull, or download from GitHub. Files over 100 MB go into a GitHub Release instead.

Google Flow can't run in the cloud because it drives your own signed-in Chrome. Generation always
happens on your machine; everything else can run in the cloud.

## Local use and other IDEs
- **Claude Code** (desktop, CLI or cloud) loads the skill from `.claude/skills/` automatically.
- **Other agents** (Codex, Cursor, …): see `AGENTS.md`.
- On a computer with the Google Flow MCP connected, the skill generates clips directly, with one
  approval per generation. Without it, the skill runs in prompt-sheet mode.
- **This repo is the master copy of the skill.** Improve it here, commit, push. On your PC, run
  `bash .claude/skills/videomania/scripts/install_skills.sh` after pulling, to update the installed
  copies.

## Newest in the skill
- `references/vox-poster-system.md` + `templates/vox-poster/`: the colour editorial "Vox style" poster look, with the critic's lessons.
- `references/research-digest-2026-10.md`: anti-slide-deck tests, hero-and-stations one-take, direction card, sound-pass licence discipline.
- `scripts/template_lint.py`: mechanical anti-template lint for a composition's source.
- **Talking-head reels**: give an image and a voiceover, get an animated talking character with motion graphics. `references/talking-head-reels.md`, `scripts/viseme_track.py`, `scripts/character_parts.py`, `assets/motion-kit/talking-character.js` (+ tests), `templates/talking-head/`.
- `assets/motion-kit/motion-shots.js`: 18 tested shots (MKS).

Credits: see `NOTICE.md`.

## Licences
- Video Mania skill: yours.
- HyperFrames skills: Apache-2.0, © HeyGen.
- Submodules: MIT, © their authors.
- OpenMontage (installed by the setup script, not vendored): AGPL-3.0.
- Bundled fonts: SIL OFL 1.1.

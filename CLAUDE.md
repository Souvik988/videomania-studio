# videomania-studio: instructions for Claude Code sessions in this repo

This repo is a video studio. Its skill `/videomania` (`.claude/skills/videomania/`) turns a voiceover
into a premium motion-graphics film: Claude as an After-Effects-grade editor and motion designer. The
HyperFrames skills it builds on are vendored next to it (`.claude/skills/hyperframes*`, Apache-2.0).
The motion reference libraries are pinned submodules under `research/`.

## First thing in a fresh cloud session
Run `bash scripts/cloud-setup.sh` (add `--smoke` the first time, to prove rendering works here). It
installs ffmpeg, Node 22, Python, HyperFrames 0.8.162 with its Chrome, and OpenMontage (pinned). It
also points OpenMontage's projects at this repo's `projects/` folder.

## The workflow (cloud)
1. The user adds a voiceover at `projects/<id>/input/<file>` and says `/videomania … --format 9:16|16:9`.
   If no format is given, ask (16:9 or 9:16).
2. Follow the skill completely: hear, understand (edit map, open loops, three openings), research
   the motion per beat, design (motion brief, look, brand MOTION.md).
3. **Google Flow cannot run here** (it needs the user's signed-in Chrome). Use the skill's
   **prompt-sheet mode**:
   - write `projects/<id>/storyboard/flow_prompts.md` from `templates/flow-prompt-sheet.md`, using
     only the clips the story needs (Omni Flash, never Veo 3.1, the user's aspect ratio);
   - commit and push it, then **stop** and tell the user how many clips to generate and where the
     sheet is.
4. The user generates the clips in Flow and pushes them to `projects/<id>/assets/flow/incoming/`
   (or attaches them). Pull, then ingest each clip exactly as delivered with
   `flow_ingest.py --file … --expect-aspect … --expect-duration …`. QC every frame. Never crop, mask or
   alter a supplied clip.
5. Build (`new_composition.py` scaffold + motion kit), sound, judge (QA gates, choreography audit,
   critic, at most 3 passes) and finish, exactly as the skill says.
6. **Deliver:**
   - commit `projects/<id>/delivery/` (final.mp4 under 100 MB, captions, quality report, editable
     source) plus the briefs and QA summaries;
   - don't commit drafts, frame dumps or stems over 50 MB (`.gitignore` covers the usual ones);
   - for files over 100 MB, tell the user to attach them to a GitHub Release.
   - Push to the session branch and report the path.

## Standing rules (from the user; full list in `.claude/skills/videomania/references/house-rules.md`)
- Flow video model: Omni Flash only, never Veo 3.1. Aspect ratio: the user's 16:9 or 9:16.
- Motion graphics must not look generic. Research first, then follow the motion brief and playbook.
- No invented metrics, testimonials or brand logos; brand names as plain type unless assets are
  supplied.
- Report only verified facts: measured audio, real QA results, honest critic scores.
- When the user gives a note, fix the film AND write the rule into `house-rules.md` (and a `qa.py`
  check where possible).
- Nothing paid: music and SFX are procedural; no paid APIs.

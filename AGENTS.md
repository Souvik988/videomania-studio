# AGENTS.md: for any coding agent (Codex, Cursor, Gemini CLI, Qoder, …)

Read `CLAUDE.md`: it is the operating guide for this repo and applies to every agent, not only Claude.
The skill itself is plain Markdown plus Python and Node scripts in `.claude/skills/videomania/`. Start
from its `SKILL.md`. Agents that don't load `.claude/skills` automatically should open that file
directly and follow it step by step.

## Making a video, in any IDE and with any model

1. Open `.claude/skills/videomania/SKILL.md` and `.claude/skills/videomania/crew/README.md`.
2. Check the machine: `python .claude/skills/videomania/scripts/vm_engines.py doctor` (clone missing
   engines with `sync`), then `python .claude/skills/videomania/scripts/pocket.py build` once.
3. For a request like "edit this video" or "make a video about X", run
   `python .claude/skills/videomania/scripts/pocket.py menu "<the request>" --has <footage,voiceover,topic,product>`,
   show the user the options, and let them pick. Never choose a style silently.
4. Work the nine crew jobs in order. For each job: open its page, read only the files it lists, write
   the hand-over file, run its check, and go on only when the check passes.
5. Build from the kits and templates the skill ships with. Write new code only for a film's one
   signature idea. Never judge your own work from the code: render frames and look at them, and run
   the QA scripts.

Nothing here needs Claude-only features. Where an IDE has sub-agents, the critic runs as a separate
agent; where it has a question box, the menu uses it. Otherwise use a numbered list.

Setup on Linux or a cloud VM: `bash scripts/cloud-setup.sh`. On Windows or macOS, use the skill's
`scripts/bootstrap.sh`.

Pushing: commit to a branch and open a pull request. Don't commit renders, frame dumps or files over
100 MB (`.gitignore` covers the usual ones). Never commit API keys or `.env` files.

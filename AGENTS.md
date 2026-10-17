# AGENTS.md: for any coding agent (Codex, Cursor, Gemini CLI, Qoder, …)

Read `CLAUDE.md`: it is the operating guide for this repo and applies to every agent, not only Claude.
The skill itself is plain Markdown plus Python and Node scripts in `.claude/skills/videomania/`. Start
from its `SKILL.md`. Agents that don't load `.claude/skills` automatically should open that file
directly and follow it step by step.

Setup on Linux or a cloud VM: `bash scripts/cloud-setup.sh`. On Windows or macOS, use the skill's
`scripts/bootstrap.sh`.

Pushing: commit to a branch and open a pull request. Don't commit renders, frame dumps or files over
100 MB (`.gitignore` covers the usual ones). Never commit API keys or `.env` files.

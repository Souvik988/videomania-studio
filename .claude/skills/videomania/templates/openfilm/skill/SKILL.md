---
name: claude-editor
description: Make a premium motion-graphics film from a voiceover or script with Claude Editor (Video Mania): the creator's mascot in a voxel world, depth typography, songs cast by meaning, editor effects with a hook on frame 0, then edit it here in Studio.
---

# Claude Editor in OpenFilm

The film is built by Video Mania's command layer and lands here as an editable timeline. Run every step with
`python <videomania skill>/scripts/vm.py` (or the `vm_*` MCP tools):

1. `vm new <film> --voice <file> | --script <text> --format reel` · `vm hear` · `vm plan --brief "..."`
2. `vm shots --from-recipe <id>` (recipes: `vm recipe list`), write `source/shots.js`, `vm check`, `vm look`
3. `vm score` · `vm render --reel` · `vm fx plan` (read it) · `vm fx check` · `vm fx apply`
4. `vm openfilm export <film>` -> this folder's film.html: tracks for effects, picture chapters, voice, music
   entrances, hook sounds and the kit's sounds. Change anything here; `vm openfilm diff <film>` shows what changed;
   `vm openfilm render <film>` (or Studio's export at -14 LUFS) delivers it.

Search any preset with `vm presets search "<what the moment needs>"` and ask the director's memory with
`vm brain ask "<question>"`. Pictures: the ChatGPT image bridge provider (Settings -> Services) makes them without a
key; generate assets before drawing in code. Rules: the Video Mania skill's `references/house-rules.md` and
`references/editor-effects-and-hook-sound.md`.

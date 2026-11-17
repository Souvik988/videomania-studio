# Claude Editor: the `vm` command layer (milestone 1, 2026-11-15)

Every editing action is a command. Claude Code calls them as MCP tools (`.mcp.json` at the repo root registers the
`vm` server: 21 tools) or in a terminal (`python <skill>/scripts/vm.py …`). The editor's interface (milestone 2)
calls the same commands. Add `--json` for machine output. Plan and architecture: `docs/claude-editor/PLAN.md`.

## The whole run (tested on `first-second`, an 8.5 s reel, 2026-11-15)

```bash
VM="<workbench venv python> <skill>/scripts/vm.py"
$VM new first-second --script script.txt --format reel     # or --voice vo.mp3; local TTS; reuses the starter assets
$VM hear first-second                                     # word times
$VM plan first-second --brief "<one line>"                # brain recall + ideas + preset suggestions
$VM brain ask "<what you are unsure about>"               # lessons, the user's own notes, past films, doctrine
$VM shots first-second --from-recipe clip10-short         # recipe shot list + storyboard/retime.md
#   Claude writes source/shots.js on the new word times (the creative part)
$VM check first-second                                    # brain gates (+ fx, hyperframes) -> scorecard
$VM look first-second --at 0.3,1.5,3.1,5.9                # snapshots: fix what the frames show, look again
#   audio/score.sh (copy a recipe's), songs cast by meaning
$VM score first-second                                    # mix + measured spread
$VM render first-second --reel                            # 16:9 + the 4:5 reel (one render at a time)
$VM fx plan first-second                                  # editor effects + hook sound from the shot list
#   READ storyboard/fx_cues.json and make the effects say what the lines say (the planner is a draft)
$VM fx check first-second && $VM fx apply first-second    # applies to the film AND the reel, then pads it
$VM deliver first-second                                  # output/<film>/ + srt + shot list + score + cues + report
$VM brain log first-second --verdict "<user's words>"     # ledger + vault; then:
$VM recipe save first-second <recipe-id> --title "..."    # the film becomes a reusable preset
```

`vm status <film>` at any time: nine stages (hear, plan, assets, shots, check, score, render, fx, deliver), the
renders, the scorecard and the next command.

## Presets: one search over everything (`vm presets search "<what the moment needs>"`)

| kind | count | what | use |
|---|---|---|---|
| effect | 41 | editor effects (hook, glitch, camera, distort, light, texture, colour, time, cut transitions) | a cue in `storyboard/fx_cues.json` |
| sound | 59 | hook sounds with sync points (CC0 SFX Kit + our synth) | a cue's `sfx` |
| grade | 296 | film-emulation LUTs (Kodak, Fuji, Polaroid, Agfa, print, b&w) | `vm grade <in> --lut <id> -o <out> [--mix 0.7]` |
| transition | 238 | GL transitions (GLSL; licence per file, most MIT) | WebGL pages / the OpenFilm layer (milestone 2) |
| ae-effect | 308 | After-Effects-equivalent effects (EffectCraft) | EffectCraft's headless MCP, once the user allows running it |
| node | 75 | framefields WebGPU effect and audio nodes | ports |
| recipe | 3+ | whole films | `vm recipe use <id> <film>` |
| + Pocket | 10,625 | styles, treatments, moves, moments, templates, prompts | `pocket.py show <id>` |

Plus OpenFilm's own library (about 5,400 CC0 sounds, transitions, effects, grades, 1,587 stickers, text and film
templates): `npx -y openfilm@latest get <sfx-search|transition|effect|filter|sticker|text|template> --prompt "…"`.

## Recipes (whole films as presets)

`vm recipe list`. A recipe holds the shot list, the score, the fx cues and what assets it needs (the starter set
covers the defaults; songs are never included). `use` on a new voiceover copies them as `*.recipe.*` plus a retime
sheet; Claude keeps the structure and moves and re-times them. Seeded: `director-film` (2 min, approved),
`clip10-short` (10 s), `hook-reel-8s` (8.5 s, the first film made only through `vm`).

## The director's brain v2 (`vm brain`)

An Obsidian-compatible vault at `<workbench>/brain/vault/` (open it in Obsidian to see the graph): the user's notes
verbatim with the rule each became, lessons, every film, effects, sounds, recipes and every doctrine section, all
wiki-linked; searched by keywords + meaning (local e5 ONNX vectors) + one hop along links. `vm brain sync`
rebuilds it; `vm brain log` adds a film. Ask it before deciding anything you are unsure of.

## Gotchas found while building it

- Windows consoles are cp1252: `vm` forces UTF-8 output (notes hold ≤, →, emoji).
- SQLite files must be closed before a rebuild on Windows (fixed in vm_brain / vm_presets).
- `vm fx plan` keeps important cues and drops anything within 1 s of them, which can drop the film's own device
  (a "glitch" word 0.9 s before a "boom" word). Read the plan; put the effect on the word the line names.
- Never run SHARP (3D) or two renders at the same time as a render: 7.4 GB of RAM.

## Milestone 2: the interface (OpenFilm Studio), tested 2026-11-15

```bash
$VM openfilm setup                 # once: the ChatGPT image bridge as an OpenFilm provider (no key) + the claude-editor skill
$VM openfilm export <film>         # <project>/openfilm/film.html: effects / chapters / voice / music entrances / hook sounds / kit sfx
npx -y openfilm@latest open <project>/openfilm     # Studio: open its address in the browser pane, beside this chat
#   the person edits anything (delete an effect, move a song entrance, change a volume, trim a chapter)
$VM openfilm diff <film>           # what they changed, by clip id (fx-1-zoom_punch, music-0-..., hook-braam-0 ...)
$VM openfilm render <film>         # the edited timeline -> renders/<film>_studio.mp4 at -14 LUFS (about 2.5 min for 8.5 s)
```

Verified on `first-second`: the zoom-punch clip deleted by hand in Studio was absent from the Studio render (frame
1.3 s unzoomed), every other effect identical, length exact, -14.3 LUFS / -1.6 dBTP.

- Effects are muted trims of the effect render laid over their moments, so deleting or trimming one in Studio removes
  that effect; moving one does not move the picture under it (re-run `vm fx` for a new timing).
- No caption track by default (the film's kinetic type is the caption; house rule 2026-10-22); `export(captions=True)`
  copies the word times when a subtitle track is wanted.
- Hook sounds are trimmed to the film's end, or Studio's timeline grows past the film.
- Studio keeps open media locked on Windows: the exporter skips unchanged files.
- The chat beside the edit: Studio in the Claude desktop app's browser pane + this Claude Code session with the `vm`
  MCP tools. OpenFilm's own desktop app (with a chat for Claude Code) is an installer download: only with the user's yes.

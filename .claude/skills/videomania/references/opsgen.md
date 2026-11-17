# OpsGen: the video editor (our fork of OpenFilm), driven by the agent

OpsGen is Claude Editor's interface: a real timeline editor (Studio) with a Claude Code chat beside it. The person
watches and nudges; the agent edits through commands, which cost a few tokens each. Source: `opsgen/` in the
videomania-studio repo (MIT fork of OpenFilm v0.3.2, rebranded by `opsgen/scripts/rebrand.py`; see `opsgen/NOTICE.md`).
Build tree (outside OneDrive): `~/video-production-workbench/opsgen`, kept in step by `bash opsgen/opsgen-dev.sh`.

## Rule 1: editor first (user's rule, 2026-11-15)

"Every time you start editing, first launch the video editor, so I can see everything visually." So before any edit:

```bash
bash <repo>/opsgen/opsgen-dev.sh desktop        # OpsGen Desktop: Studio + the Claude Code chat (once per session)
vm studio <film>                                # the film opens in it; every later vm stage updates the timeline live
```

`vm studio` exports the film (`<project>/openfilm/film.html`), opens it in the running OpsGen (the desktop app's
Studio when it runs: `~/.opsgen-dev`, port 4757; else the web Studio), and marks the film live: `vm hear`, `vm score`,
`vm render` and `vm fx` re-export when they finish, so the person sees the voice land, then the music, the picture,
the effects. No mouse: everything below is a command.

## Rule 2: read the timeline cheaply, edit it with operations

```bash
vm tl <film>                        # (= opsgen tl --film <project>/openfilm) one line per track, every clip id and time
vm edit <film> '<op or [ops]>'      # atomic: all apply or none; prints what changed and the new timeline
```

| op | fields | what |
|---|---|---|
| add | src, at, track?, in?, out?, len?, id?, volume?, speed?, style?, class?, box{x,y,w,h,r} | a clip (track: index, "new", "new-top"; else the first free track of its kind) |
| move | id, at? / by?, track? | |
| trim | id, in?, out? | source seconds |
| len | id, dur | length on the film |
| set | id, volume?, speed?, muted?, disabled?, style?, class?, box? | |
| delete | id, ripple? | ripple closes the gap |
| dup | id, at, track? | |
| split | id, t | -> id, id-b |
| ramp | id, speeds [[dur, speed], ...] | speed ramp (slow-mo into normal, etc.) |
| freeze | id, t, dur | hold a frame (the still is made), ripple after |
| kf | id, frames {"0%": "scale: 1", "100%": "scale: 1.1"}, dur?, ease?, delay? | keyframed motion / opacity / rotate (CSS) |
| fade | id, in?, out? | picture and sound fades |
| ripple | track, from, by | shift a track |
| track | add / remove / lock / unlock / mute / unmute / hide / show | |

Everything OpenFilm's format can say still works in film.html (pages with `window.film.frame(t)`, CSS looks, masks,
blend modes, captions); `opsgen look` checks determinism and loudness; `opsgen render` exports.

## Rule 3: footage edits (new pixels or sound)

`vm media -h`: reverse, stabilize (vid.stab), denoise (voice), key (chroma -> VP9 alpha), reframe (16:9 -> 9:16 with
a virtual camera that follows the subject: saliency + motion [+ depth], dead zone, eased), track (CSRT -> keyframes
that pin an overlay), beats (cut points of a song), broll (a picture/clip on a spoken word, faded). Colour: `vm grade`
(296 film LUTs). Editor effects + hook sound: `vm fx`. Silence/retake cuts: `scripts/cut_speech.py`.

## The chat

OpsGen Desktop's chat runs a real Claude Code session (Anthropic's ACP adapter, the person's own login) in the film's
folder. OpsGen gives it the `vm` MCP tools (from `~/.opsgen/agent-mcp.json`, written by `vm openfilm setup`) and the
Claude Editor instructions (`opsgen/apps/desktop/src/agent-prompt.md`). Typing there = typing in Claude Code.

## Can every edit be done?

| an editor does | OpsGen / vm |
|---|---|
| cut, trim, split, ripple, move, duplicate, tracks | `vm edit` |
| speed, ramps, freeze, reverse | `vm edit` (speed, ramp, freeze), `vm media reverse` |
| keyframes: position, scale, rotation, opacity | `vm edit kf` |
| transitions, effects, glitch / warp / shake / flashes, LUTs | `vm fx`, OpsGen library transitions/effects, `vm grade` |
| titles, kinetic type, captions | pages / the voxel kit, OpsGen text templates, caption tracks |
| masks, blend modes, picture-in-picture, split screen | CSS on the clip (`set style`), `vm media broll --mode pip/split` |
| chroma key, background removal | `vm media key`, `greenscreen_key.py`, OpsGen cutout (local BiRefNet) |
| stabilisation, reframing, motion tracking | `vm media stabilize / reframe / track` |
| audio: volume, fades, ducking, denoise, music by meaning, beats | `vm edit set/fade`, `sound_mix.py`, `vm media denoise / beats` |
| B-roll from words, generated stills, stock | `vm media broll`, image bridge provider, OpsGen get (with keys) |
| export: 16:9, 9:16, 4:5 reel, stems, subtitles, NLE timelines | `vm render --reel`, `opsgen render`, Studio's export (FCP / Premiere / Resolve) |
Not yet: multicam sync, nested sequences, true 3D compositing inside Studio (3D is built in the voxel kit pages).

## Keeping the fork current

Upstream changes: copy a newer OpenFilm into `opsgen/` (keep our files: `scripts/rebrand.py`, `opsgen-dev.sh`,
`NOTICE.md`, `TRADEMARK.md`, `UPSTREAM_COMMIT.txt`, the logos, `packages/openfilm/src/agent-edit.mjs`, the agent prompt
and MCP patch), run `python scripts/rebrand.py`, then `bash opsgen-dev.sh install` and the tests.
Gotchas met: never rename identifiers by plain text (property names, object keys); rename module paths, visible text,
env vars, the data folder; files named after the brand must follow their imports; Git Bash rewrites `/MIR`-style
arguments (MSYS_NO_PATHCONV); OneDrive must never hold node_modules.

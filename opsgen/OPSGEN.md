# OpsGen

The video editor of Claude Editor: built for an agent to drive and a person to watch. A fork of OpenFilm (MIT; see
[NOTICE.md](NOTICE.md)) with the OpenFilm name and logo replaced, and these additions:

| addition | where |
|---|---|
| **Agent edit layer**: `opsgen tl` (the whole timeline in a few lines) and `opsgen edit '<ops json>'` (add, move, trim, len, set, delete, dup, split, ramp, freeze, kf, fade, ripple, track), atomic and validated by the format's own parser | `packages/openfilm/src/agent-edit.mjs`, `bin/opsgen.mjs` |
| **Claude Code in the chat by default**, with the Claude Editor (`vm`) MCP tools handed to every agent session from `~/.opsgen/agent-mcp.json` | `apps/desktop/src/agents.mjs` (`opsgenMcpServers`) |
| **Claude Editor instructions** for the chat agent (commands first, the director's memory, asset-first, hook on frame 0) | `apps/desktop/src/agent-prompt.md` |
| OpsGen mark and icons | `BrandLogo.tsx` (studio and chat), `docs/logo-*.svg`, `apps/desktop/build/icon*` |
| scripted rebrand, so upstream OpenFilm can be merged again | `scripts/rebrand.py` |
| dev loop outside OneDrive (sync, install, desktop, studio, tests) | `opsgen-dev.sh` |

The Claude Editor side (the Video Mania skill) adds `vm studio` (editor first, live timeline), `vm tl` / `vm edit`,
`vm media` (reverse, stabilize, denoise, key, reframe, track, beats, broll), `vm openfilm setup` (image-bridge
provider, skill, MCP file). See the skill's `references/opsgen.md`.

```bash
bash opsgen-dev.sh install     # once
bash opsgen-dev.sh desktop     # OpsGen Desktop: Studio + Claude Code chat
bash opsgen-dev.sh test        # the package tests
```

Not supported here: macOS packaging (the .icns icons were removed with the OpenFilm logo), OpenFilm's hosted service
under OpsGen's name (it is OpenFilm's: the provider keeps its own name).

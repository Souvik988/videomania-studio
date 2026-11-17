# sfx-hook: the hook-sound library (59 sounds)

- `kit/*.ogg` — 51 sounds picked from **SFX Kit by Wyzowl** (CC0-1.0, https://github.com/wyzowl/sfx-kit): cinematic hits,
  booms and sub drops, risers and reverse whooshes, whooshes, digital glitches, stings, impacts. Converted to OGG.
- `synth/*.wav` — 8 original sounds from `scripts/hook_sounds.py` (CC0): braam, braam_short, ominous_swell, tear,
  sub_hit, heartbeat, tape_stop, shutter_stutter.
- `manifest.json` — every sound with `sync_at` (the instant that lands on the picture), measured `lufs`, tier,
  description, use_for / avoid_for, source and licence. Search: `python scripts/sfx_library.py find "<words>"`.

Rebuild: `python scripts/hook_sounds.py && python scripts/sfx_library.py build --kit <research>/wyzowl_sfx-kit`.
Used by `scripts/fx_pass.py` (rules: `references/editor-effects-and-hook-sound.md`). All CC0: safe in the public repo.

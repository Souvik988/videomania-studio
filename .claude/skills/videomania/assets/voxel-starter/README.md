# voxel-starter: the approved assets of the director film

Everything a new voxel-diorama film needs, so a fresh install can make the same kind of film without
generating anything first (`scripts/new_film.py` copies this folder into the project by default).

| folder | what | made by |
|---|---|---|
| `mascot/me/` | the creator's picture mascot: 17 poses (`talk point walk jump sit_code think cheer wave run floor_code shrug fly hold_doc surprised holo_type thumbs idle`) + a depth map per pose + `poses.json` | ChatGPT image bridge from the creator's photo, cut by `pose_sheet.py`, depth by `pose_depth.py` |
| `gen/icons/` | 10 glossy 2.5D icons: prompt, script, storyboard, animation, captions, skill, sound, mix, voiceover, course | ChatGPT image bridge |
| `gen/*.png` | app screens (`editor_ui`, `code_skill`, `viral_feed`) and the orange stage backdrop (`stage_backdrop`) | ChatGPT image bridge |
| `plates/` | photoreal/painted worlds + depth maps: `open_world` (meadow), `cosmos`, `loft`, `vista` | ChatGPT image bridge + `vm_depth.py` |
| `cast/fox.png` | a small extra cast member | ChatGPT image bridge |

**Not included, on purpose (this repo is public):**
- video files and frames cut from them (`assets/clips/...`): regenerate from a draft render (runbook Step 3);
  `scripts/split_frames.py` rebuilds the split-monitor frames from `gen/` pictures;
- songs: the director film used commercial tracks for private viewing only. Put your own royalty-free or
  licensed songs in `<project>/audio/music2/` and run `scripts/music_map.py` on them
  (`references/audio-cinematography.md`);
- voice recordings and the creator's source photo.

The mascot is the creator's likeness. To make a different host, follow `references/mascot-from-photo.md`
with another person's photo (with their permission) and put the result in `source/assets/mascot/me/`.

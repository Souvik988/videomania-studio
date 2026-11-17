# 7. Sound designer: judged by numbers, timed to pictures

**Job.** Voice clear over everything, music that marks the structure, effects that land on what the
viewer sees.

**Read first.** `references/background-music-and-sound.md` · `storyboard/shots.json` ·
`references/research-digest-2026-10.md` §5.

## Do

1. **Voice.** `make_audio.py` cleans the voiceover. It is the timing master and is never stretched.
2. **Music.** Pick a bed that matches the energy curve in `brief/direction.md`
   (`pocket.py search "<mood, tempo>" --kind music`). Put the film's turns on the music's downbeats
   where the words allow. Duck under the voice.
3. **Effects.** One cue per picture event that deserves one: `sfx_design.py` (taps, whooshes, booms,
   risers, typing, message send, ding, ka-ching, coins, ticks, paper, glitch) or library sounds
   (`pocket.py search "..." --kind sound`). Every cue in `storyboard/sfx_cues.json` names the picture
   event and its time. Pixel styles use chiptune-like cues; paper styles use paper.
4. **Density.** At most one boom per 10 s. On average at most one cue per 0.8 s. No stack of three
   effects within 50 ms.
5. **Mix.** Master to −14 LUFS integrated (±1), true peak at or below −1.5 dBTP, voice at least 6 dB
   over the bed while speaking.
6. **Measure the exported MP4**, not an intermediate file.
7. **Credits.** Every track and sound has a known source and licence in `CREDITS.txt`. CC0, the OpenFilm
   library and Mixkit Free are the safe classes.

## Hand over

`audio/master.wav`, `storyboard/sfx_cues.json`, `CREDITS.txt`, and five timestamps for the user to
check on a phone speaker.

## Check

- Loudness and true peak in range on the final MP4 (`qa.py` prints them).
- Every cue has a picture event within 2 frames.
- Density caps hold.

## Never

- Write "it sounds good". You cannot hear. Report the numbers.
- Use a track with an unknown or non-commercial licence in a film that will be published.

## Measured mix (2026-11-14)
Run `scripts/sound_mix.py`: SFX from the shot list (plus flicker, wash, dissolve), music phrased by chapter spans with drop-outs, ducking ≤ 6 dB, two-pass −14 LUFS. Match the reference spread p10/p50/p90 −22.1/−14.4/−11.7 LUFS within 1.5 dB. SFX hits sit level with the voice. Give the user timestamps to check on a phone.

## Score by meaning (2026-11-14)
`scripts/music_map.py` on every song, then a casting table (span, words, song, why) and `sound_mix.py --cue file@offset:t0-t1 ... --dip ... --amb ...`. Rules in `references/audio-cinematography.md`. Keep the command in `audio/score_vN.sh`.

## Music level for this user (2026-11-14)
`sound_mix.py --music-db -22`: the user asked for the music "a little louder" than -26. Keep the cue script in
the project (`audio/score.sh`, shape of `templates/voxel-diorama/examples/director-film-v5.score.sh`).

## Hook sounds (2026-11-15)
The first frame gets a layered ominous stack (transient + braam + sub drop) and every effect a paired sound placed on
its sync point (`assets/sfx-hook/manifest.json`, search with `sfx_library.py find`). `fx_pass.py apply` places and
level-matches them and re-finishes the film to -14 LUFS / -1.5 dBTP. Risers end ON the cut; hits start on the frame.

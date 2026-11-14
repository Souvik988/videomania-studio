# Audio cinematography — score by meaning, not by laying a track underneath

From the director film v3 (2026-11-14). The user gave six songs and said: "I don't want it just put behind.
Understand the music, understand the feeling, use the catchiest one for the context; sometimes go a cappella."
You cannot hear. You can measure, and you can reason about what a song means. Do both.

## 1. Map every song first

```bash
python <skill>/scripts/music_map.py audio/music/*.mp3 -o audio/music_map.json
```

Per song: bpm, bar length, key/mode, drive (beat-led vs melody-led), energy per bar, sections
(low/mid/high with start times), the 16 biggest hits, clean entry points, and words for its character.
Add what you know about the song itself (its title, its famous moment, whether it has vocals and where).

## 2. Cast the songs like actors

Write a table: film span → words spoken → song → why. Rules:
- A song's **meaning** must fit the line (the director film: ABBA "Gimme! Gimme! Gimme!" under "everyone's
  asking the same thing" = everyone saying "gimme the prompt", and again under "Want the file?";
  a heroic battle theme on "A director"; a heist-swagger jazz on "no magic prompt / not a course";
  a string orchestra on "script, storyboard, animation… a whole crew"; a warm sunset synth on "that's you").
- **Change songs only at chapter turns**, on the word that turns the story.
- **No vocals under the voice-over.** Use instrumental parts only (intros, breaks); vocals start = cue ends.
- **Bookend**: the song of the hook comes back at the end.
- Use 4–7 songs in a 2-minute film; one song per idea, never a song "for variety".

## 3. A cappella on purpose

Silence the music where the words must land alone: the hard "WRONG" (cut the song dead on the word),
the confession ("here's the part nobody tells you"), the suspense ("but first…"). 3–10 s each, 2–4 per film.
SFX still play — silence of music, not of sound.

## 4. Enter on the grid

Every entrance: film time = the word; file offset = a downbeat (from the map) or the song's first hit,
so the song's hit lands on the word. To make a section arrive on a later word, compute the offset backwards
(the sunset song's big section at 17.2 s landing on "YOU." at 99.64: start at 90.98 with offset 8.475,
a downbeat). Hard entrances: fade-in 0.02–0.04 s; soft ones 0.6 s.

## 5. Literal moments (the jokes the ear gets)

- "Lower that voice" → the music drops 15 dB for that phrase (`--dip 87.6-88.45:-15`).
- "Hold it one beat longer" → the song ends one beat after the word.
- Source music: when the picture shows a screen or a speaker, the song starts muffled (`lp=1100`) as if from
  that speaker, then opens up full when we go "inside" (meadow monitor → pixel world).
- Real-world shots get ambience (wind, birds: `--amb 0-3.4`).

## 6. The command

```bash
python <skill>/scripts/sound_mix.py <project> --shots shots.js --voice input/vo.mp3 \
  --amb 0-3.4 \
  --cue audio/music/gimme.mp3@1.1:1.6-3.24:gain=-4:lp=1100:in=0.6:out=0.05 \
  --cue audio/music/gimme.mp3@2.74:3.24-5.8:in=0.02:out=0.04 \
  --cue audio/music/ngahhh.mp3@0.093:15.12-22.4:out=0.5 \
  --dip 87.6-88.45:-15 ...
```

`file@offset:t0-t1[:gain=dB][:lp=Hz][:in=s][:out=s]`. Songs are level-matched by loudness automatically;
music sits ~18–20 dB under the voice, ducking ≤ 6 dB, SFX hits level with the voice. **This user wants the music clearly audible:** use `--music-db -22` (v5, "a little louder" than v4's -26). The approved score is `templates/voxel-diorama/examples/director-film-v5.score.sh`. Keep the script
of cues in the project (`audio/score_v3.sh`) so the next version can change one line.

## 7. Check without ears

- The mixer prints the momentary spread; target the reference's p10/p50/p90 (−22.1/−14.4/−11.7) ±1.5 dB.
- Print the music stem level per second and confirm silence where you meant a cappella and music where
  you meant music (`audio/stems/music_bed.wav`).
- Tell the user the timestamps of every entrance, drop and joke to check on a phone speaker.

## 8. Licences

Commercial songs (ABBA, game soundtracks, recordings of classical works) are fine for the user's private
viewing; say so plainly and never publish or deliver them for a client without a licence. For anything that
will be posted, use CC0 / royalty-free music (OpenFilm library, the royalty-free tracks the user supplies).

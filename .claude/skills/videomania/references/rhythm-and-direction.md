# Rhythm and direction — chapters, not a slideshow

Read this before writing any shot list for a narrated film. It is written for every model that runs the
skill (Fable, Opus, Sonnet, others): follow the numbers, they come from measuring the user's reference reel
and from the user's notes on the director film v1 (2026-11-14).

## What went wrong in v1 (the user's words, summarised)

- "Every 2–3 seconds something different… it doesn't feel rhythmic, it feels like you were forcing it."
- The start had no impact; the reference starts differently.
- "I can't hear the sound": no audible SFX, the music bed was a constant hum.
- The type did not bend or go around the subject; the picture was too blurry; the mascot was stiff.
- "You don't have to copy his direction, build your own, but it has to be the rhythm."

v1 had 42 shots in 113 s (22 cuts a minute) because a brain gate demanded a world change every 8 s.
The gate was wrong; it is rewritten (`brain.py check`, lesson L-1).

## 1. Rhythm = chapters that change inside the take

The reference cuts **at chapter turns**, not on a clock. Measured hard cuts (s): a flicker burst at
0.1–0.6, then 6.9, 7.9, 11.0, 13.4, 15.1/15.2, 17.2, 18.7, 20.3, 22.3, 24.5/24.8, 28.4, 32.1/32.4, 37.8,
a burst 39.7–39.9, 40.7/40.9, 42.9/43.0, 55.5/55.7, 58.6 — then **one 22-second take** to 80.5 — then
80.7, 82.4, 85.3, 86.9, 87.9, 96.3. About 16 cuts a minute counting bursts; takes of 1 to 22 s.

Rules:
- A **chapter** is one idea of the voiceover (a question, an answer, a list, a reveal). One take, 2.5–20 s.
- **Change inside the take on the word**: a camera key, a word group, a wash of colour, a pose, a card, a
  burst, a pixel dissolve. Something new every 2–3 s — but it rides the sentence, so it feels like rhythm.
- **Cut** only when the voiceover turns (new chapter), and in **bursts** of 2–4 very short cuts (0.1–0.3 s)
  at the big beats. Two cuts 0.2 s apart read as a hit; cuts evenly spaced every 2.5 s read as a metronome.
- Hold the longest take for the richest moment (the reference holds 22 s on its list/demo). Fill it with
  word-level change, never with cuts.
- Targets the gate checks: median take 2.5–9 s, 8–22 cuts a minute, at least 3 world changes in 40 s+,
  every take over 6 s has a change at least every 2.5 s.

## 2. The opening (first 2 s)

The reference opens on a **flicker burst**: 4–6 looks in 0.6 s (negative, red silhouette, mono, normal),
each with a glitch tick, then a fast push into the subject. No fade-in, ever. Kit: shot 0 gets
`flicker: { t: [0, 0.6], looks: ["negative","red","mono","normal","red","normal"] }` plus `cam.keys`
pushing in, and the first composed words land by 1.0 s. The first sound is a hit, not a rising bed.

## 2b. Real world to pixel world (v3 opening, the user's note on the reference)

The reference opens in a world that feels real (grass, a computer standing in a field) and a moment later
drops into the animated world. Recipe: generate a photoreal plate with the ChatGPT bridge (a lone desk
and monitor in a meadow, golden light, sharp foreground grass), make its depth map (`vm_depth.py`), use the
kit set `meadow` (relief plate, pollen dust, outdoor light), push the camera with `cam.keys` from wide
into the monitor in about 3 s while the first words fly in from depth, and leave with `out: "pixelate"`: the
real picture breaks into pixels and the next shot is the pixel world. Sound: wind and birds, the hook
song muffled "from the computer", opening up full on the pixel cut (`references/audio-cinematography.md`).
Any later world switch can reuse it: real to pixel, pixel to real.

## 3. Type that bends and goes around the subject

- Frame the subject on a third (camera `look` offset to the other side); words take the empty side.
- `type: { compose: true }` and give each word its own place: `C(x, y, { size, rot, tilt, skew, arc })`.
  Mix sizes 0.55–2.3, rotations ±3–8°, a `tilt` (3D lean) on one word per group, an `arc` on the last word.
- Words never sit on the face. Leave at least one word-height between lines; check in snapshots.
- Letters flicker in colour and settle (default); keep `flicker: false` on bright sets where the flicker
  colours lose contrast (the orange stage).
- The previous group stays faintly (28 %) for one beat, so the frame builds instead of wiping.
- Dark ink (`ink`, `punch`) on bright worlds.
- **Depth** (`type: { depth: true }`, on everywhere in v3): words fly in from deep space (`from: "deep"`),
  from behind the lens (`"near"`, use it for the punch word) or the side (`"side"`); each word can sit at its
  own depth (`z`, px); the group drifts slowly in 3D while on screen and the previous group recedes
  700 px back and turns away. This is the "typography moving in 3D space, going in depth" the user asked for.

## 4. Picture clarity

The reference keeps backgrounds **clear**. Default lens: aperture 0.38, maxBlur 9, grain 0.022. Use heavy
depth of field only when it is motivated (a rack focus to a prop, a dream world). Never blur every shot.

## 5. The mascot acts

Pose changes go through a pixel dissolve (`dissolve: [t…]` on the cast entry, 0.48 s) so the character
re-forms instead of popping. Give each take 2–4 acts (pose, point, talk, jump, wave) on the words.

## 6. Sound you can hear

Use `scripts/sound_mix.py` (it builds SFX from the shot list and phrases the music by chapter):

- **Music is phrased**: it plays in chapter spans and **drops out** for the dramatic beats (the void
  chapters, the reveal); switch track at the film's turn. Music sits ~20 dB under the voice.
- **Gentle ducking**: ≤ 6 dB, 30 ms attack, 350 ms release. Never 7:1 pumping.
- **SFX are loud**: hits level with the voice (0 dB vs voice RMS), +4 dB more when they land in a speech gap.
  Every transition, punch word, 3D word, dissolve, wash and flicker tick has a sound.
- **Measure**, because you cannot hear: momentary loudness (ebur128 M) p10 / p50 / p90.
  Reference: −22.1 / −14.4 / −11.7 LUFS. v1 (failed): −19.6 / −15.0 / −12.2. v2: −21.1 / −14.9 / −11.5.
  A floor (p10 − p50) shallower than −5 means the bed fills every gap; a top (p90 − p50) over +4 means
  the SFX are too hot.
- Master −14 LUFS, true peak ≤ −1.5. Tell the user which timestamps to check on a phone speaker.

## 7. Your own direction, their rhythm

Do not copy the reference's shots. Keep its rhythm (chapters, bursts, change on the word, the long take)
and invent the worlds, the camera paths and the gags. Write a `why` for every take.

## Checklist before rendering

1. `brain.py check shots.js` passes (rhythm gates).
2. Snapshots at the first 2 s and one frame per chapter: no word on a face, no word off-frame, no overlap.
3. `sound_mix.py` spread within 1.5 dB of the reference on p10/p50/p90.
4. `npx hyperframes check` passes contrast.

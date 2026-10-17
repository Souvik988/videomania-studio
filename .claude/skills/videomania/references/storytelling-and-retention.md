# Storytelling and retention: why a viewer stays to the end

Distilled 2026-10-17 from Nate Herk's **herk-edit-kit** (MIT, github.com/nateherkai/herk-edit-kit;
local copy at `video-production-workbench/research/herk-edit-kit/`). Its numbers come from
measuring 27 top-performing reels frame by frame and from dozens of edit rounds in which every
note the creator gave became a permanent rule. Use them as a starting point, not as law.
`editor-doctrine.md` decides what the viewer sees, `motion-design-playbook.md` how it moves; this
file decides **why they keep watching**. It applies to every edit; the reel numbers apply to 9:16
short-form.

## 1. Priority one: a reason to stay, by 3 seconds

Before any aesthetic judgement, ask: **"In the first 3 seconds, is someone convinced they need to
watch until the end?"** "That looked cool" is not an answer. Record the specific benefit, the
unresolved question and the payoff time in `storyboard/open_loops.json` (`opening`).
- Speech or a meaningful image starts within 0.1 s. There's no logo bumper, no slow fade-up and
  no caption-only first frame.
- The first frame is already meaningful: the topic's object, product or person, in motion.
- The first cut lands at 0.6–1.0 s, on the first charged word.
- **Draft three openings** that lead into the same narration (problem first, result glimpse,
  recognition first). Render each opening's first 3 seconds cheaply (a snapshot strip is enough),
  compare them, and record the choice and the reason.
- Never manufacture a claim for a hook, withhold the topic, or fake a failure. Keep the
  narration's qualifications.

## 2. The story spine (map the narration onto it before designing)

1. **Hook** (0–3 s): a claim or question that names the subject.
2. **Context or credibility**: one line.
3. **Open the loop**: plant a specific unresolved state the viewer can see, such as three empty
   slots, a locked panel, two parts that don't fit, or the list's items shown early but blurred.
4. **Items or proof**: each spoken item gets its own shot, with a section mark, a one-line
   definition, two or three literal visuals, and emphasis on the key line.
5. **Resolution**: closes the loop with the **same object, completed**, and calls back to the hook
   visual.
6. **CTA**: show the resource or action first, then the words. Hold it at least 3 s.

## 3. Open loops done properly (`storyboard/open_loops.json`)

- **One main question**, with short subordinate questions, rather than many unrelated mysteries.
- The loop has an **object**: the thing on screen that holds the open state. Plant it (`setup`),
  move it with partial answers (`updates`), and close it (`closure`) before the CTA with the
  narration's own words (`supportingSpeech`, quoted verbatim).
- An object that reappears without resolving anything is a callback, not a closed loop. A row of
  ticks is not a payoff. The problem graphic itself must change state.
- Don't show all the answers on the first card. That closes a list loop at once.
- `scripts/open_loops.py --project ID` validates the ledger; `qa.py` runs it as a gate. Whether the
  question is actually clear is judged on rendered frames.

## 4. One persistent world (for explainers, ads and anything with a system to show)

Cutting to a new graphic costs the viewer their bearings every time. Moving through a space that
stays put costs nothing.
- **The world never resets.** What the viewer has seen stays where they left it. New material is
  added to it. Once drawn, an element is never redrawn, moved or relabelled without meaning.
- **Spatial grammar, decided first and held.** For example: left to right is toward the outcome, up
  is toward a person (the only warm colour), down is into the system. Break it **once**, on
  purpose, for meaning.
- **The camera is the edit.** Work at three altitudes and move between adjacent ones:

  | Altitude | Shows | Used for |
  |---|---|---|
  | World | the whole space | orienting, payoffs, "here is where we are" |
  | Region | the part under discussion | most of the runtime |
  | Detail | one element | a number, a state change, a decision |

  Jumping from detail to world is disorienting, except as the payoff pull-back, where it is the
  best move available.
- **Frame with exact windows, not scale factors.** Window edges fall between labels. Reuse the same
  window for the same purpose. Vary move duration with distance travelled.
- **No label within 60 px of the frame edge**, solved by placement, not masking.
- **The camera and a full-frame wipe run in sequence, never overlapping.** A cover goes opaque
  before the camera moves under it. Two sequential moves on one subject read as a glitch, so merge
  them into one gesture with a shared ease.
- **Attention is a spotlight.** Exactly one element is at full brightness at any moment; everything
  else already drawn stays quiet but legible. Hierarchy comes from the ratio, not from darkening
  everything:

  | State | Luma (16–235) | Opacity |
  |---|---|---|
  | active stroke and label | 200–235 | 1.0 |
  | context, still relevant | 120–150 | ~0.56 |
  | spent | 85–105 | ~0.33 |
  | any label, any state | never below 90 | |

- **If it doesn't get a word, it doesn't get drawn.** Every element on screen is named by the
  narration.

## 5. Pacing (9:16 short-form house numbers; scale with judgement for ads and explainers)

- Shots average **1.1–1.4 s**, none over about **2.8 s**, unless it's a declared story hold.
  Motion-graphics films change through morphs and moves as well as cuts, so cadence is judged on
  visible changes: `qa.py` fails any stretch over **2.2 s with no visible change** outside
  `--allow-holds`.
- A new element arrives every 0.3–0.6 s inside a busy scene. Every 7–8 s of density, give a 1 s
  rest beat. Density rises, briefly releases, then resolves. Avoid metronomic cuts.
- Change action, scale or camera only when it adds information. Alternate assembly, detail, human
  expression, evidence and a resolved wide view.
- No dead air in the voice. Never speed narration up. When cutting speech, cut **between phrases,
  never inside one** (see `edit_clip.py` / `cut_speech.py`).

## 6. Footage and B-roll (what keeps a frame alive)

**Video beats images, every time.** Preference order:
1. real footage of the thing named;
2. a real screen recording, zoomed to the part being discussed, with a visible cursor;
3. an animated UI mock (typing, rows ticking, a counter climbing), labelled as an example;
4. generated video (Google Flow, Omni Flash) as a **concrete metaphor** ("burning money" = a bill
   burning), never generic "person at a computer";
5. under-1 s highlight crops of a real page on names, prices or badges.

Rules from mistakes:
- **An AI still used as B-roll is a build error.** A Flow still is only a first frame for a Flow
  video, or a static texture inside a moving composition.
- AI video often changes camera angle around 2.5–3 s and turns on-screen text into gibberish. Use
  the first continuous seconds, and keep screens small in frame.
- Consecutive AI shots of the same person must match: same outfit, same room, same identity
  sentence.
- **Don't play the narrator over footage of a real person visibly talking.** Viewers think that
  person speaks in the narrator's voice. Choose shots where the person acts rather than speaks.
- Use each B-roll interval once per film. A callback needs a changed state or a new moment.
- A whole web page shrunk to phone size is unreadable: crop to the phrase and highlight it on the
  spoken word. Small UI floating in empty space is the fastest "AI edit" tell, so zoom it to fill
  its panel.
- Never invent numbers, results or successful tests to decorate a claim.

## 7. Captions

Two modes; `caption_track.py --mode chunk|phrase`.
- **chunk** (default for 9:16 short-form):
  - 1–3 words per chunk, split on phrase boundaries;
  - a hard swap with no pop animation, appearing 2 frames before the first word;
  - one heavy sans in caps, about 62 px;
  - colour on 25–45 % of chunks, whole chunk only, with meaning: red = the wrong way or a loss,
    teal or marigold = the concept, green = the action or payoff.
- **phrase** (16:9, explainers, long lines of meaning): two-line phrase-locked cues with
  word-by-word brightening.
- **One look for the whole film.** Every caption in the same dark box with a **thin light edge**,
  so it reads on black, white and footage alike. Mixing boxed and bare captions looks cheap.
- **Never white on light.** `qa.py` measures every caption against its real pixels (WCAG 4.5:1).
- Never over a mouth or chin, least of all in the first second. A caption that runs across a cut
  moves with the cut. On shots full of text to read, move the caption to a clear zone instead of
  hiding it.

## 8. Sound

- **SFX follow visible actions**, not every cut:
  - a soft air whoosh only on a real spatial move;
  - a damped tap when something lands;
  - a dry click for small UI;
  - paper for documents;
  - one short warm tone for a check, a dry stop for an X.
- **Banned:** laser zaps, pitch-drop plops, sci-fi chirps, a whoosh on every cut. In
  `procedural_sfx` use `tick`, `thud` and short `whoosh` by preference; `glitch` and `riser` sparingly.
- Vary the sound for repeated items (pitch or type), so a list doesn't sound like a percussion loop.
- The music bed sits about **11 dB under the voice** (9–14 dB) and ducks under speech. The first 1–2 s
  can be quieter, with the beat landing on the second line. Never fade the last spoken word.
- Master at −14 LUFS with true peak **≤ −1.5 dBTP, measured on the encoded file** (qa gate).
- For narrated films, keep picture, music and SFX on one clock (the word timings / beat grid), so a
  retime moves everything together.

## 9. Reviewing like an audience, not like a validator

- **Write an entertainment review separate from technical QA** (`qa/<tag>/entertainment_review.md`):
  - timestamped weaknesses;
  - where attention would drop and why;
  - adjacent shots compared without their headings;
  - repeated headline copy;
  - generic footage.
- **Persona panel.** "Would this viewer finish? Where would they stop?" beats a 1–10 score. Never
  invent retention numbers.
- State the review modality honestly. Stills, strips and signal analysis are not watching or
  listening. A waveform proves levels, not that the music is right.
- **Verify every critic or AI-watch complaint on real frames before acting**; they hallucinate.
- **Calibrate checkers with negative controls.** A caption shifted by 0.3 s, a one-frame gap or a
  white-on-light caption must fail. Never loosen a check just to turn it green.

## 10. Notes become rules (the loop that made these edits good)

When the user gives a note ("I can't read that", "that shot doesn't move", "that sound is cheap"):
1. fix the film;
2. **write the fix into the skill** as a rule (`references/house-rules.md`), a check (`qa.py`) or a
   script change, so the same note is never needed twice;
3. record it in `house-rules.md` with the date and the user's words.

The next film starts from the improved skill.

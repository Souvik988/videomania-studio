# 6. Editor: cut, pace, caption, assemble

**Job.** Make the pieces one film: footage cut on words, shots joined motion to motion, captions that
can be read, and a draft that passes the gates.

**Read first.** `references/editor-doctrine.md` §6–9 · `references/typography-and-captions.md` ·
`references/rendering-and-delivery.md` · for footage: the `video-use` engine's `SKILL.md` hard rules
and `references/greenscreen-compositing.md` if keyed.

## Do

1. **Footage first** (if there is any). `cut_speech.py`: remove dead air between phrases, never inside
   one; propose retakes and fillers in `edit/cut_candidates.json` for the user's yes. Rules that are not
   taste:
   - cut only on word boundaries, with 30–200 ms of padding;
   - 30 ms audio fade on both sides of every cut;
   - captions are the last thing drawn, over every overlay;
   - never re-encode a segment twice.
2. **Treatments on words.** A switch of look (pixel switch, collage insert, punch-in) starts on the word
   that motivates it and ends on a phrase boundary. Give each switch a visible trigger.
3. **Joins.** At every cut the outgoing and incoming shots are both moving; the eye lands where it
   left. Use at least two transition types, one with depth; keep the showpiece transition for one moment.
4. **Captions.** `caption_track.py`; one fixed home (bottom centre), one or two lines, the punch word in
   its role colour. About 0.3 s per word and at least 1 s on screen for anything that must be read.
5. **Safe zones.** Keep text out of the platform's buttons (9:16 unknown platform: top 220 px, bottom
   420, right 140, left 60; 16:9: 120 top and bottom, 60 sides).
6. **Draft.** Render a draft and run `qa.py --tag draft`.

## Hand over

`renders/draft_<n>.mp4` and `qa/draft/summary.json`.

## Check (`qa.py --tag draft`)

- Caption contrast at least 4.5:1 on the real pixels.
- No stretch over 2.2 s without a visible change, outside planned holds.
- The open-loop ledger closes.
- An opening strip of the first 2.5 s shows motion from frame 0.
- No more than 3 flashes in any second.

## Never

- Cut inside a word. Crop, mask or alter a supplied or generated clip to hide something.
- Hold the end card for more than a quarter of the film (short films: 1.4 s; long explainers may hold
  6–8 s when a typed call to action needs it).

## Formats for a narrated film (2026-11-14)
16:9 is the master. A **reel** is the same film composed at 4:5 and padded to 9:16 with black bars:
`reel_frame.py prep` -> snapshot -> move only props that left the frame -> render -> `reel_frame.py pad` ->
`reel_frame.py restore`. Full commands: `references/director-film-runbook.md` Step 11.

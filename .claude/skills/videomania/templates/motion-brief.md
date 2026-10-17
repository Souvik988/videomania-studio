# Motion brief: <project id>

Written in step 3 after research (`brief/motion_research.md`). Every coded scene follows this file;
the critic scores the film against it. Rules: `references/motion-design-playbook.md`.

## 1. The bar
<one line, e.g. "Apple-keynote launch film quality: tactile, precise, expensive.">
If a frame would not survive at that bar, it is not done.

## 1b. Brand
`brands/<slug>/MOTION.md` read: <yes / no brand / created as a draft>. Look chosen: <warm-editorial |
apple-product | dark-lit | minimal-dimensional>, and why it fits the story.

## 2. Format
<1080x1920 | 1920x1080>, <30> fps, <exact seconds>, narration is the timing master. Safe zone for
9:16: words and logos between y 250 and y 1420, out of the right 120 px.

## 3. Concept and central visual rule
- Concept (one sentence): <...>
- Central visual rule (every scene obeys it): <...>
- Carried motif: <the object or shape that returns and pays off>

## 4. Look
- Ground / surface / ink / muted / accent / second accent: <hex codes, with what each is for>
- Finish, one only: <paper grain + halftone | film grain + halation + vignette | frosted glass + rim
  light | flat editorial>
- Depth: <shadows, glass, highlights>; nothing floats small in empty space; the hero fills 60–70 % of
  the frame.

## 5. Type system
- Display (1–4 words, 120 px or more): <font, weight, tracking>
- Secondary: <font, weight>
- Labels and crumbs (34 px or more, tracked +0.14 em or wider, 18 characters or fewer): <font>
- Captions: <style>. Headlines rise through a mask line; no typewriter headlines.

## 6. Motion
- Signature curve: <cubic-bezier(.45,0,.15,1), 0.6–0.8 s>; the camera rides the same curve.
- Springs: <tight, 2–6 % overshoot; per-element damping for stacks>
- Stagger: <40–90 ms in reading order>
- Living hold: <what keeps moving in each hold>
- Camera: <slow 1.03–1.07 push per scene | screen-studio reframes>

## 7. Scene chain (one row per beat, from the edit map)
Research each beat, not just the film: run `motion_refs.py --query "<this beat's subject + move>"`
and cite the reference that fed it.

| t (s) | beat | hero object | the one change | built with (blueprint / 2–4 rules / MK·MKFX / runtime) | reference used | bridge into next scene | real words on screen |
|---|---|---|---|---|---|---|---|

## 8. Banned for this film
<start from playbook §10, then add or remove per film>

## 9. Originality
Every element is original. No real product's UI, icons or logos redrawn from memory. References
gave technique only; sources are listed in `brief/motion_research.md`.

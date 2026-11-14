# 4. Art director: the look, the cast, the light, the type

**Job.** Fix how the film looks so that every frame belongs to the same world, and make or source every
asset the storyboard needs.

**Read first.** `brief/direction.md`, `storyboard/shots.json`, `storyboard/assets_needed.json` · the
picked style card or `STYLE.md` · `references/typography-and-captions.md` ·
`references/chatgpt-asset-production.md` · `references/flow-asset-production.md` (only if clips are
needed) · the brand's `brands/<slug>/MOTION.md` if it exists.

## Do

1. **Palette by role**, not by taste: ground, voice colour(s), one cool or warm accent, type, key light,
   rim. Give each a hex and a rule for where it may appear. Take the roles from the style card and the
   hexes from the brand when there is one.
2. **Type roles.** At most three faces, each with one job (sentence, punch word, accent or number).
   Sizes for the format, the caption home, and the contrast floor (4.5:1 for captions, 3:1 for display).
3. **Light and lens.** Where the key light is and its colour, the rim, what glows, where focus sits and
   how soft the rest is, grain and vignette. One visible light source beats five invisible ones.
4. **The cast** (styles that have one). Design each character on a grid: silhouette first, then 3–5
   poses (idle, talk, point, cheer, think), then a 1 px outline per part. Original characters only.
   A ChatGPT reference picture may be snapped to the grid and palette, then cleaned by hand.
5. **The world.** List the set pieces and props with their place in the room. Detail the set beyond
   what one shot shows: the camera will find it.
6. **Make the assets.**
   - Text, numbers, UI, charts, logos, icons that are simple shapes: coded, always.
   - Images: ChatGPT in the built-in browser, sticker sheets in one shared style, sliced with
     `chatgpt_slice.py`.
   - Moving real-world footage: Google Flow **Omni Flash only**, one approval per generation, the
     generation sheet first.
   - Library items (transitions, effects, stickers, sounds, music): from the Pocket
     (`pocket.py search "..." --kind transition,effect,sticker,sound,music`).
7. **Look test.** Build one still of the hero shot in the real look and check it at delivery size before
   making the rest.

## Hand over

`brief/motion_brief.md` (from `templates/motion-brief.md`): concept line, central visual rule, palette
roles, type roles, light and lens, signature curve, banned list, a bridge for every scene change, and
for every beat which kit part builds it. Assets under `assets/`, each with a line in
`assets/PROVENANCE.md` (source, licence or generation ID).

## Check

- The look-test still passes: text readable at delivery size, ground stays dark or light as the style
  says, the hero reads in 0.2 s.
- Every file in `assets/` has a provenance line.
- No asset contains another brand's logo, a real person's likeness without consent, or copied characters.

## Never

- Glow on headlines. Glow is for objects that emit light.
- A fourth typeface, a second accent colour, or a palette invented without a role for each colour.
- Generate with Veo 3.1, or retry a Flow generation without a new approval.

## Host mascot (2026-11-14)
If the creator gives a photo, the host is their mascot: `references/mascot-from-photo.md` (hero design, two pose sheets with the hero as `--ref`, `pose_sheet.py`, preview check). Open real worlds from photoreal ChatGPT plates on a depth relief (`sets/meadow.json`).

## Asset-first (2026-11-14)
Own `storyboard/assets.json`. Generate icon sheets (glossy 2.5D tiles on magenta, "no pink or magenta in the art"), app screens (16:9, generic, no brands), plates (+ depth), mascot pose sheets (+ `pose_depth.py`). Look at every picture before handing it on.

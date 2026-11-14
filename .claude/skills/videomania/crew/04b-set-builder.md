# 4b. Set builder: a picture becomes a world the cast can walk through

**Job.** Build the film's environment as a 3D set described in data (`sets/<name>.json`), from a concept
picture, without a 3D program. No Blender.

**Read first.** `brief/motion_brief.md` (palette, light) · `templates/voxel-diorama/kit/setdata.js` (the
format and every prefab, at the top of the file) · `templates/voxel-diorama/sets/cafe.json` (a finished
example) · `references/styles/voxel-diorama.md` §2b (fine detail, depth in layers).

## Do

1. **Concept picture.** Generate one picture of the place with the ChatGPT image bridge
   (`~/.claude/skills/gpt-image-bridge/bin/gpt-image-2 "<prompt>" <absolute path> --size 1536x1024`, run in
   the background: it takes 4–6 minutes). Ask for: the place, seen from the front at eye level, built
   from clean blocks; the layout left to right; the back wall; where the light comes from; the palette
   by role; **empty of people, no text**. Save it as `assets/concept/<name>.png` and look at it.
2. **Read the picture into a list.** Write down, left to right and front to back: every surface (floor,
   walls, window), every piece of furniture with its rough size and colour, every light and what colour
   it throws, and the far distance (what is behind the window or the horizon).
3. **Write `sets/<name>.json`.** One unit is one voxel; a person is about 12 units tall; a table top is at
   6–7; a room is 80–90 wide; the back wall is at z = −20 and the cast stands around z = 8.
   - Start with `floor`, `wall` (with its `window`), the far distance (`city`, or your own `plate`s), then
     big furniture, then small things, then lights.
   - Use prefabs first: `floor wall rug table chair stool counter shelf sofa crate stairs door plant tree
     cup machine case picture monitor-frame pendant floorlamp desklamp streetlamp neon stringlights dust
     railing city`. Use `box` and `vox` (with `"unit": 0.5`) for anything else.
   - Put the picture's colours in `palette` and refer to them as `"$name"`.
   - Add `marks` for where the cast stands and walks, and at least a `wide` camera in `cams`.
   - Light it the way the picture is lit: the key light where the picture's brightest lamp is, one rim
     colour, a dim `hemi`. Every lamp you can see should also be a `light`.
4. **Preview and compare.**
   `python scripts/set_preview.py --set <name> --cast --concept assets/concept/<name>.png`
   Open `compare.jpg` (concept on the left, render on the right) and the contact sheet (wide, left,
   right, top). The report prints a colour difference: **under 0.12 is close**.
5. **Fix the biggest difference first** and run it again: what is missing, what is the wrong size or
   place, then colours, then light. Three passes at most. Stop when a stranger would say both pictures
   show the same place.
6. **Depth check.** In the wide view there must be something near the lens (dust, a lamp, a crate), the
   stage, a middle ground and a far distance. In the top view nothing may float or intersect.

## The fast route: a world from one picture

When the place is a view (a landscape, a skyline, a cavern, space) and the cast only stands in front of
it, do not rebuild it from boxes. Generate the picture, run `python scripts/vm_depth.py <picture>`, and use the
`vista` set with the two files as its `relief` (kit README, "A world from one picture"). Check a
snapshot at both ends of the camera move: no torn edges, the whole picture in frame, the cast clear of
busy areas. Use a built set (above) when the cast must walk among the furniture.

## Hand over

`sets/<name>.json` in the project's `source/sets/`, the concept picture, `compare.jpg`, and one line in
`assets/PROVENANCE.md` for the concept. A set worth keeping goes back into the kit's `sets/` folder
(crew job 9).

## Check

- `set_preview.py` runs clean and the colour difference is under 0.12, or the report says why it is not.
- The cast, at the `stage` mark, is fully visible in the `wide` camera and not hidden by furniture.
- Four depths are present in the wide view.

## Never

- Open Blender or ask for a 3D file. A set is data; anything a prefab cannot make is built from boxes.
- Copy a real place's logos or signs. A neon sign is a shape, not a brand.
- Leave big bare squares: break large surfaces into planks, slats, shelves or rings.

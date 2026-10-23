# Motion effects library (MKS)

`assets/motion-kit/motion-shots.js`: 18 named shots and effects, each a seek-safe function on the
film's one paused timeline (`MKS.name(tl, parent, at, opts)`), copied into every new film by
`new_composition.py`. All 18 were snapshot-verified in `projects/mks-gallery` (2026-10-23).
Reach for these before hand-building a look; combine them with `MK` (springs, camera, masks) and
`MKFX` (headline, chartMorph, dashboardZoom…). Tests: `node assets/motion-kit/motion-shots.test.cjs`.

Every effect needs a **story job**. Name it in the motion brief ("orbit: the theme builder is the
hero of this beat") or don't use it. One loud thing at a time; ≥ 1 visible change every ~2 s.

## The catalogue

| Effect | What the viewer sees | Story job | Inputs | Timing |
|---|---|---|---|---|
| `orbit` | one lifted card (screenshot, product, UI) turning slowly in 3D, a sheen crossing it, its shadow sliding the other way over a blurred page | "look at this one thing", payoffs, premium product beats | `src x y w h`, `page`, `deg`, `lift`, `dur` | rise 0.8 s, sweep ±16° over 3–5 s |
| `casualCam` | handheld drift with snap punch-ins on stressed words (UGC / talking-head energy) | keeps a talking head alive; punches = emphasis | target wrapper, `punches:[{t,scale}]`, `amp`, `rot` | drift steps 0.22 s; punch 2 frames in, 0.8 s back |
| `uiWorld` | a field of UI cards in depth; the camera dollies through them to a hero card | "your whole system", feature overviews, the app as a place | `cards:[{src|html}]`, `hero`, `travel` | 2.5–3.5 s, power3.inOut |
| `frameBreak` | the subject rises out of its framed photo, past the border | "this is bigger than a screen", reveals, hooks | `frameSrc`, `cutoutSrc` (alpha PNG aligned to the frame), rect, `out` | 0.6 s back.out |
| `digitalZoom` | stepped 2-frame punch-ins onto a region with RGB flicker and HUD brackets + "ZOOM 3.0×" readout | evidence, "look closer", security-cam / screen-recording reveals | target, `region`, `steps:[1.6,2.6]`, `gap`, `hud`, `label` | steps ~0.45–0.6 s apart |
| `phoneMockup` | coded phone with the real recording, rising in at a tilt, glass glare, gentle float | app demos (the user's own recordings only) | `src` (+`videoAttrs` for HyperFrames video), `x y w`, `tilt` | 0.95 s expo.out |
| `checklist` | rows slide in, boxes fill and tick on their spoken words, optional strike | lists the narration says ("App, iOS, Website, Dashboard") | `items:[{text, at}]`, `size`, `strike` | tick on the word; rows 90 ms apart |
| `headlineWall` | a tilted wall of newspaper headline cards; the camera pans; one card lifts, centres and gets a red marker circle | "everyone is talking about X", social proof, problem framing | `cards:[{kicker,title,src}]`, `highlight`, `cols` | pan 3 s; lift at 55 % |
| `zoomThrough` | the camera dives (log-space, motion blur) into a rect, and the next scene grows out of it | match-cut transitions: a screen becomes the next scene | `world`, `next`, `rect`, `dur` | 0.8–1.0 s expo.in |
| `chartGrid` | a grid of mini charts (bars grow, lines draw, numbers count) flies in; the camera pushes into one | "the numbers", dashboards, the one stat that matters | `cells:[{label,type:bar|line|number,values|value,format}]`, `focus` | cells 90 ms apart; push at 60 % |
| `pullbackReveal` | open tight on a detail (rack focus releasing), pull back in log space to the whole | "this one row… is part of all this", context reveals | target, `detail` rect, `dur` | 1.6–2.2 s power3.inOut |
| `greenScreen` | the sandwich: plate (parallax) → giant words behind → keyed subject (rim light) → foreground | every green-screen film (pairs with `greenscreen_key.py`) | `plate`, `subject` (alpha video/PNG), `behind:[{text,x,y,at}]` | words rise 0.5 s expo |
| `paperCut` + `paperGround` | Vox collage: fibre paper + halftone ground; torn-edge cut-outs with white borders and tape snapping in "on twos" | explainers, history, money, "how it works" | `pieces:[{src|color,x,y,w,rot,gray}]`, `onTwos` | 0.42 s steps(6) per piece, ~0.25 s apart |
| `doodleBoil` | a hand-drawn stroke (circle, underline, arrow, star, squiggle, check, or any path) draws on, then boils like hand animation | emphasis on a word or object, editorial annotation | `shape|d`, rect, `color`, `boilFps` (8) | draw 0.5 s; boil through the hold |
| `vertigo` | dolly zoom: background layers scale by depth while the subject holds its size | the realisation beat ("pata hai?"), dread, a twist | `layers:[{el, depth}]`, `amount`, `dur` | 1.4–2.2 s, once per film |
| `coverStory` | the frame becomes a magazine cover: masthead behind the subject's head, cover lines, issue line, barcode | brand/founder moments, end cards, "the story of…" | `masthead`, `plate`, `subject` (alpha), `lines:[{text,big,italic,sub}]`, `issue` | 0.9 s settle; lines 160 ms apart |
| `glassType` | frosted-glass letters: the scene behind is blurred and brightened only inside the glyphs, with a light edge | premium titles over footage, CTA words | `text`, `x y size`, `role` | 0.7 s power3.out |
| `slideUpText` | per-letter slide-up from behind a soft-edged line, ~0.7 frame apart, expo out, mirrored exit (Daniel Do's Fusion macro) | clean titles, lower thirds, quotes | `text`, `x y size`, `role`, `out` | 0.55 s per letter, total < 0.8 s |

`MKS.logCam(tl, target, at, fromRect, toRect, dur, {W,H,ease,blur})` is the camera under
`pullbackReveal`, `zoomThrough` and `chartGrid`: scale moves in log space, so a zoom in and a zoom
out read at the same speed (ai-video-editor-cooked's zoom rule).

## Rules that make them look premium

- **Real material only**: screenshots and recordings of the user's product, ChatGPT stickers/cut-outs,
  Flow clips. Coded text, numbers and logos. Nothing invented.
- **Zooms are camera moves**: ≥ 0.8 s each way unless it is a deliberate snap (casualCam, digitalZoom);
  log-space scale; on a person, grow from the top-centre of the head and never crop the top of the
  head (the stills critic checks).
- **Easing**: entrances ease-out, exits ease-in (65–75 % of the entrance), on-screen moves ease-in-out,
  loops sine; never linear on a spatial move. Stagger budget < 0.5 s total. Overshoot 0 % premium,
  5–10 % success, 15–25 % celebration.
- **Depth**: a lifted thing gets a shadow that moves the other way; back layers blur; one light
  direction per scene.
- **One loud thing**: at most a third of the elements move at once; the rest hold or drift.
- **Fake-oner**: transitions hide in motion (zoomThrough, whip, a rack-focus blur), not in fades.
- **Stills before renders**: snapshot every effect's settled frame and one mid-motion frame
  (`npx hyperframes snapshot --at …`) and check: readable at phone size, nothing off-frame, no card on
  a face, the last frame strong enough to be a poster.

## Pairing effects with the story (from the editor doctrine)

| Beat | Good effects |
|---|---|
| Hook (0–3 s) | frameBreak, digitalZoom, glassType, greenScreen words behind, casualCam punch |
| Problem | headlineWall, doodleBoil on the pain word, paperCut evidence, vertigo on the realisation |
| Reveal / product | zoomThrough into the app, uiWorld, orbit on the hero screen, phoneMockup |
| Proof / numbers | chartGrid, checklist, pullbackReveal from one row to the whole dashboard |
| CTA / end card | coverStory, glassType, slideUpText, orbit on the logo card |

Sources: nextwork-projects/ai-video-editor-cooked (MIT; product shot library, zoom rules, stills
checks; its motion-design reference tables are MIT, LottieFiles), Daniel Do's DaVinci Resolve slide-up
macro (re-implemented from its curves: per-letter Y offset with Expo ease-out, 0.7-frame order delay,
mirrored cubic opacity, soft rectangle mask, motion blur), the vox-motion-graphics skill (collage and
diorama grammar), Nate Herk's Claude + Blender guide (one timeline, stills first, exact-number fixes).

# Motion research sources (the user's list, 2026-10-17)

Before designing a film's motion, research how Opus 5.5 work on similar subjects looks. Use the
local copies first, because they are fast, offline and searchable. Use the live sites for what is
new this week. Everything here is reference for craft. Never copy a creator's copy, brand,
characters, palette or exact layout into the user's film. Take the technique, not the piece.

## Local (cloned read-only under `video-production-workbench/research/`, all MIT)

| Source | What it gives | How to use |
|---|---|---|
| `awesome-opus5-5-videos` (github.com/yihui-dev/awesome-opus5-5-videos) | 703 prompts behind real Opus 5.5 videos, tagged motion / explainer / 3d / interactive, with tech tags (Canvas, SVG, GSAP, GLSL, Three.js) and links to the original posts | `python scripts/motion_refs.py --query "<subject + look words>" --category motion` → craft lines from the best matches; `--full N` reads one prompt in full |
| `motion-graphics-skills` (github.com/charlie947/motion-graphics-skills, Charlie Hills) | 15 workflow skills (launch video, vox explainer, Apple launch film, reel export, motion brief writer, reference-to-motion) and the 16 premium effect recipes with exact timings | `motion_refs.py --effects` / `--effect "<name>"`; read `skills/<name>/SKILL.md` for a workflow's review rules |
| `herk-edit-kit` (github.com/nateherkai/herk-edit-kit, Nate Herk) | measured editing playbook (27 top reels), motion philosophy ("dark lit" look, HyperFrames craft laws), 406 donor cards with slots, 9 palettes, a transitions catalogue, short-form story and quality gates | `motion_refs.py --cards "<purpose>"` / `--card <id>`; rules distilled into `storytelling-and-retention.md` and playbook §12–14; `analyze_video.py` and `caption_contrast.py` are its tools ported to Python |

Update the first two with `motion_refs.py --update` (a `git pull`; ask nothing, it only reads public repos).

## Live sites (fetch with firecrawl_scrape or WebFetch; read, don't download assets)

| URL | What to look for |
|---|---|
| https://youmind.com/opus-5-5-prompts/explore | newest Opus 5.5 prompts (486+), sorted by recency. Open the ones close to the brief ("View full prompt") |
| https://ai9app.io/video-prompts/opus-5-5 | curated Opus 5.5 listings: showreels, SaaS launch, Three.js, hand-drawn p5.js MV, "15 commercial video styles" |
| https://github.com/yihui-dev/awesome-opus5-5-videos | same as the local clone, plus the README gallery of the 100 best remakes |
| https://charliehills.substack.com/ | posts on Opus 5.5 motion ("Claude Opus 5.5 = your motion designer", "Claude /motion") — brief-first workflow, house-style file, premium notes. Paid sections are not accessible; use only the free parts |
| https://medium.com/@nr7670/opus-5-5-prompt-library-for-creators-motion-graphics-ai-video-ca43a6d562ad | prompt anatomy (role, outcome, beat sheet, visual system, assets, audio, stop rules) and the 3-pass loop (structure → brand/type/assets → audio/captions/CTA) |
| https://jitter.video/templates/jitter-ai/ | effect vocabulary: grainy colour clamp, threshold, halftone, luma dots, gooey, fluted glass, pixelated mask/dissolve, type trail, stretched type repeater, image stretch, card flip, 3D rotation, text extrusion, dithering, CRT, ripple, highlight |
| https://www.swishy.ai/ | template catalogue by job (text, overlays, logos, social, charts, money, app/website, UI elements, launch videos). Use it to name a UI micro-animation precisely (notification stack, iMessage thread, laptop opening, folder open, counter, calendar drop) |
| https://autoae.online/hooks | AE-grade hook templates: glass button click with ripple, creator profile showcase, portrait montage plus kinetic type, storefront showcase, 3D object typography, parallax ribbons, footage rings and carousels, door-reveal statement, spotlight name reveal |

## How much research per film

- **Short or simple edit (under 30 s, one look):** run `motion_refs.py` with 2–3 queries and read 2
  prompts in full.
- **Ad, launch or explainer:** also skim youmind and ai9app for the newest relevant pieces, and pick 2
  effect recipes per act.
- Write what you took into `brief/motion_research.md`: 3–6 references (link, author, the one
  technique taken from each) and the resulting concept, central visual rule, look and banned list.
  The critic checks the film against that file.
- Stop researching when the motion brief is decided. Research is input to design, not a substitute.

## Added 2026-10-23 (the user's pack)

- nextwork-projects/ai-video-editor-cooked (MIT) — cloned read-only to
  `~/video-production-workbench/research/ai-video-editor-cooked`: product-video shot library
  (`plugins/ai-editor/remotion/src/product/Shots.tsx`), zoom rules (`skills/style-edit/references/motion.md`),
  stills/storyboard critics (`agents/`), motion-design timing tables (`skills/motion-design/reference/`).
- vox-motion-graphics skill (user's file) — collage and paper-diorama grammar, story engine →
  `editorial-collage-and-diorama.md`.
- Daniel Do, DD_Slide_Up_Text_Animation (DaVinci Resolve Fusion macro) → `MKS.slideUpText`.
- Nate Herk, "Claude + Blender: Make 3D Motion Graphics From Code" (AI Automation Society) →
  `blender-3d-route.md`.


# Blender 3D route (optional)

From Nate Herk's "Claude + Blender: Make 3D Motion Graphics From Code" (AI Automation Society; prompt
structure by rari, @0xwhrrari). Use it only when a beat needs real 3D (a mascot, glass slabs, physical
lighting) that CSS 3D and `MKS` can't sell. Everything else stays in HyperFrames.

**This machine (2026-10-23): Blender is not installed and there is no NVIDIA GPU** (~7 GB RAM).
Cycles on CPU is very slow; use EEVEE or Cycles at low samples for short inserts (2–4 s), render
stills first, and never run it beside a HyperFrames render. Ask the user before installing Blender
(portable build from blender.org, ~400 MB).

## Method

Claude doesn't generate the video: it writes a program that answers "what should the frame look like
at this exact moment?" So fixes are cheap: change one number, re-render only those frames.

- **One timeline file** (`timeline.py`) holds every position and event time. The interface (HTML +
  Puppeteer screenshot), the 2D comp (canvas frames), the 3D scene (`scene.py`, Blender Python) and the
  sound (`sound.py`) all read it, so a click lands on the frame the foot hits the button. In Video
  Mania the voiceover's word times feed this file.
- **The brief has six blocks**: BRAND (hero, app, result, set: the only block that changes between
  films), FORMAT (engine, size, fps, length, BPM, shared timeline), BEATS (what happens per second
  range; every action changes something visible), CAMERA (wide open, follow at the hero's height,
  shallow focus, end on the result), LOOK (screens glow under black glossy glass; lights hidden from
  reflections), CHECKS (interface image and comp contact sheet, then half-size stills, then the film).
- **Headless**: `blender -b scene.blend -P gpu.py -P render.py -- --frames 1-360 --out renders/full`;
  re-render ranges (`--frames 105-145,285-360`); scan every frame's brightness and re-render blank
  ones.
- **Stills before the render**: 18 half-size stills at low samples as one grid. Check: text readable at
  phone size, positions right, brand colour right (measure a pixel against the hex), no white light
  blowing out the glass, last frame strong enough to be a poster.
- **Exact fixes, rounds**: "rays twice as wide", "exposure 0 → −0.4", "shorter cracks, camera in".
  The polish comes from 3–4 such rounds.
- **Finish**: `ffmpeg -framerate 30 -i renders/full/f_%04d.png -i sound.wav -vf "vignette=angle=PI/6"
  -c:v libx264 -profile:v high -crf 17 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart -shortest out.mp4`,
  then into the HyperFrames film as a `<video>` layer.
- For 9:16 make a separate composition with bigger type and fewer elements; never crop the 16:9.

## Troubleshooting (from the guide)

| Problem | Fix |
|---|---|
| Brand colour washed out / pink | AgX lightens: lower exposure, darken base colour, measure a pixel |
| White blocks on glass | hide lights from glossy reflections (object visibility) |
| Objects in the wrong place | `view_layer.update()` before parenting |
| Out of memory mid-render | chunked renders that skip finished frames |
| Audio clips on phones | true-peak ceiling at −1 dB, not a sample-peak limiter |

# Vox poster reference build (colour)

`scenes_vox.reference.js` is the real 635-line scene file of a 53 s, 9:16 Hinglish ad ("Bill kaun
bharta hai", Shotlin) built in the Vox poster look. It is a **reference implementation to read and
lift from, not a runnable template**: it expects the film's `index.html`, a `data.js` scene table,
the motion kit (`MK`), and media under `media/vox/` (ChatGPT cut-outs, satin and velvet grounds,
3D objects, device mockups).

Lift these helpers (all defined at the top, lines 53 to 215):

| Helper | What it gives |
|---|---|
| `stage` + `setBG` | one camera node holding ground and scenes, so a focus pull blurs both; four grounds (satin, velvet, grid paper, cobalt) switched on timeline sets |
| `focusPull`, `iris`, `flash`, `letterbox` | the four transitions of the look (blur-and-scale pull, circle iris, colour flash, cinema bars) |
| chrome (`hdr`, `counter`, `ftr`, `chromeMode`) | persistent micro-type header and spec footer with issue counter and barcode, flipping dark/light with the ground |
| `kline` | the kinetic editorial caption line: roles `s` sans, `b` bold extended, `c` script payoff, `d` Didone hero, `h` highlighter; fixed top zone |
| `hero` | giant Didone word with scan stripes and RGB fringe |
| `frame`, `cut`, `obj` | colour frame that opens, cut-out breaking out of it, 3D object with dotted ring |
| `spec` | product-label spec card (barcode, QR pattern, globe, accent glyph) |
| `phone` | device shell for real app recordings |

Design notes and the critic's defects are in `references/vox-poster-system.md`.

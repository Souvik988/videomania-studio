# ChatGPT asset production (images, icons, 3D elements, UI pieces)

The user's standing instruction (2026-10-22): **whenever a film needs an image asset, generate it in
ChatGPT**, which the user keeps signed in in the built-in browser pane. That covers icons, 3D objects,
stickers, UI elements, illustrations, textures, B-roll stills and backgrounds. Asset generation is
not a limit. Plan every asset the edit map needs, then make it.

## When ChatGPT, when code, when Flow
| Need | Source |
|---|---|
| 3D icons and objects (diya, cart, pin, coin, gift, megaphone…), stickers, illustrations, avatars, textures, mini dioramas | **ChatGPT** (transparent PNG sticker sheet) |
| a background or plate still, a B-roll still | **ChatGPT**, then animated by code (camera move, parallax, light). A still never sits frozen on screen |
| real moving footage (people, nature, places) | Google Flow, Omni Flash only, one approval per generation (SKILL §2) |
| text, numbers, prices, UI that must be exact, logos, device frames, charts | **coded** (never generated, because spelling and numbers must be exact) |
| the user's own product | the user's screen recordings in coded device mockups |

## Procedure (built-in browser, chatgpt.com)
1. Check that the pane shows ChatGPT signed in (`tabs_context`, then a screenshot). If it is
   signed out, ask the user to sign in. Never type credentials.
2. Ask for a **sticker sheet**: 6 objects in a 3×2 grid per image, fully TRANSPARENT background,
   generous spacing, no text or letters, one shared style line (lighting, camera angle, palette in
   the film's hex values). Follow-up sheets say "same exact style, lighting, angle and palette" so
   the whole film's set matches. Ask for real currency only as plain abstract notes.
3. Wait for the image (about 1–2 min; take a low-scale screenshot to check). Open it, then click
   **Download** (find the "Download" button; the share icon on the image opens the viewer first).
4. The file lands in `~/Downloads`. While it downloads it is named `<uuid>.tmp`; it is renamed to
   the ChatGPT title when done. Wait until it is a complete PNG (ends in `IEND`), then move it to
   `projects/ID/assets/chatgpt/sheet_<x>.png`.
5. Slice it: `chatgpt_slice.py sheet.png assets/chatgpt name1,...,name6` (reading order). Look at
   each PNG before using it.
6. Record provenance in `assets/chatgpt/README.md`: sheet file, prompt, date, the names cut from it.

Downloading these files is pre-authorised by the user's standing instruction above. Everything
else in the browser follows the normal rules: no sign-ins, no purchases, nothing posted.

## Craft rules for generated stills
- Use them as **elements** in the motion design (spring in, hop, roll, dock, burst), never as a
  frozen full-frame slide.
- Keep one style family per film (all from the same chat thread, so the look stays consistent).
- An object that plants a question (the cart, the pin) must come back to pay it off
  (`storytelling-and-retention.md`).
- Blank areas a generated object offers (a blank shop poster, a blank screen) are slots for coded
  content: words, prices, flips.

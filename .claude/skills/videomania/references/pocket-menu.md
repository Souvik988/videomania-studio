# The Pocket and the menu

The Pocket is the index of everything Video Mania can make: film and art styles, edit treatments,
formats, transitions, effects, text animations, templates, stickers, music and sounds, decoded
professional moves, and proven prompts, drawn from every engine in `engines/engines.json`. It is
searched, never recalled from memory: what is installed changes, and memory invents.

`P` below is `python "$S/pocket.py"`.

## Commands

| Command | Use |
|---|---|
| `P build` | Rebuild the index after an engine was added or updated, or a style card was written. First run downloads a small sentence model (about 120 MB); `--no-vectors` skips it |
| `P menu "<brief>" --has footage,voiceover,topic,product` | The grouped menu for a request |
| `P search "<words>" --kind style,treatment -k 10` | A direct search. Kinds: `treatment style look grammar format transition text caption-style effect filter template sticker music sound moment prompt skill guide fix-move palette example engine` |
| `P show <id>` | One row in full: what it is, where it lives, **the files to read before using it**, what it needs, its licence |
| `P pick <id> ...` | Record the user's choices; picked rows rank higher later |
| `P stats` | Rows per kind and engine |

Search understands meaning as well as words, in English and Chinese: "sad goodbye, hand-made" finds a
watercolour farewell. Write the query the way you would describe the film to a designer: subject,
mood, look, audience.

## When to show the menu

| The request | Do |
|---|---|
| Generic: "edit this video", "make a video about X", "make it cool" | **Always show the menu.** Never pick a style silently |
| Names a style or treatment: "Vox poster explainer", "pixel art" | Search to confirm it exists, show that option plus two neighbours, ask only if a real choice remains |
| A follow-up on a film in progress | No menu. Use `brief/picks.json` |
| "What can you do?", "what styles do you have?" | `P stats`, then a menu for the kind they ask about |

## How to show it

1. Run `P menu`. Keep only options whose needs are met (`P show <id>` when unsure).
2. Present two groups first, each option as **one line the user can picture**, your recommendation first:
   - **How to treat it** (3–5 from "Ways to treat it")
   - **The look** (4–6 from "Film and art styles", no more than two from one engine)
3. Then, briefly, **extras they can add**: one or two transitions, a text style, music mood. Offer; do
   not make them choose every one. You choose the rest and say what you chose.
   Some rows (huashu-art-motion) are written in Chinese: put them into the user's language, in your
   own words, when you show them. With footage only, lead with treatments and keep looks to the two or
   three that suit graphics laid over footage.
4. Where a row has a `preview` (a poster or GIF path, or an image link), show or link it.
5. Use the question box when the IDE has one (two questions: treatment, look; allow several picks and
   free text). Otherwise a numbered list and "reply with numbers or describe something else".
6. If the user describes something that is not in the Pocket, say so plainly, then offer the nearest
   rows and the option to build it new (new work costs more time).

Example for footage of a podcast and the request "edit this, make it fun":

> **How should I treat it?**
> 1. Switch into pixel art on the punchlines (recommended): the frame breaks into blocks and becomes a
>    pixel version of the moment, then snaps back.
> 2. Tight cut with kinetic word-by-word captions.
> 3. Edit it like 3–6 reference videos you send me.
> 4. Paper-collage B-roll over the key lines.
>
> **Which look for the graphics?** …

## After the user picks

1. `P pick <ids>`; write `brief/picks.json`.
2. For every pick run `P show <id>` and **read every file it lists** before planning. A style's own
   rules beat general rules when they conflict; the user's house rules beat both.
3. If two picks conflict (a no-text style with word-by-word captions), say so and ask which wins.

## Honesty

- Rows of kind `prompt` and `moment` are ideas and measured moves to learn from, not assets to copy.
- An option that needs an app or a key that is missing is shown as "needs X", never as ready.
- The `onetake` engine is licensed for non-commercial use: offer it for personal films only.

# 1. Producer: find out what to make, show the menu, get a yes

**Job.** Turn whatever the user said into a brief they approved, built from what Video Mania can
actually make.

**Read first.** `references/house-rules.md` · `references/input-contracts.md` · `references/pocket-menu.md`

## Do

1. **Look at what you were given.** Run `preflight.py --input <each path>`. Note which of these exist:
   `footage` (a video to edit), `voiceover` (audio or a script), `topic` (an idea only), `product` (a
   site, app or object), `references` (videos to edit like).
2. **Decide: specific or generic.**
   - Specific ("a 30 s Vox poster explainer about X, 9:16"): search the Pocket to confirm the style exists
     (`pocket.py search "<their words>" --kind style,treatment`), then go to step 5.
   - Generic ("edit this video", "make something cool about X"): go on to step 3. Never guess a style
     for a generic request.
3. **Open the pocket.** `pocket.py menu "<the request in your words + the subject + the mood>" --has
   <footage,voiceover,topic,product>`. Read the result. Drop options that need something missing
   (`pocket.py show <id>` lists needs) and say so in one line if a strong option is unavailable.
4. **Show the menu and ask.** Follow `references/pocket-menu.md`: 3–5 ways to treat it, 4–6 styles,
   then extras. Each option is one line the user can picture. Recommend one of each, first in the list.
   Ask the format (16:9 or 9:16) in the same message if they have not said. Wait for the answer.
5. **Write the plan on one screen** and get a yes: the idea in one sentence, length, format, the
   treatment and style picked, what will be generated (ChatGPT images freely, Flow clips one approval
   each), what the user must supply, and what it will not include.
6. **Record it.** `pocket.py pick <id> ...` for each choice. Write `brief/brief.yaml` (from
   `templates/brief.yaml`) and `brief/picks.json`:
   ```json
   {"treatment": "treatment/voxel-diorama-director", "style": "vm/style/voxel-diorama",
    "extras": ["openfilm/transitions/pixelate"], "format": "16:9", "length_s": 45}
   ```

## Hand over

`brief/brief.yaml` and `brief/picks.json`.

## Check

- The user's own words approving the plan are quoted in `brief/brief.yaml` under `approval`.
- Every id in `picks.json` exists (`pocket.py show <id>` succeeds).

## Never

- Start building on a generic request without showing the menu.
- Offer a style that is not in the Pocket, or one whose needs are missing, as if it were ready.
- Ask more than one round of questions before the plan. Decide the rest yourself and say what you chose.

## Asset pass first (2026-11-14)
Before the storyboard is turned into shots.js, run the asset pass (`references/asset-first.md`): list every object, screen, icon, place and character in `storyboard/assets.json`, start the ChatGPT generations in the background (3 at a time), cut real footage frames with ffmpeg. Nothing reaches the animator as "draw it in code" unless it carries a written `drawn_ok` reason.

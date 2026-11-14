# Cinematography: every shot is a named choice with a reason

Film language mapped onto kit settings. The storyboard artist picks one option from each row for every
shot and writes the reason in the shot's `why`. A shot whose choices cannot be explained is filler.

## The six decisions

| Decision | Options | Kit setting | What it does to the viewer |
|---|---|---|---|
| **Size** | extreme wide · wide · full · medium · close · extreme close · insert | camera distance (`from`/`to`), `fov` | wide = where are we; medium = who; close = what they feel; insert = what matters |
| **Angle** | eye level · low · high · top-down · dutch · over the shoulder · point of view | camera height, `up` tilt, presets `low-hero`, `top-down`, `dutch`, `ots` | low = power; high = small, overwhelmed; dutch = something is wrong; OTS = a conversation |
| **Lens** | wide (24–30°… in the kit 40–60° fov) · normal (30–36°) · long (17–24°) | `fov`; `lens.aperture` for depth of field | wide and near = energy and distortion; long = compressed, calm, intimate; shallow focus = isolate |
| **Move** | hold · push · pull · dolly · orbit · crane · tilt/pan · snap zoom · vertigo · shake · follow · rack focus | presets `hero-push`, `pull-back`, `dolly`, `hero-orbit`, `crane`, `snap-zoom`, `vertigo`; `shake`; `follow`; `focus: {from, to}` | push = it matters more; pull = there is more to this; dolly = place and depth; crane = scale or an ending; vertigo = realisation |
| **Light** | key side and height · warm against cool · practical in frame · rim · silhouette · one colour | set lights, `castLight` | key side sets the mood; a rim separates the subject; silhouette = mystery; one colour = a chapter |
| **Composition** | thirds · centre · leading lines · frame within a frame · foreground object · negative space | where the cast stands (`at`), camera `look`, `type` box placement | centre = confrontation; thirds = conversation with the space; negative space = room for type and for doubt |

## Rules between shots

1. **No two neighbouring shots share both size and move.** Change at least one.
2. **After three close or medium shots, give a wide** so the viewer knows where they are.
3. **Cut on motion.** The camera, the cast or an object is moving at both sides of every cut.
4. **Keep screen direction.** A character walking left to right keeps going left to right across the cut,
   unless the turn is the point.
5. **Match the eye.** Where the eye is at the end of a shot (a point on the thirds) is where the next shot's
   subject starts.
6. **One move per reason.** A vertigo or a snap zoom spends attention; use one where the story turns, not as decoration.
7. **The camera is a character.** Decide what it wants in each shot (to find, to follow, to reveal, to
   confront) and write it in the `why`.

## Writing the `why`

One line per shot: *what the viewer expects at this second, and how this shot confirms or breaks it.*

- "They expect the host to explain; instead the robot flies off with the idea (break)."
- "Second beat on the café: push in because the claim gets personal (confirm, deepen)."
- "45 s: attention dips after a long explanation; a world change to the canyon resets it (break)."

The brain checks that every shot has one (`brain.py check`), and the beat map shows them second by second
(`brain.py beats`).

"""What to do next on a film: the next crew job, what to read, what to write, which check to run.

    python vm_next.py <project dir>

Any model in any IDE can follow a film from start to finish by running this after each job. It reads only
the project's files, so it also tells a new session where the last one stopped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import vm_env

S = vm_env.SKILL_DIR
SC = "python " + str(S / "scripts")


def first(p: Path, *names: str) -> Path | None:
    for n in names:
        hits = sorted(p.glob(n))
        if hits:
            return hits[0]
    return None


def film_id(p: Path) -> str:
    return p.name


def logged(fid: str) -> bool:
    led = vm_env.workbench() / "brain" / "ledger.jsonl"
    return led.exists() and any(json.loads(x).get("film") == fid for x in led.read_text(encoding="utf-8").splitlines() if x.strip())


def shots_file(p: Path) -> Path | None:
    return first(p, "source/shots.js", "storyboard/shots.json")


def jobs(p: Path):
    shots = shots_file(p)
    return [
        ("1 Producer", "crew/01-producer.md", lambda: (p / "brief/brief.yaml").exists() and (p / "brief/picks.json").exists(),
         "brief/brief.yaml with the user's approval quoted, brief/picks.json",
         f'{SC}/pocket.py menu "<request>" --has <footage,voiceover,topic,product>   then show the menu and wait'),
        ("2 Director", "crew/02-director.md", lambda: (p / "brief/direction.md").exists() and (p / "brief/ideas.md").exists(),
         "brief/ideas.md (five concepts with probabilities) and brief/direction.md",
         f'{SC}/brain.py recall   and   {SC}/brain.py ideas --brief "<brief>" --project {p}'),
        ("3 Storyboard", "crew/03-storyboard.md", lambda: shots is not None and bool((p / "brief/brain_check.txt").exists() and "PASS" in (p / "brief/brain_check.txt").read_text(encoding="utf-8")),
         "the shot list (source/shots.js from templates/voxel-diorama, or storyboard/shots.json) with meta and a why on every shot",
         f"{SC}/brain.py check <shots.js> > {p / 'brief/brain_check.txt'}   (must end in PASS; change the plan, not the gate)"),
        ("4 Art director", "crew/04-art-director.md", lambda: (p / "brief/motion_brief.md").exists(),
         "brief/motion_brief.md, assets/ with assets/PROVENANCE.md", "every asset has a provenance line"),
        ("4b Set builder", "crew/04b-set-builder.md", lambda: not shots or all((p / "source/sets" / f"{w}.json").exists() or w in ("studio", "void", "city-night")
                                                                               for w in set(_sets(shots))),
         "source/sets/<name>.json for every world the shots use", f"{SC}/set_preview.py --set <name> --cast --concept <picture>"),
        ("5 Animator", "crew/05-animator.md", lambda: first(p, "renders/draft*.mp4", "renders/*.mp4") is not None,
         "the composition in source/ and a first render in renders/", "npx hyperframes check (0 errors), then npx hyperframes render -o ../renders/draft_1.mp4"),
        ("7 Sound designer", "crew/07-sound.md", lambda: (p / "audio/master.wav").exists() or (p / "audio/NO_SOUND").exists(),
         "audio/master.wav (or an audio/NO_SOUND file saying why there is none)", "loudness -14 LUFS ±1, true peak <= -1.5 dBTP"),
        ("6 Editor", "crew/06-editor.md", lambda: first(p, "qa/draft*/summary.json", "qa/*/summary.json") is not None,
         "a draft with sound and qa/draft/summary.json", f"{SC}/qa.py --tag draft"),
        ("8 Critic", "crew/08-critic.md", lambda: first(p, "qa/*/critique.md") is not None,
         "qa/<tag>/critique.md written by a separate agent that did not build the film", "every P0 and P1 checked on real frames"),
        ("9 Teacher", "crew/09-teacher.md", lambda: logged(film_id(p)),
         "the film in the brain's ledger, lessons and bets updated, house rules for every user note",
         f"{SC}/brain.py log <shots.js> --film {film_id(p)} --score <critic score> --verdict \"<user's words>\"   then   {SC}/brain.py learn"),
    ]


def _sets(shots: Path) -> list[str]:
    try:
        import brain
        return [s.get("set", "studio") for s in brain.load_shots(str(shots)).get("shots", [])]
    except SystemExit:
        return []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    p = Path(sys.argv[1]).resolve()
    if not p.exists():
        raise SystemExit(f"no project at {p}")
    done = []
    for name, page, ok, handover, check in jobs(p):
        try:
            passed = ok()
        except Exception:
            passed = False
        if passed:
            done.append(name)
            continue
        print(f"Project: {p}")
        print(f"Done:    {', '.join(done) or 'nothing yet'}")
        print(f"\nNEXT:    {name}")
        print(f"Read:    {S / page}  (and references/house-rules.md first)")
        print(f"Write:   {handover}")
        print(f"Check:   {check}")
        print("\nWhen the check passes, run this again.")
        return 0
    print(f"Project: {p}\nAll crew jobs are done: {', '.join(done)}. Deliver (crew/06-editor.md, rendering-and-delivery.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

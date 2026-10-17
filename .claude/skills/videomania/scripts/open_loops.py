"""Validate a film's open-loop ledger (storyboard/open_loops.json) against its narration.

Usage:
  open_loops.py --project ID [--ledger storyboard/open_loops.json] [--duration 64.7] [--cta 56.6]

The ledger (template: templates/open_loops.json) records the one main question a viewer should
want answered, where its object is planted on screen, how it updates, and where it closes:

  {"opening": {"benefit": "...", "evidenceBy3": 2.4, "payoffTime": 54.6, "openings_tried": [...]},
   "loops": [{"id": "main", "question": "...", "object": "...", "setup": 2.3,
              "updates": [{"time": 5.1, "state": "..."}], "closure": 38.4,
              "resolution": "...", "supportingSpeech": "exact words from the narration"}]}

Checks (structure only; whether the question is actually clear is judged on rendered frames):
  - an opening with a specific benefit, evidence on screen by 3.0 s, and a payoff time inside the film
  - at least one loop; every loop has setup < updates (in order) < closure
  - every closure lands before the CTA (when --cta is given) and inside the film
  - supportingSpeech is found verbatim (case/punctuation-insensitive) in the narration
  - no loop closes before it is planted, and the main loop is not closed in the first 25 % of the film

Rules from herk-edit-kit's short-form-edit skill (MIT): one main question, planted as a
specific unresolved state, partial answers along the way, earned closure before the CTA. An
object that reappears without resolving anything is a callback, not a closed loop.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def narration_text(proj: Path) -> str:
    for name in ("phrases_roman.json", "phrases.json"):
        p = proj / "transcript" / name
        if p.exists():
            return " ".join(x["text"] for x in json.loads(p.read_text(encoding="utf-8")))
    return ""


def words_of(s: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", s.lower()).split()


def contains(hay: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return n > 0 and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


def validate(ledger: dict | list, narration: str, duration: float | None, cta: float | None) -> dict:
    if isinstance(ledger, list):
        ledger = {"loops": ledger}
    problems: list[str] = []
    op = ledger.get("opening") or {}
    if not op.get("benefit"):
        problems.append("opening.benefit missing: name the specific reason to keep watching")
    ev = op.get("evidenceBy3")
    if ev is None or float(ev) > 3.0:
        problems.append(f"opening.evidenceBy3 = {ev}: the reason to stay must be on screen by 3.0 s")
    pay = op.get("payoffTime")
    if pay is None or (duration and float(pay) > duration):
        problems.append(f"opening.payoffTime = {pay}: must be inside the film")
    loops = ledger.get("loops") or []
    if not loops:
        problems.append("no loops: plant at least one specific unresolved state")
    hay = words_of(narration)
    for lp in loops:
        lid = lp.get("id", "?")
        try:
            setup, closure = float(lp["setup"]), float(lp["closure"])
        except (KeyError, TypeError, ValueError):
            problems.append(f"{lid}: setup and closure times are required")
            continue
        times = [float(u["time"]) for u in lp.get("updates", [])]
        seq = [setup] + times + [closure]
        if any(b <= a for a, b in zip(seq, seq[1:])):
            problems.append(f"{lid}: times must increase setup < updates < closure, got {seq}")
        if cta is not None and closure > cta:
            problems.append(f"{lid}: closes at {closure} s, after the CTA at {cta} s")
        if duration and closure > duration:
            problems.append(f"{lid}: closes at {closure} s, after the film ends ({duration} s)")
        if lid == "main" and duration and closure < 0.25 * duration:
            problems.append(f"main: closes at {closure} s, in the first quarter; the loop resolves too early")
        for k in ("question", "object", "resolution"):
            if not lp.get(k):
                problems.append(f"{lid}: '{k}' missing")
        sp = lp.get("supportingSpeech", "")
        if not sp:
            problems.append(f"{lid}: supportingSpeech missing (quote the narration that closes the loop)")
        elif hay and not contains(hay, words_of(sp)):
            problems.append(f"{lid}: supportingSpeech not found verbatim in the narration: {sp!r}")
    return {"pass": not problems, "loops": len(loops), "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--ledger", default="storyboard/open_loops.json")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--cta", type=float, help="time the call to action starts")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(a.project)
    path = proj / a.ledger
    if not path.exists():
        print(json.dumps({"pass": False, "problems": [f"{path} not found: write it in step 2 (Understand)"]}, indent=2))
        return 1
    res = validate(json.loads(path.read_text(encoding="utf-8")), narration_text(proj), a.duration, a.cta)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

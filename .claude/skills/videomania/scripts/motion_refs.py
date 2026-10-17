"""Search the local Opus 5.5 motion-reference library before designing an edit.

Usage:
  motion_refs.py --query "launch dashboard ui morph glass" [--category motion|explainer|3d|interactive]
                 [--top 6] [--full N] [--update]
  motion_refs.py --effects            # list the 16 premium effect recipes (motion-graphics-skills)
  motion_refs.py --effect "chart morph"   # print one recipe in full
  motion_refs.py --cards "stat dashboard"  [--tier tier1|tier2] [--style vox-explainer|kallaway]
                                          # donor layouts from herk-edit-kit's 406-card library
  motion_refs.py --card kallaway.t1.stat.counter   # path, slots, duration and the card's markup head

Sources (cloned read-only under video-production-workbench/research/, both MIT):
  awesome-opus5-5-videos   703 prompts behind real Opus 5.5 videos (data/videos.json)
  motion-graphics-skills   Charlie Hills' 15 skills incl. 16 effect recipes and review rules
  herk-edit-kit            Nate Herk's kit: 406 HyperFrames cards (vox-explainer, kallaway) with
                           named slots, palettes, transitions catalogue (cloned on first --cards use)

Prints, per matching prompt: author, tags, source link and only the lines that carry
technique (keywords, palette, type, timing, banned lists) — not the whole prompt. Use
--full N to read the Nth hit in full. These are references for craft, never copy
their copy, brands or characters into the user's film.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

RESEARCH = vm_env.workbench() / "research"
AWESOME = RESEARCH / "awesome-opus5-5-videos"
PACK = RESEARCH / "motion-graphics-skills"
HERK = RESEARCH / "herk-edit-kit"
REPOS = {AWESOME: "https://github.com/yihui-dev/awesome-opus5-5-videos.git",
         PACK: "https://github.com/charlie947/motion-graphics-skills.git"}
HERK_URL = "https://github.com/nateherkai/herk-edit-kit.git"

# lines worth surfacing even when they miss the query: they carry the craft
CRAFT = re.compile(r"(banned|never|no cuts|no fades|camera|palette|#[0-9a-f]{6}|type|font|tracking|"
                   r"spring|ease|cubic|stagger|mask|morph|ghost|hold|loop|beat|bpm|grain|texture|"
                   r"halation|vignette|stepped|on twos|rule|concept|one object|continuous)", re.I)


def ensure_repos(update: bool) -> None:
    for path, url in REPOS.items():
        if not path.exists():
            print(f"cloning {url} -> {path}", file=sys.stderr)
            subprocess.run(["git", "clone", "--depth", "1", url, str(path)], check=True)
        elif update:
            subprocess.run(["git", "-C", str(path), "pull", "--ff-only"], check=False)


def load_prompts() -> list[dict]:
    data = json.loads((AWESOME / "data" / "videos.json").read_text(encoding="utf-8"))
    return [v for v in data if v.get("prompt")]


def score(text: str, terms: list[str]) -> float:
    low = text.lower()
    hits = sum(low.count(t) for t in terms)
    covered = sum(1 for t in terms if t in low)
    detail = min(len(text), 6000) / 6000  # detailed briefs teach more than one-liners
    return covered * 3 + min(hits, 30) * 0.3 + detail


def craft_lines(prompt: str, terms: list[str], limit: int = 14) -> list[str]:
    out = []
    for line in re.split(r"[\n]+|(?<=\.)\s+(?=[A-Z])", prompt):
        s = line.strip()
        if 12 <= len(s) <= 400 and (any(t in s.lower() for t in terms) or CRAFT.search(s)):
            out.append(s)
        if len(out) >= limit:
            break
    return out


def cards_index() -> list[dict]:
    if not HERK.exists():
        print(f"cloning {HERK_URL} -> {HERK} (about 400 MB)", file=sys.stderr)
        subprocess.run(["git", "clone", "--depth", "1", HERK_URL, str(HERK)], check=True)
    reg = json.loads((HERK / "style-library" / "registry.json").read_text(encoding="utf-8"))
    out = []
    for st in reg["styles"]:
        for c in st.get("cards", []):
            out.append({**c, "path": str(HERK / "style-library" / c["file"]), "style_status": st.get("status")})
    return out


def effects_index() -> list[tuple[str, str]]:
    ref = (PACK / "skills" / "motion-effects" / "references" / "effects.md").read_text(encoding="utf-8")
    parts = re.split(r"\n### ", ref)
    return [(p.split("\n", 1)[0].strip(), p) for p in parts[1:]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="")
    ap.add_argument("--category", choices=["motion", "explainer", "3d", "interactive"])
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--full", type=int, help="print the Nth hit (1-based) in full")
    ap.add_argument("--update", action="store_true", help="git pull both reference repos first")
    ap.add_argument("--effects", action="store_true")
    ap.add_argument("--effect")
    ap.add_argument("--cards", help="search the card library by words in id/purpose/slots")
    ap.add_argument("--card", help="show one card by id")
    ap.add_argument("--tier", choices=["tier1", "tier2", "custom"])
    ap.add_argument("--style")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cards is not None or args.card:
        cards = cards_index()
        if args.card:
            c = next((c for c in cards if c["id"] == args.card), None)
            if not c:
                print(f"no card {args.card!r}")
                return 1
            print(json.dumps({k: c[k] for k in ("id", "tier", "purpose", "slots", "duration", "path")}, indent=2))
            head = Path(c["path"]).read_text(encoding="utf-8")
            print()
            print(head[:2500])
            print()
            print("DONOR ONLY: 1920x1080, draft status, the source creator's palette and fonts. Rebuild the "
                  "structure at the film's size with the motion brief's tokens; never ship it as is.")
            return 0
        q = [t.lower() for t in re.findall(r"[\w-]+", args.cards)]
        rows = [c for c in cards if (not args.tier or c["tier"] == args.tier) and (not args.style or c["style"] == args.style)]
        def cscore(c):
            hay = " ".join([c["id"], c.get("purpose", ""), " ".join(c.get("slots", []))]).lower()
            return sum(hay.count(t) for t in q) if q else 0
        rows = sorted(rows, key=lambda c: -cscore(c))[: args.top * 3] if q else rows[: args.top * 3]
        for c in rows:
            d = c.get("duration") or {}
            print(f"{c['id']:44s} {c['tier']:6s} {c.get('purpose',''):12s} slots={','.join(c.get('slots', []))}  {d.get('min','?')}-{d.get('max','?')}s")
        print()
        print(f"{len(cards)} cards. Show one: --card <id>. Donor layouts only; restyle to the motion brief.")
        return 0
    ensure_repos(args.update)

    if args.effects or args.effect:
        idx = effects_index()
        if args.effects:
            for name, body in idx:
                use = re.search(r"\*\*Use it when:\*\* (.+)", body)
                print(f"{name:28s} {use.group(1) if use else ''}")
            return 0
        want = args.effect.lower()
        for name, body in idx:
            if want in name.lower():
                print("### " + body.strip())
                return 0
        print(f"no effect matching {args.effect!r}; run --effects for the list")
        return 1

    terms = [t.lower() for t in re.findall(r"[\w.#+-]+", args.query) if len(t) > 1]
    if not terms:
        ap.error("--query is required (or --effects / --effect)")
    rows = [v for v in load_prompts() if not args.category or v.get("category") == args.category]
    ranked = sorted(rows, key=lambda v: -score(v["prompt"], terms))[: args.top]
    if args.full:
        v = ranked[args.full - 1]
        print(f"# {v['author']} · {v.get('category')} · {', '.join(v.get('tech_tags') or [])}\n{v.get('post_url')}\n")
        print(v["prompt"])
        return 0
    for i, v in enumerate(ranked, 1):
        print(f"\n[{i}] {v['author']} · {v.get('category')} · {', '.join(v.get('tech_tags') or [])} · "
              f"{len(v['prompt'])} chars\n    {v.get('post_url')}")
        for s in craft_lines(v["prompt"], terms):
            print("    - " + s[:240])
    print(f"\n{len(rows)} prompts searched. Read one in full with --full N.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

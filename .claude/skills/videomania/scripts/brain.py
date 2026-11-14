"""The director's brain: memory across films, forced variety, measured surprise, and self-improvement.

    python brain.py recall  [--brief "..."]                 what past films did and what the brain has learned
    python brain.py ideas   --brief "..." [--seed N] [--project DIR]
                                                            draws from the Pocket + a constraint card + the
                                                            divergence prompt (write to brief/ideas.md)
    python brain.py check   <shots.js|shots.json> [--project DIR]
                                                            novelty gate (vs the last 10 films) + surprise budget
                                                            + "why" coverage; exit 1 when a gate fails
    python brain.py beats   <shots.js>                      second-by-second map: what happens, why, dead seconds
    python brain.py log     <shots.js> --film ID [--score N] [--verdict "user's words"] [--good|--bad]
                                                            add the film to the ledger (crew job 9)
    python brain.py bet add "<try this>" [--tags a,b]       a new idea to test
    python brain.py bet result <BET-ID> --film ID --win|--loss
    python brain.py learn                                   update weights, promote bets that won twice, retire losers
    python brain.py stats

Brain files live in <workbench>/brain/ (ledger.jsonl, weights.json, experiments.jsonl, beats/) and the
skill's brain/ folder (lessons.md, constraints.json), so lessons travel with the skill and the film history
stays on the machine. Everything here is a script: the gates decide, not the model's mood.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

import vm_env

SKILL_BRAIN = vm_env.SKILL_DIR / "brain"
AXES = ["device", "home_world", "palette", "hook", "signature", "transitions", "structure"]
IMPOSSIBLE_CAMS = {"vertigo"}


def bdir() -> Path:
    d = vm_env.workbench() / "brain"
    (d / "beats").mkdir(parents=True, exist_ok=True)
    return d


def jl_read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def jl_write(p: Path, rows: list[dict]) -> None:
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def ledger() -> list[dict]:
    return jl_read(bdir() / "ledger.jsonl")


# --------------------------------------------------------------------------------------- reading a film

def load_shots(path: str) -> dict:
    p = Path(path)
    if p.suffix == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    js = ("const fs=require('fs'),vm=require('vm');const c={window:{}};"
          "vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.window.SHOTS||null))")
    r = subprocess.run(["node", "-e", js, str(p)], capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.strip() in ("", "null"):
        raise SystemExit(f"could not read {p}: {r.stderr.strip()[:300] or 'no window.SHOTS'}")
    return json.loads(r.stdout)


def words_of(s: dict) -> list[tuple]:
    out = []
    for g in s.get("lines") or []:
        for w in g:
            if w and w[0] != "\n":
                out.append(tuple(w) + (None,) * (4 - len(w)))
    return out


def features(S: dict) -> dict:
    """Everything the brain compares films by, read from the shot list."""
    shots = S.get("shots", [])
    meta = S.get("meta", {})
    dur = S.get("duration") or (shots[-1]["t1"] if shots else 0)
    sets = [s.get("set", "studio") for s in shots]
    secs = Counter()
    for s in shots:
        secs[s.get("set", "studio")] += s["t1"] - s["t0"]
    moves, trans, cams, acts = Counter(), [], [], Counter()
    for s in shots:
        cam = (s.get("cam") or {}).get("preset") or ("custom" if s.get("cam") else "hero-push")
        c0 = s.get("cam") or {}
        # hand-placed cameras are compared by their path, so three different custom moves are not "the same camera"
        if c0.get("keys"):   # a keyframed take is compared by where it starts and ends
            k0, k1 = c0["keys"][0], c0["keys"][-1]
            cams.append("keys@" + json.dumps([k0.get("from"), k0.get("look"), k1.get("from"), k1.get("look")]))
        else:
            cams.append(cam if cam != "custom" else "custom@" + json.dumps([c0.get("from"), c0.get("to"), c0.get("look")]))
        if (s.get("cam") or {}).get("shake"):
            moves["camera/handheld"] += 1
        if s.get("focus") and isinstance(s.get("focus"), dict):
            moves["camera/rack"] += 1
        moves["camera/" + cam] += 1
        trans.append(s.get("out", "cut"))
        for w in words_of(s):
            if w[2] in ("punch", "num"):
                moves["type/" + ("punch" if w[2] == "punch" else "count")] += 1
            if w[3]:
                moves["type/" + {"type": "typed"}.get(w[3], w[3])] += 1
        for w in s.get("type3d") or []:
            moves["type/through" if w.get("anim") == "through" else "type/word3d"] += 1
        for k, mid in (("burst", "screen/burst"), ("search", "screen/search"), ("meter", "screen/meter"), ("cursor", "screen/cursor"),
                       ("fan", "object/fan"), ("strip", "object/strip"), ("cards", "object/cards"), ("props", "object/doc"), ("screen", "object/monitor")):
            if s.get(k):
                moves[mid] += 1
        for c in s.get("cast") or []:
            for a in c.get("acts") or ([{"do": "walk"}] if c.get("to") else []):
                acts[a.get("do", "pose")] += 1
                if a.get("do") in ("fly", "jump", "run"):
                    moves["cast/" + {"run": "run-in"}.get(a["do"], a["do"])] += 1
    world_changes = sum(1 for a, b in zip(sets, sets[1:]) if a != b)
    impossible = sum(1 for s in shots if any(a.get("do") == "fly" for c in s.get("cast") or [] for a in c.get("acts") or [])
                     or any(w.get("anim") == "through" for w in s.get("type3d") or [])
                     or (s.get("cam") or {}).get("preset") in IMPOSSIBLE_CAMS or s.get("impossible")
                     or s.get("particles") or s.get("relief")
                     or any(abs((k.get("fov") or 0) - ((s.get("cam") or {}).get("keys") or [{}])[0].get("fov", 0)) >= 12
                            for k in (s.get("cam") or {}).get("keys") or []))
    sig = meta.get("signature") or (max(moves, key=lambda m: (not m.startswith("camera/hero"), moves[m])) if moves else "")
    first = shots[0] if shots else {}
    hook = meta.get("hook") or ((first.get("cam") or {}).get("preset", "custom") + "+" + ",".join(sorted(k for k in ("burst", "search", "type3d", "cursor") if first.get(k))))
    return {
        "duration": round(dur, 2), "shots": len(shots),
        "device": meta.get("device") or meta.get("concept", "")[:60] or "unstated",
        "home_world": secs.most_common(1)[0][0] if secs else "", "worlds": sorted(secs),
        "palette": (S.get("palette") or {}).get("voice", "").lower(),
        "hook": hook, "signature": sig,
        "transitions": sorted(set(trans) - {"cut"}), "cameras": cams, "moves": dict(moves), "acts": dict(acts),
        "structure": meta.get("structure") or f"{len(shots)} shots / {len(secs)} worlds",
        "world_changes": world_changes, "impossible": impossible,
        "why": sum(1 for s in shots if s.get("why")), "constraint": meta.get("constraint", ""),
    }


# --------------------------------------------------------------------------------------------- recall

def cmd_recall(a) -> int:
    rows = ledger()
    print(f"Films in the ledger: {len(rows)}")
    for r in rows[-10:]:
        f = r["features"]
        print(f"  - {r['film']} ({r['date']}): device={f['device']}; worlds={','.join(f['worlds'])}; signature={f['signature']}; "
              f"score={r.get('score', '-')}; verdict={r.get('verdict') or '-'}")
    if rows:
        used = Counter()
        for r in rows[-5:]:
            used.update(r["features"]["moves"].keys())
            used.update("world/" + w for w in r["features"]["worlds"])
        print("\nOverused lately (last 5 films) — avoid unless the brief demands it:")
        print("  " + ", ".join(f"{k} ×{v}" for k, v in used.most_common(12)))
    w = json.loads((bdir() / "weights.json").read_text(encoding="utf-8")) if (bdir() / "weights.json").exists() else {}
    if w:
        good = sorted(((v["mean"], k) for k, v in w.items() if v["n"] >= 2), reverse=True)
        if good:
            print("\nWhat has scored well (mean score, at least 2 films): " + ", ".join(f"{k} {m:.0f}" for m, k in good[:8]))
            print("What has scored badly: " + ", ".join(f"{k} {m:.0f}" for m, k in good[-5:]))
    print("\nLessons:")
    for line in (SKILL_BRAIN / "lessons.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("- [L-"):
            print("  " + line)
    open_bets = [b for b in jl_read(bdir() / "experiments.jsonl") if b["status"] == "open"]
    if open_bets:
        print("\nOpen bets to try on this film if it fits:")
        for b in open_bets:
            print(f"  - {b['id']}: {b['try']} (wins {b['wins']}, losses {b['losses']})")
    if rows and len(rows) % 10 == 0:
        print("\nREPLAY DUE: this is film", len(rows) + 1, "- remake one old brief with the current rules and compare both with the same critic.")
    return 0


# ---------------------------------------------------------------------------------------------- ideas

DIVERGE = """## Divergence (write this section before choosing a concept)

1. Write **five concepts** for the brief. Each uses a different carrying device (a journey, a transformation,
   a game, a rivalry, a machine, a world inside an object…). For each write: the device in one line, the
   signature moment, the worlds it visits, and **your honest estimate of the probability that a typical
   director would pitch it** (the five add up to 1).
2. Every concept must use the constraint card and at least two of the draws below.
3. Score each 1–5 on: stops the scroll by 3 s · serves the point · buildable with the kit · could only be
   this subject.
4. Choose the concept with the **lowest probability** that scores at least 3 on every line. Keep the safest
   one as the fallback. Write all five in brief/ideas.md: the unused ones are the next films' starting points.
"""


def pocket_draws(rng: random.Random, recent: set[str]) -> list[tuple[str, str, str]]:
    db = vm_env.workbench() / "pocket" / "pocket.db"
    if not db.exists():
        return []
    con = sqlite3.connect(db)
    out = []
    for kind, n in (("style", 1), ("treatment", 1), ("move", 2), ("moment", 1), ("prompt", 1)):
        rows = [r for r in con.execute("SELECT id, name, summary FROM items WHERE kind=?", (kind,)) if r[0] not in recent]
        rng.shuffle(rows)
        out += [(kind, r[0], r[2][:170]) for r in rows[:n]]
    return out


def cmd_ideas(a) -> int:
    rows = ledger()
    seed = a.seed if a.seed is not None else int(dt.datetime.now().timestamp()) % 100000
    rng = random.Random(seed)
    recent = set()
    for r in rows[-3:]:
        recent.update("move/" + m for m in r["features"]["moves"])
    cards = json.loads((SKILL_BRAIN / "constraints.json").read_text(encoding="utf-8"))["cards"]
    used_cards = {r["features"].get("constraint") for r in rows[-8:]}
    card = rng.choice([c for c in cards if c not in used_cards] or cards)
    draws = pocket_draws(rng, recent)
    worlds = sorted({w for r in rows[-3:] for w in r["features"]["worlds"]})
    out = [f"# Ideas for: {a.brief}", "", f"Seed {seed} (run again with another --seed for different draws).", "",
           "## Constraint card (the concept must obey it)", "", f"> {card}", "",
           "## Draws from the Pocket (use at least two)", ""]
    out += [f"- [{k}] `{i}`: {s}" for k, i, s in draws]
    out += ["", "## Avoid (used in the last 3 films)", "",
            f"- worlds: {', '.join(worlds) or 'none yet'}",
            f"- moves: {', '.join(sorted(m.split('/', 1)[1] for m in recent)[:14]) or 'none yet'}", "", DIVERGE,
            "## Then", "", "Put the choice in the shot list's `meta`: `{ concept, device, hook, signature, structure, constraint }`,",
            "and give every shot a `why` (what the viewer expects at this second and how the shot confirms or breaks it).",
            "Run `python brain.py check <shots.js>` before building."]
    text = "\n".join(out) + "\n"
    if a.project:
        p = Path(a.project) / "brief" / "ideas_seed.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"written: {p}")
    print(text)
    return 0


# ---------------------------------------------------------------------------------------------- check

def same(axis: str, x, y) -> bool:
    if isinstance(x, list):
        sx, sy = set(x), set(y)
        return bool(sx | sy) and len(sx & sy) / len(sx | sy) >= 0.6
    return bool(x) and x == y and x != "unstated"


def cmd_check(a) -> int:
    S = load_shots(a.shots)
    f = features(S)
    shots = S.get("shots", [])
    fails, warns = [], []
    # 1. novelty: differ from each of the last 10 films on at least 4 of the 7 axes
    print("Novelty (must differ on at least 4 of 7 axes from each of the last 10 films)")
    film_id = (S.get("meta") or {}).get("film")
    base = lambda f: re.sub(r"-v\d+$", "", f or "")   # versions of the same film are revisions, not rivals
    for r in [r for r in ledger() if base(r["film"]) != base(film_id)][-10:]:
        g = r["features"]
        shared = [ax for ax in AXES if same(ax, f[ax], g[ax])]
        mark = "FAIL" if len(shared) > 3 else "ok"
        print(f"  {mark:<4} vs {r['film']:<22} shares {len(shared)}: {', '.join(shared) or '-'}")
        if len(shared) > 3:
            fails.append(f"too close to {r['film']} ({', '.join(shared)})")
    # 2. surprise budget
    dur = f["duration"] or 1
    print("\nSurprise budget")
    # Rhythm, not forcing (lesson L-1, rewritten 2026-11-14): chapters are long takes that change INSIDE the take,
    # on the word; hard cuts come at chapter turns and in short bursts. See references/rhythm-and-direction.md.
    lens = sorted(s["t1"] - s["t0"] for s in shots) or [0]
    med = lens[len(lens) // 2]
    cuts_min = (len(shots) - 1) / dur * 60
    print(f"  median take {med:.1f} s (want 2.5–9), cuts per minute {cuts_min:.1f} (reference reel ~16, want 8–22)")
    if med < 2.0:
        fails.append(f"median take {med:.1f} s: cuts are forcing the rhythm; merge shots into chapters that change inside the take")
    if cuts_min > 26:
        fails.append(f"{cuts_min:.0f} cuts a minute: too many; keep cuts for chapter turns and bursts")
    if dur > 40 and f["world_changes"] < 3:
        fails.append("fewer than 3 world changes: the film never leaves home")
    for s in shots:
        L = s["t1"] - s["t0"]
        if L <= 6:
            continue
        ev = len(s.get("lines") or []) + len(s.get("wash") or []) + len((s.get("cam") or {}).get("keys") or [])             + sum(len(c.get("acts") or []) + len(c.get("dissolve") or []) for c in s.get("cast") or [])             + len(s.get("cards") or []) + len(s.get("burst") or []) + len(s.get("props") or []) + len(s.get("type3d") or [])
        if ev < L / 2.5:
            warns.append(f"take {s.get('id')} is {L:.1f} s with {ev} changes inside it: give it a change on the word every 2–3 s (camera key, wash, act, card)")
    need_imp = max(1, int(dur // 20)) if dur >= 10 else 0
    print(f"  impossible moments: {f['impossible']} (need >= {need_imp})")
    if f["impossible"] < need_imp:
        fails.append("not enough impossible moments: a flight, a word through the lens, vertigo, a world from a picture")
    for name, seq in (("transition", [s.get("out", "cut") for s in shots]), ("camera", f["cameras"])):
        for i in range(len(seq) - 2):
            if seq[i] == seq[i + 1] == seq[i + 2] and seq[i] != "cut":
                fails.append(f"same {name} three times in a row: {seq[i]} (shots {i + 1}-{i + 3})")
                break
    over = {m: n for m, n in f["moves"].items() if n > 3 and not m.startswith("camera/") and not m.startswith("type/punch")}
    if over:
        warns.append("moves used more than three times: " + ", ".join(f"{m} ×{n}" for m, n in over.items()))
    distinct = len([m for m in f["moves"] if not m.startswith("camera/hero")])
    print(f"  distinct moves: {distinct} (want >= 6 for films over 20 s)")
    if dur > 20 and distinct < 6:
        warns.append("fewer than 6 different moves")
    for i, s in enumerate(shots):
        L = s["t1"] - s["t0"]
        if L < 0.8 or (L > 25 and i < len(shots) - 1):
            warns.append(f"shot {s.get('id', i + 1)} lasts {L:.1f} s (keep 0.8–25 s; long takes need changes inside)")
    acts = f["acts"]
    if sum(acts.values()) and len(acts) < 3:
        warns.append(f"the cast does only {len(acts)} kind(s) of action: {', '.join(acts)} (want 3)")
    # 2b. asset-first (user rule 2026-11-14): things the viewer reads as objects or screens must be real pictures
    # (ChatGPT image bridge, real footage, the film's own frames) stitched in by code - not drawn by code.
    # A shot may keep a drawn element on purpose with `drawn_ok: "<why>"` (e.g. deliberately generic slop).
    drawn = []
    for s in shots:
        if s.get("drawn_ok"):
            continue
        sid = s.get("id", "?")
        sc = s.get("screen") or {}
        if sc and sc.get("kind") in ("player", "code", "timeline", "chat") and not sc.get("src"):
            drawn.append(f"{sid}: screen '{sc.get('kind')}' is drawn (use kind 'frames' with real footage or 'image' with a generated screen)")
        for c in s.get("cards") or []:
            if not c.get("img"):
                drawn.append(f"{sid}: card '{c.get('label', c.get('id'))}' has a drawn icon (give it img: a generated icon)")
        if s.get("fan") and not s["fan"].get("imgs"):
            drawn.append(f"{sid}: the fan is drawn cards (give it imgs: real frames or generated thumbnails)")
        if s.get("strip") and not s["strip"].get("imgs"):
            drawn.append(f"{sid}: the strip is drawn thumbnails (give it imgs)")
        for pr in s.get("props") or []:
            if pr.get("kind") == "doc" and not pr.get("img"):
                drawn.append(f"{sid}: prop '{pr.get('id')}' is a drawn box (use a generated picture or the mascot's hold_doc pose)")
    print(f"\nAsset-first: {len(drawn)} code-drawn object(s) where a real asset belongs")
    for d in drawn[:12]:
        print("  - " + d)
    if drawn:
        fails.append(f"{len(drawn)} code-drawn objects: generate them first (references/asset-first.md), or mark the shot drawn_ok with a reason")
    # 3. why coverage
    print(f"\nWhy: {f['why']} of {len(shots)} shots have a reason written")
    if f["why"] < len(shots):
        miss = [s.get("id", str(i + 1)) for i, s in enumerate(shots) if not s.get("why")]
        (fails if f["why"] < len(shots) / 2 else warns).append("shots without a `why`: " + ", ".join(miss))
    meta = S.get("meta") or {}
    for k in ("concept", "device", "hook", "constraint"):
        if not meta.get(k):
            warns.append(f"meta.{k} is missing")
    print()
    for w in warns:
        print("WARN  " + w)
    for x in fails:
        print("FAIL  " + x)
    print("PASS" if not fails else f"\n{len(fails)} gate(s) failed: change the plan, not the gate.")
    return 1 if fails else 0


# ---------------------------------------------------------------------------------------------- beats

def beat_events(S: dict) -> list[tuple[float, str]]:
    ev = []
    for s in S.get("shots", []):
        cam = (s.get("cam") or {}).get("preset", "custom")
        ev.append((s["t0"], f"[{s.get('id')}] {s.get('set', 'studio')} · {cam}" + (f" · why: {s['why']}" if s.get("why") else " · why: (none)")))
        for w in words_of(s):
            ev.append((w[1], f"word '{w[0]}'" + (f" ({w[2]})" if w[2] and w[2] != "say" else "") + (f" +{w[3]}" if w[3] else "")))
        for w in s.get("type3d") or []:
            ev.append((w.get("t", s["t0"]), f"3D word '{w['text']}' {w.get('anim', 'slam')}"))
        for c in s.get("cast") or []:
            for act in c.get("acts") or []:
                ev.append(((act.get("t") or [s["t0"]])[0], f"{c['who']} {act.get('do')}"))
        for k in ("burst", "fan", "meter"):
            for x in (s.get(k) if isinstance(s.get(k), list) else [s.get(k)] if s.get(k) else []):
                ev.append((x.get("t", s["t0"]), k))
        for k in ("search", "cursor", "strip"):
            if s.get(k):
                ev.append((s[k]["t"][0], k))
        if s.get("out", "cut") != "cut":
            ev.append((s["t1"], f"transition {s['out']}"))
    return sorted(ev)


def cmd_beats(a) -> int:
    S = load_shots(a.shots)
    ev = beat_events(S)
    dur = S.get("duration") or 0
    dead = []
    print(f"{'sec':>4}  what happens")
    for sec in range(int(dur + 0.999)):
        here = [e for t, e in ev if sec <= t < sec + 1]
        print(f"{sec:>4}  " + (" | ".join(here) if here else "-"))
        if not here and not any(sec - 1 <= t < sec + 2 for t, _ in ev):
            dead.append(sec)
    if dead:
        print(f"\nDead stretches (nothing new for 2 s or more) at: {', '.join(map(str, dead))} s")
    return 0


# ------------------------------------------------------------------------------------------------ log

def cmd_log(a) -> int:
    S = load_shots(a.shots)
    rows = [r for r in ledger() if r["film"] != a.film]
    f = features(S)
    row = {"film": a.film, "date": dt.date.today().isoformat(), "features": f, "score": a.score, "verdict": a.verdict,
           "good": True if a.good else (False if a.bad else None), "source": str(Path(a.shots).resolve()), "meta": S.get("meta", {})}
    rows.append(row)
    jl_write(bdir() / "ledger.jsonl", rows)
    (bdir() / "beats" / f"{a.film}.json").write_text(json.dumps({"film": a.film, "duration": f["duration"], "events": beat_events(S),
                                                                  "score": a.score}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"logged {a.film}: {f['shots']} shots, worlds {','.join(f['worlds'])}, signature {f['signature']}. Ledger has {len(rows)} films.")
    return 0


# ----------------------------------------------------------------------------------------- bets, learn

def cmd_bet(a) -> int:
    p = bdir() / "experiments.jsonl"
    bets = jl_read(p)
    if a.op == "add":
        bid = f"BET-{len(bets) + 1}"
        bets.append({"id": bid, "try": a.text, "tags": [t for t in (a.tags or "").split(",") if t], "status": "open", "wins": 0, "losses": 0,
                     "films": [], "date": dt.date.today().isoformat()})
        print(f"{bid} opened: {a.text}")
    else:
        b = next((x for x in bets if x["id"] == a.text), None)
        if not b:
            raise SystemExit(f"no bet {a.text}")
        if a.win:
            b["wins"] += 1
        else:
            b["losses"] += 1
        b["films"].append({"film": a.film, "win": bool(a.win)})
        print(f"{b['id']}: wins {b['wins']}, losses {b['losses']}")
    jl_write(p, bets)
    return 0


def cmd_learn(_) -> int:
    rows = ledger()
    agg: dict[str, list[float]] = {}
    for r in rows:
        s = r.get("score")
        if s is None and r.get("good") is not None:
            s = 80 if r["good"] else 45
        if s is None:
            continue
        f = r["features"]
        keys = [f"move/{m}" for m in f["moves"]] + [f"world/{w}" for w in f["worlds"]] + [f"transition/{t}" for t in f["transitions"]]
        for k in keys:
            agg.setdefault(k, []).append(float(s))
    weights = {k: {"n": len(v), "mean": sum(v) / len(v)} for k, v in agg.items()}
    (bdir() / "weights.json").write_text(json.dumps(weights, indent=1), encoding="utf-8")
    # bets: two wins and no loss since -> a rule; a loss resets the count
    p = bdir() / "experiments.jsonl"
    bets = jl_read(p)
    lessons = (SKILL_BRAIN / "lessons.md").read_text(encoding="utf-8")
    n = len(re.findall(r"^- \[L-\d+\]", lessons, re.M))
    promoted = 0
    for b in bets:
        if b["status"] != "open":
            continue
        streak = 0
        for x in b["films"]:
            streak = streak + 1 if x["win"] else 0
        if streak >= 2:
            n += 1
            films = ", ".join(x["film"] for x in b["films"] if x["win"])
            lessons = lessons.rstrip() + f"\n- [L-{n}] {b['try']}. Evidence: {films}. Confidence: {b['wins']}/{b['wins'] + b['losses']}.\n"
            b["status"] = "promoted"
            promoted += 1
        elif b["losses"] >= 3 and b["wins"] == 0:
            b["status"] = "retired"
    (SKILL_BRAIN / "lessons.md").write_text(lessons, encoding="utf-8")
    jl_write(p, bets)
    print(f"weights for {len(weights)} items from {len(rows)} films; {promoted} bet(s) promoted to lessons")
    return 0


def cmd_stats(_) -> int:
    rows = ledger()
    print(f"films {len(rows)}, bets {len(jl_read(bdir() / 'experiments.jsonl'))}, beats maps {len(list((bdir() / 'beats').glob('*.json')))}")
    c = Counter()
    for r in rows:
        c.update(r["features"]["moves"].keys())
    print("most used moves: " + ", ".join(f"{k} ×{v}" for k, v in c.most_common(10)))
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("recall"); s.add_argument("--brief"); s.set_defaults(fn=cmd_recall)
    s = sub.add_parser("ideas"); s.add_argument("--brief", required=True); s.add_argument("--seed", type=int); s.add_argument("--project"); s.set_defaults(fn=cmd_ideas)
    s = sub.add_parser("check"); s.add_argument("shots"); s.add_argument("--project"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("beats"); s.add_argument("shots"); s.set_defaults(fn=cmd_beats)
    s = sub.add_parser("log"); s.add_argument("shots"); s.add_argument("--film", required=True); s.add_argument("--score", type=float)
    s.add_argument("--verdict"); s.add_argument("--good", action="store_true"); s.add_argument("--bad", action="store_true"); s.set_defaults(fn=cmd_log)
    s = sub.add_parser("bet"); s.add_argument("op", choices=["add", "result"]); s.add_argument("text"); s.add_argument("--tags"); s.add_argument("--film")
    g = s.add_mutually_exclusive_group(); g.add_argument("--win", action="store_true"); g.add_argument("--loss", action="store_true"); s.set_defaults(fn=cmd_bet)
    sub.add_parser("learn").set_defaults(fn=cmd_learn)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

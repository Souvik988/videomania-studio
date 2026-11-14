"""Sound design from the shot list: one cue per picture event, with the density caps from crew job 7.

    python sfx_from_shots.py <shots.js> -o storyboard/sfx_cues.json

Every cue names the picture event it sits on. Rules (from the reference reel and crew/07-sound.md):
transitions get a whoosh, glitch or boom by kind; punch words a low tap, the biggest ones a boom (at most one
boom per 10 s); words flying through the lens get a riser into a boom; numbers tick; sticker bursts sparkle;
typing types; a cursor clicks; flights whoosh; jumps get air; particle shapes shimmer; cards land with paper.
Then caps: no two cues within 0.12 s (the louder wins), and at most one cue per 0.8 s on average.
Render the stem with sfx_design.py (stem mode) and mix under the voice.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import brain

PRIORITY = {"boom": 9, "riser": 8, "whoosh_long": 7, "glitch": 7, "whoosh": 6, "whoosh_down": 6, "sparkle": 5, "typing": 5,
            "tap_lo": 5, "ticktock": 4, "click": 4, "shutter": 4, "send": 4, "ding": 4, "paper": 3, "air": 3, "tap": 3, "tap_hi": 2}


def build(S: dict) -> list[dict]:
    cues = []
    add = lambda t, name, why, gain=-10, pan=0.0: cues.append({"t": round(max(0.0, t), 3), "name": name, "gain_db": gain, "pan": pan, "reason": why})
    shots = S["shots"]
    for i, s in enumerate(shots):
        out = s.get("out", "cut")
        nxt = shots[i + 1] if i + 1 < len(shots) else None
        if nxt:
            T = s["t1"]
            if out == "flash":
                add(T - 0.35, "whoosh_long", f"flash into {nxt['id']}", -9)
            elif out in ("mosaic", "dots", "pixelate"):
                add(T - 0.2, "glitch", f"{out} into {nxt['id']}", -12)
            elif out == "whip":
                add(T - 0.18, "whoosh", f"whip into {nxt['id']}", -9, -0.3 if i % 2 else 0.3)
            elif out == "iris":
                add(T - 0.3, "whoosh_down", f"iris into {nxt['id']}", -10)
            elif nxt.get("set") != s.get("set"):
                add(T, "air", f"world change into {nxt['id']}", -14)
        for w in brain.words_of(s):
            if w[2] == "punch":
                add(w[1], "tap_lo", f"punch word {w[0]}", -6)
                add(w[1] + 0.01, "boom", f"punch word {w[0]} (big)", -11)
            elif w[2] == "num":
                add(w[1], "ticktock", f"number {w[0]} counts up", -14)
            elif w[3] == "jitter":
                add(w[1], "tap_hi", f"letters drop in: {w[0]}", -16)
            elif w[3] in ("mark", "bracket"):
                add(w[1] + 0.05, "tap", f"{w[3]} on {w[0]}", -15)
        for w in s.get("type3d") or []:
            if w.get("anim") == "through":
                add(w["t"] - 0.05, "riser", f"'{w['text']}' flies at the lens", -9)
                add(w["t"] + (w.get("dur") or 1) * 0.8, "boom", f"'{w['text']}' passes the lens", -6)
            else:
                add(w["t"], "boom", f"3D word {w['text']} lands", -9)
        for b in s.get("burst") or []:
            add(b["t"], "sparkle", "sticker burst", -10, (b.get("x", 0.5) - 0.5) * 1.2)
        if s.get("search"):
            add(s["search"]["t"][0] + 0.1, "typing", f"typing '{s['search']['text']}'", -13)
        if s.get("cursor"):
            add(s["cursor"]["t"][1], "click", "cursor clicks", -8)
        if s.get("meter"):
            add(s["meter"]["t"] + 0.1, "ticktock", f"level bar fills ({s['meter'].get('label')})", -14)
        if s.get("fan"):
            add(s["fan"]["t"], "paper", "cards dealt", -9)
        if s.get("strip"):
            add(s["strip"]["t"][0], "whoosh_long", "film strip pours through", -12)
        for c in s.get("cards") or []:
            add(c.get("t", s["t0"]), "tap_hi", f"card {c.get('label')} lands", -14)
        for p in (s.get("props") or []):
            add(p.get("t", s["t0"]), "paper", f"prop {p['id']} appears", -11)
        if s.get("particles"):
            for shape, t in s["particles"].get("seq", [])[1:]:
                add(t, "shutter" if shape != "burst" else "glitch", f"particles become a {shape}", -12)
        for c in s.get("cast") or []:
            for a in c.get("acts") or []:
                t0 = (a.get("t") or [s["t0"]])[0]
                if a.get("do") == "fly":
                    add(t0, "whoosh", f"{c['who']} takes off", -11, -0.4)
                elif a.get("do") == "jump":
                    add(t0, "air", f"{c['who']} jumps", -16)
                elif a.get("do") == "run":
                    add(t0, "whoosh", f"{c['who']} runs in", -12, -0.5)
    return cues


def cap(cues: list[dict], dur: float) -> list[dict]:
    cues.sort(key=lambda c: c["t"])
    kept: list[dict] = []
    last_boom = -99.0
    for c in cues:
        if c["name"] == "boom":
            if c["t"] - last_boom < 10:
                continue
            last_boom = c["t"]
        if kept and c["t"] - kept[-1]["t"] < 0.12:
            if PRIORITY.get(c["name"], 1) > PRIORITY.get(kept[-1]["name"], 1):
                kept[-1] = c
            continue
        kept.append(c)
    limit = int(dur / 0.8)
    while len(kept) > limit:   # drop the least important, keeping structure cues
        k = min(range(len(kept)), key=lambda i: PRIORITY.get(kept[i]["name"], 1))
        kept.pop(k)
    return kept


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shots")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    S = brain.load_shots(a.shots)
    dur = S.get("duration") or S["shots"][-1]["t1"]
    cues = cap(build(S), dur)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"duration": dur, "cues": cues}, indent=1, ensure_ascii=False), encoding="utf-8")
    booms = sum(1 for c in cues if c["name"] == "boom")
    print(f"{len(cues)} cues ({len(cues) / dur * 0.8:.2f} per 0.8 s), {booms} booms, written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

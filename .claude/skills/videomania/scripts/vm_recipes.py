"""Recipes: whole films saved as presets. A recipe is a folder recipes/<id>/ with recipe.json and the files that
make the film: shots.js (the direction), score.sh (the sound), fx_cues.json (editor effects + hook), optional
shots_reel.js, assets.json (what the film needs; the starter set covers the defaults).

    vm recipe list | show <id> | save <film> <id> [--title --about] | use <id> <film>

`use` on a NEW voiceover copies the recipe into the project as shots.recipe.js / score.recipe.sh / fx_cues.recipe.json
and writes storyboard/retime.md: Claude keeps the recipe's structure, devices and moves and re-times them on the new
words. `use` on the SAME voiceover (a remake) copies everything into place.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RD = SKILL / "recipes"
FILES = {"shots": "shots.js", "score": "score.sh", "fx": "fx_cues.json", "reel": "shots_reel.js", "assets": "assets.json"}


def listing() -> list[dict]:
    out = []
    for f in sorted(RD.glob("*/recipe.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        out.append({k: r.get(k) for k in ("id", "title", "about", "duration", "format", "tags")})
    return out


def get(rid: str) -> dict:
    f = RD / rid.replace("recipe:", "") / "recipe.json"
    if not f.exists():
        raise SystemExit(f"no recipe '{rid}' (vm recipe list)")
    r = json.loads(f.read_text(encoding="utf-8"))
    r["dir"] = str(f.parent)
    r["files"] = {k: str(f.parent / v) for k, v in FILES.items() if (f.parent / v).exists()}
    return r


def file(r: dict, key: str) -> Path:
    p = Path(r["dir"]) / FILES[key]
    if not p.exists():
        raise SystemExit(f"recipe {r['id']} has no {FILES[key]}")
    return p


def save(p: Path, rid: str, title: str, about: str) -> dict:
    d = RD / rid
    d.mkdir(parents=True, exist_ok=True)
    src = {"shots": p / "source" / "shots.js", "score": p / "audio" / "score.sh", "fx": p / "storyboard" / "fx_cues.json",
           "reel": p / "_landscape" / "shots_reel.js", "assets": p / "storyboard" / "assets.json"}
    copied = []
    for k, f in src.items():
        if f.exists():
            shutil.copy2(f, d / FILES[k])
            copied.append(FILES[k])
    st = json.loads((p / "vm.json").read_text(encoding="utf-8")) if (p / "vm.json").exists() else {}
    meta = {}
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        import brain
        meta = brain.load_shots(str(src["shots"])).get("meta", {})
    except Exception:
        pass
    r = {"id": rid, "title": title, "about": about or meta.get("concept", ""), "from_film": p.name,
         "duration": st.get("duration"), "format": st.get("format"), "saved": dt.date.today().isoformat(),
         "meta": meta, "tags": [t for t in (meta.get("device", "") + " " + meta.get("hook", "")).split()[:12]],
         "files": copied,
         "needs": "the voxel-starter assets (mascot, icons, screens, backdrop, plates); songs are NOT included (bring your own)"}
    (d / "recipe.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    return r


def use(rid: str, p: Path) -> dict:
    r = get(rid)
    st = json.loads((p / "vm.json").read_text(encoding="utf-8")) if (p / "vm.json").exists() else {}
    same = r.get("from_film") and st.get("voice", "").split("/")[-1] and r.get("duration") == st.get("duration")
    placed = {}
    targets = {"shots": p / "source" / ("shots.js" if same else "shots.recipe.js"),
               "score": p / "audio" / ("score.sh" if same else "score.recipe.sh"),
               "fx": p / "storyboard" / ("fx_cues.json" if same else "fx_cues.recipe.json"),
               "assets": p / "storyboard" / "assets.json"}
    for k, t in targets.items():
        f = Path(r["dir"]) / FILES[k]
        if f.exists():
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, t)
            placed[k] = str(t)
    if (p / "vm.json").exists():
        st["recipe"] = r["id"]
        (p / "vm.json").write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    nxt = "vm check" if same else f"vm shots {p.name} --from-recipe {r['id']}  (retime sheet), then write source/shots.js"
    return {"recipe": r["id"], "remake": bool(same), "placed": placed, "next": nxt}

"""One preset library for Claude Editor: every effect, sound, grade, transition, style and recipe the editor can use,
in one index searched by keyword (SQLite FTS5) and by meaning (the Pocket's e5 ONNX vectors), merged by rank.

Sources (kind):
  effect        scripts/fx_pass.py presets (41: hook, glitch, camera, distort, light, texture, colour, time, cut transitions)
  sound         assets/sfx-hook (59 hook sounds with sync points)                                     + OpenFilm's 5,400 sfx (live)
  grade         Film-Luts: 296 film-emulation LUTs (vm grade <in> --lut <id>)
  transition    gl-transitions: GLSL transitions (MIT ones), for WebGL pages / the OpenFilm layer
  ae-effect     EffectCraft: 308 After-Effects-equivalent effects (runs through effectcraft-cli when allowed)
  node          framefields: 75 WebGPU effect/audio nodes (Apache-2.0)
  recipe        whole-film presets (recipes/<id>/recipe.json)
  + the Pocket (10,625 styles, treatments, moves, moments, templates, prompts) merged into every search.

    python vm_presets.py build        python vm_presets.py search "ominous glitch hook"     python vm_presets.py show grade:print/kodak_2393_cuspclip
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
SKILL = S.parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402


def research() -> Path:
    return vm_env.workbench() / "research"


def store() -> Path:
    d = vm_env.workbench() / "presets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _rows():
    rows = []
    # effects (fx_pass)
    fx = SKILL / "engines" / "fx_presets.json"
    for r in json.loads(fx.read_text(encoding="utf-8")) if fx.exists() else []:
        rows.append(dict(id=f"effect:{r['id']}", kind="effect", name=r["id"].replace("_", " "), engine="fx_pass",
                         summary=f"{r['job']} Family {r['family']}. Sound: {', '.join(s['id'] for s in r['sfx'])}. Avoid: {r['avoid']}",
                         tags=r["family"], use=f"storyboard/fx_cues.json: {{\"t\": <s>, \"fx\": \"{r['id']}\"}} then vm fx apply"))
    # hook sounds
    man = SKILL / "assets" / "sfx-hook" / "manifest.json"
    for s in json.loads(man.read_text(encoding="utf-8")) if man.exists() else []:
        rows.append(dict(id=f"sound:{s['id']}", kind="sound", name=s["id"], engine="sfx-hook",
                         summary=f"{s['description']} Use for: {', '.join(s.get('use_for', []))}. {s['duration']:.2f}s, sync at {s['sync_at']}s.",
                         tags=" ".join([s.get("category", "")] + s.get("tags", [])), use=f"fx cue sfx: {{\"id\": \"{s['id']}\", \"at\": \"start|peak|end\"}}"))
    # LUTs
    fl = research() / "YahiaAngelo_Film-Luts" / "film_luts.json"
    if fl.exists():
        for l in json.loads(fl.read_text(encoding="utf-8"))["filmLUTs"]:
            rel = l["lut_file"].replace("luts/", "").replace(".cube", "")
            rows.append(dict(id=f"grade:{rel}", kind="grade", name=l["name"], engine="Film-Luts",
                             summary=f"Film-emulation colour grade: {l['name']} ({l['category']}). Cinematic film look LUT.",
                             tags=f"grade lut film color {l['category']}", use=f"vm grade <in.mp4> --lut {rel} -o <out.mp4> [--mix 0.7]"))
    # gl-transitions
    gd = research() / "gl-transitions" / "transitions"
    for f in sorted(gd.glob("*.glsl")) if gd.exists() else []:
        head = f.read_text(encoding="utf-8", errors="replace")[:600]
        lic = (re.search(r"License:\s*(.+)", head) or [None, "?"])[1].strip()
        desc = (re.search(r"Description:\s*(.+)", head) or [None, ""])[1].strip()
        tags = (re.search(r"Tags:\s*(.+)", head) or [None, ""])[1].strip()
        rows.append(dict(id=f"transition:{f.stem}", kind="transition", name=f.stem, engine=f"gl-transitions ({lic})",
                         summary=desc or f"GLSL transition {f.stem}", tags=f"transition glsl {tags}",
                         use=f"WebGL page transition (research/gl-transitions/transitions/{f.name}); licence {lic}"))
    # EffectCraft AE-equivalent effects
    ed = research() / "storytold_effectcraft" / "docs" / "effects.md"
    if ed.exists():
        cat = ""
        for line in ed.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                cat = line[3:].strip()
            m = re.match(r"\|\s*([^|]+?)\s*\|\s*`(ec\.[^`]+)`\s*\|\s*(\d+)", line)
            if m:
                rows.append(dict(id=f"ae-effect:{m[2]}", kind="ae-effect", name=m[1], engine="EffectCraft (AE-equivalent)",
                                 summary=f"After Effects-equivalent effect '{m[1]}' ({cat}), {m[3]} parameters.",
                                 tags=f"after effects ae {cat}", use=f"effectcraft-cli command_run effect.apply {m[2]} (needs EffectCraft running)"))
    # framefields nodes
    nd = research() / "gatewai_framefields" / "nodes"
    for d in sorted(nd.iterdir()) if nd.exists() else []:
        pj = d / "package.json"
        if not pj.exists():
            continue
        meta = json.loads(pj.read_text(encoding="utf-8")).get("framefields", {})
        doc = ""
        for ts in list((d / "src").rglob("*.ts"))[:6]:
            m = re.search(r"/\*\*\s*\n?\s*\*?\s*(.+?)\n", ts.read_text(encoding="utf-8", errors="replace"))
            if m and len(m[1]) > 12:
                doc = m[1].strip(" *")
                break
        rows.append(dict(id=f"node:{d.name}", kind="node", name=meta.get("type", d.name), engine="framefields (WebGPU)",
                         summary=doc or f"{meta.get('kind', '')} node {d.name}", tags=f"{meta.get('kind', '')} webgpu node",
                         use=f"port from research/gatewai_framefields/nodes/{d.name}"))
    # recipes
    rd = SKILL / "recipes"
    for f in sorted(rd.glob("*/recipe.json")) if rd.exists() else []:
        r = json.loads(f.read_text(encoding="utf-8"))
        rows.append(dict(id=f"recipe:{r['id']}", kind="recipe", name=r.get("title", r["id"]), engine="recipes",
                         summary=r.get("about", ""), tags=" ".join(r.get("tags", [])), use=f"vm recipe use {r['id']} <film>"))
    return rows


def build() -> int:
    rows = _rows()
    db = store() / "presets.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE items (n INTEGER PRIMARY KEY, id TEXT, kind TEXT, name TEXT, engine TEXT, summary TEXT, tags TEXT, use TEXT)")
    con.execute("CREATE VIRTUAL TABLE fts USING fts5(name, summary, tags, kind, tokenize='unicode61 remove_diacritics 2')")
    for n, r in enumerate(rows):
        con.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?)", (n, r["id"], r["kind"], r["name"], r["engine"], r["summary"], r["tags"], r["use"]))
        con.execute("INSERT INTO fts(rowid, name, summary, tags, kind) VALUES (?,?,?,?,?)", (n, r["name"], r["summary"], r["tags"], r["kind"]))
    con.commit()
    con.close()
    try:
        import numpy as np
        import pocket
        emb = pocket.Embedder()
        v = emb.embed([f"{r['name']}. {r['kind']}. {r['summary']} {r['tags']}" for r in rows], "passage: ")
        np.save(store() / "vectors.npy", v)
    except Exception as ex:  # keyword search still works
        print(f"(vectors skipped: {ex})", file=sys.stderr)
    return len(rows)


def _fts(q):
    toks = [t for t in re.findall(r"[\w]+", q.lower()) if len(t) > 1]
    return " OR ".join(f'"{t}"*' for t in toks)


def search(q: str, k: int = 12, kinds: set | None = None, pocket_too: bool = True) -> list[dict]:
    db = store() / "presets.db"
    if not db.exists():
        build()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    ranks: dict[str, float] = {}
    rowmap: dict[str, dict] = {}
    fq = _fts(q)
    if fq:
        for i, r in enumerate(con.execute("SELECT items.* FROM fts JOIN items ON items.n = fts.rowid WHERE fts MATCH ? ORDER BY bm25(fts, 5, 2, 3, 1) LIMIT 300", (fq,))):
            if kinds and r["kind"] not in kinds:
                continue
            ranks[r["id"]] = ranks.get(r["id"], 0) + 1 / (60 + i)
            rowmap[r["id"]] = dict(r)
    vp = store() / "vectors.npy"
    if vp.exists():
        try:
            import numpy as np
            import pocket
            vecs = np.load(vp)
            pocket._EMB = getattr(pocket, "_EMB", None) or pocket.Embedder()
            qv = pocket._EMB.embed([q], "query: ")[0]
            i = 0
            for n in np.argsort(-(vecs @ qv))[:300]:
                r = con.execute("SELECT * FROM items WHERE n=?", (int(n),)).fetchone()
                if r is None or (kinds and r["kind"] not in kinds):
                    continue
                ranks[r["id"]] = ranks.get(r["id"], 0) + 1 / (60 + i)
                rowmap[r["id"]] = dict(r)
                i += 1
        except Exception as ex:
            print(f"(meaning search unavailable: {ex})", file=sys.stderr)
    if pocket_too and (not kinds or kinds & {"style", "treatment", "move", "moment", "template", "prompt", "transition", "effect", "pocket"}):
        try:
            import pocket
            for i, r in enumerate(pocket.search(q, k=k)):
                pid = f"pocket:{r.get('id')}"
                ranks[pid] = ranks.get(pid, 0) + 1 / (60 + i)
                rowmap[pid] = dict(id=pid, kind=r.get("kind", "pocket"), name=r.get("name", ""), engine=r.get("engine", "pocket"),
                                   summary=(r.get("summary") or "")[:300], tags=r.get("tags", ""), use=f"pocket.py show {r.get('id')}")
        except Exception as ex:
            print(f"(pocket unavailable: {ex})", file=sys.stderr)
    top = sorted(ranks.items(), key=lambda x: -x[1])[:k]
    res = [{k_: v for k_, v in rowmap[i].items() if k_ != "n"} for i, _ in top]
    con.close()
    return res


def show(pid: str) -> dict:
    con = sqlite3.connect(store() / "presets.db")
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM items WHERE id=?", (pid,)).fetchone()
    return dict(r) if r else {"error": f"no preset {pid}"}


def kinds() -> dict:
    con = sqlite3.connect(store() / "presets.db")
    return {k: n for k, n in con.execute("SELECT kind, COUNT(*) FROM items GROUP BY kind")}


def lut_path(lut: str) -> Path:
    lut = lut.replace("grade:", "")
    p = research() / "YahiaAngelo_Film-Luts" / "luts" / f"{lut}.cube"
    if not p.exists():
        hits = list((research() / "YahiaAngelo_Film-Luts" / "luts").rglob(f"*{lut}*.cube"))
        if not hits:
            raise SystemExit(f"no LUT '{lut}' (vm presets search \"<look>\" --kind grade)")
        p = hits[0]
    return p


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        print(build(), "presets indexed;", kinds())
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        for r in search(" ".join(sys.argv[2:])):
            print(f"{r['kind']:11s} {r['id'][:44]:44s} {r['summary'][:80]}")
    elif len(sys.argv) > 2 and sys.argv[1] == "show":
        print(json.dumps(show(sys.argv[2]), indent=1))
    else:
        print(__doc__)

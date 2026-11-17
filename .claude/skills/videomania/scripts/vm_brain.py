"""The director's brain v2: an Obsidian-compatible vault of linked notes + a hybrid index (keywords, meaning, links).

    vm brain sync              rebuild the vault from the skill and the film ledger, then index it
    vm brain ask "how do I open a tech reel so people don't skip"
    vm brain log <film> [--verdict "user's words"] [--good|--bad]   after a film: ledger + film note + resync
    vm brain vault             where it is (open the folder in Obsidian to see the graph)

Vault: <workbench>/brain/vault/
  index.md                     map of content
  notes/   the user's own notes, verbatim, with the rule each became (house-rules.md)
  lessons/ L-1 ... (brain/lessons.md), each with evidence and confidence
  films/   every film in the ledger: features, verdict, what it used
  effects/ sounds/ recipes/    the editor's presets, linked to each other
  doctrine/                    every section of the skill's references, so a question lands on the right page
Search = SQLite FTS5 + e5 vectors (the Pocket's local ONNX model) merged by rank, then one hop along [[links]].
Why own it (not claude-mem): domain notes for directing, no second agent spending tokens, no background vector
server on a 7 GB machine, plain markdown the user can read and edit.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
SKILL = S.parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402


def vault() -> Path:
    v = vm_env.workbench() / "brain" / "vault"
    v.mkdir(parents=True, exist_ok=True)
    return v


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70] or "note"


def note(rel: str, title: str, body: str, tags: list[str], links: list[str]):
    p = vault() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    fm = "---\n" + f"title: \"{title.replace(chr(34), '')}\"\n" + f"tags: [{', '.join(tags)}]\n" + "---\n\n"
    lk = ("\n\nLinks: " + " · ".join(f"[[{l}]]" for l in links)) if links else ""
    p.write_text(fm + f"# {title}\n\n" + body.strip() + lk + "\n", encoding="utf-8")


def sync() -> dict:
    v = vault()
    counts = {}
    # lessons
    for line in (SKILL / "brain" / "lessons.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \[(L-\d+)\]\s*(.+)", line)
        if m:
            refs = re.findall(r"references/([\w-]+)\.md", m[2])
            note(f"lessons/{m[1]}.md", f"{m[1]} {m[2][:70]}", m[2], ["lesson"], [f"doctrine/{r}" for r in refs] + ["index"])
            counts["lessons"] = counts.get("lessons", 0) + 1
    # the user's notes (house rules table)
    for line in (SKILL / "references" / "house-rules.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 3 and re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            date, said, rule = cells[0], cells[1], cells[2]
            enforced = cells[3] if len(cells) > 3 else ""
            refs = re.findall(r"references/([\w-]+)\.md|`([\w-]+)\.md`", enforced + rule)
            refs = [a or b for a, b in refs]
            name = f"{date}-{slug(said[:40])}"
            note(f"notes/{name}.md", f"{date}: {said[:60]}", f"**The user said:** {said}\n\n**Rule now:** {rule}\n\n**Enforced by:** {enforced}",
                 ["user-note", date[:7]], [f"doctrine/{r}" for r in refs if r] + ["index"])
            counts["notes"] = counts.get("notes", 0) + 1
    # films (ledger)
    led = vm_env.workbench() / "brain" / "ledger.jsonl"
    for line in led.read_text(encoding="utf-8").splitlines() if led.exists() else []:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        f = r.get("features", {})
        body = (f"Date {r.get('date')}. Verdict: {r.get('verdict') or '-'}. Score: {r.get('score') or '-'}.\n\n"
                f"Worlds: {', '.join(f.get('worlds', []))}. Hook: {f.get('hook')}. Signature: {f.get('signature')}. "
                f"Transitions: {', '.join(f.get('transitions', []))}. Structure: {f.get('structure')}.\n\nMoves: "
                + ", ".join(f"{k} x{v}" for k, v in (f.get("moves") or {}).items()))
        rec = r["film"].split("-v")[0]
        note(f"films/{r['film']}.md", f"Film: {r['film']}", body, ["film"], [f"recipes/{rec}"] + ["index"])
        counts["films"] = counts.get("films", 0) + 1
    # effects and sounds
    fx = json.loads((SKILL / "engines" / "fx_presets.json").read_text(encoding="utf-8"))
    for e in fx:
        note(f"effects/{e['id']}.md", f"Effect: {e['id']}", f"{e['job']}\n\nFamily: {e['family']}. Length {e['dur']} s ({e['centre']}). Avoid: {e['avoid'] or '-'}.",
             ["effect", e["family"]], [f"sounds/{s['id']}" for s in e["sfx"]] + ["doctrine/editor-effects-and-hook-sound"])
    counts["effects"] = len(fx)
    for s in json.loads((SKILL / "assets" / "sfx-hook" / "manifest.json").read_text(encoding="utf-8")):
        note(f"sounds/{s['id']}.md", f"Sound: {s['id']}", f"{s['description']}\n\nUse for: {', '.join(s.get('use_for', []))}. Avoid: {', '.join(s.get('avoid_for', []))}. "
             f"{s['duration']} s, sync at {s['sync_at']} s, {s.get('lufs')} LUFS. Source: {s['source']} ({s['license']}).", ["sound", s.get("category", "")], ["doctrine/editor-effects-and-hook-sound"])
        counts["sounds"] = counts.get("sounds", 0) + 1
    # recipes
    for f in (SKILL / "recipes").glob("*/recipe.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        note(f"recipes/{r['id']}.md", f"Recipe: {r['title']}", f"{r['about']}\n\nDuration {r.get('duration')} s, format {r.get('format')}. Use: `vm recipe use {r['id']} <film>`.",
             ["recipe"] + r.get("tags", [])[:6], ["index"])
        counts["recipes"] = counts.get("recipes", 0) + 1
    # doctrine: every section of every reference
    n = 0
    for ref in sorted((SKILL / "references").glob("*.md")):
        txt = ref.read_text(encoding="utf-8")
        title = (re.search(r"^# (.+)", txt, re.M) or [None, ref.stem])[1]
        secs = re.split(r"\n(?=## )", txt)
        body = f"Source: `references/{ref.name}`\n\n" + "\n\n".join(f"- {(re.match(r'## (.+)', s) or [None, 'intro'])[1]}" for s in secs)
        note(f"doctrine/{ref.stem}.md", title, body + "\n\n" + txt[:6000], ["doctrine"], ["index"])
        n += 1
    counts["doctrine"] = n
    # map of content
    groups = {}
    for p in sorted(v.rglob("*.md")):
        rel = p.relative_to(v).as_posix()[:-3]
        if rel != "index":
            groups.setdefault(rel.split("/")[0], []).append(rel)
    body = "The director's memory: open this folder in Obsidian to see the graph.\n\n" + "\n".join(
        f"## {g}\n" + " · ".join(f"[[{x}]]" for x in xs) + "\n" for g, xs in groups.items())
    note("index.md", "Director brain", body, ["index"], [])
    counts["indexed"] = index()
    return counts


def _notes():
    v = vault()
    rows = []
    for p in sorted(v.rglob("*.md")):
        txt = p.read_text(encoding="utf-8")
        rel = p.relative_to(v).as_posix()[:-3]
        title = (re.search(r'^title: "(.*)"', txt, re.M) or [None, rel])[1]
        links = sorted(set(re.findall(r"\[\[([^\]|#]+)", txt)))
        body = re.sub(r"^---.*?---\n", "", txt, flags=re.S)
        rows.append(dict(id=rel, title=title, body=body, links=links))
    return rows


def store() -> Path:
    d = vm_env.workbench() / "brain" / "index"
    d.mkdir(parents=True, exist_ok=True)
    return d


def index() -> int:
    rows = _notes()
    db = store() / "brain.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE notes (n INTEGER PRIMARY KEY, id TEXT, title TEXT, body TEXT, links TEXT)")
    con.execute("CREATE VIRTUAL TABLE fts USING fts5(title, body, tokenize='unicode61 remove_diacritics 2')")
    for n, r in enumerate(rows):
        con.execute("INSERT INTO notes VALUES (?,?,?,?,?)", (n, r["id"], r["title"], r["body"], json.dumps(r["links"])))
        con.execute("INSERT INTO fts(rowid, title, body) VALUES (?,?,?)", (n, r["title"], r["body"]))
    con.commit()
    con.close()
    try:
        import numpy as np
        import pocket
        e = pocket.Embedder()
        np.save(store() / "vectors.npy", e.embed([f"{r['title']}. {r['body'][:1500]}" for r in rows], "passage: "))
    except Exception as ex:
        print(f"(vectors skipped: {ex})", file=sys.stderr)
    return len(rows)


def ask(q: str, k: int = 8) -> list[dict]:
    db = store() / "brain.db"
    if not db.exists():
        sync()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    ranks: dict[int, float] = {}
    toks = [t for t in re.findall(r"\w+", q.lower()) if len(t) > 2]
    if toks:
        fq = " OR ".join(f'"{t}"*' for t in toks)
        for i, r in enumerate(con.execute("SELECT rowid FROM fts WHERE fts MATCH ? ORDER BY bm25(fts, 4, 1) LIMIT 200", (fq,))):
            ranks[r[0]] = ranks.get(r[0], 0) + 1 / (60 + i)
    vp = store() / "vectors.npy"
    if vp.exists():
        try:
            import numpy as np
            import pocket
            vecs = np.load(vp)
            pocket._EMB = getattr(pocket, "_EMB", None) or pocket.Embedder()
            qv = pocket._EMB.embed([q], "query: ")[0]
            for i, n in enumerate(np.argsort(-(vecs @ qv))[:200]):
                ranks[int(n)] = ranks.get(int(n), 0) + 1.2 / (60 + i)      # meaning weighs a little more
        except Exception as ex:
            print(f"(meaning search unavailable: {ex})", file=sys.stderr)
    # one hop along links: a strong note lends a little score to what it links to
    byid = {r["id"]: r["n"] for r in con.execute("SELECT n, id FROM notes")}
    top = sorted(ranks.items(), key=lambda x: -x[1])[:k]
    for n, sc in top:
        links = json.loads(con.execute("SELECT links FROM notes WHERE n=?", (n,)).fetchone()[0])
        for l in links:
            if l in byid and l != "index":
                ranks[byid[l]] = ranks.get(byid[l], 0) + sc * 0.15
    out = []
    for n, sc in sorted(ranks.items(), key=lambda x: -x[1])[:k]:
        r = con.execute("SELECT * FROM notes WHERE n=?", (n,)).fetchone()
        body = re.sub(r"\s+", " ", r["body"])
        hit = next((m.start() for t in toks for m in [re.search(re.escape(t), body.lower())] if m), 0)
        out.append({"note": r["id"], "title": r["title"], "snippet": body[max(0, hit - 120): hit + 420],
                    "links": json.loads(r["links"])[:8], "file": str(vault() / (r["id"] + ".md")), "score": round(sc, 4)})
    con.close()
    return out


def log_film(p: Path, verdict=None, good=False, bad=False) -> dict:
    shots = p / "source" / "shots.js"
    cmd = [str(vm_env.venv_python()), str(S / "brain.py"), "log", str(shots), "--film", p.name]
    if verdict:
        cmd += ["--verdict", verdict]
    if good:
        cmd += ["--good"]
    if bad:
        cmd += ["--bad"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    st = json.loads((p / "vm.json").read_text(encoding="utf-8")) if (p / "vm.json").exists() else {}
    extra = f"\n\nProject: `{p}`. Recipe: {st.get('recipe') or '-'}. Gates: {json.dumps(st.get('stages', {}).get('check', {}).get('gates', {}))[:600]}"
    counts = sync()
    fn = vault() / "films" / f"{p.name}.md"
    if fn.exists():
        fn.write_text(fn.read_text(encoding="utf-8").rstrip() + extra + "\n", encoding="utf-8")
        index()
    return {"film": p.name, "ledger": r.stdout.strip()[-400:] or r.stderr[-400:], "vault": counts}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        print(sync())
    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        for r in ask(" ".join(sys.argv[2:])):
            print(f"{r['score']:.4f}  {r['note']:45s} {r['snippet'][:110]}")
    else:
        print(__doc__)

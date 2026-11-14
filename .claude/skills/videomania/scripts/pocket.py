"""The Pocket: one searchable index of everything Video Mania can make.

    python pocket.py build [--no-vectors]        index every engine (styles, treatments, transitions, effects,
                                                 text animations, templates, moments, prompts, skills, formats)
    python pocket.py search "<words>" [-k 10] [--kind style,treatment] [--engine lemo-opuscar] [--json]
    python pocket.py menu "<brief>" [--has footage,voiceover,topic,product] [--json]
                                                 the grouped menu to show a user before building
    python pocket.py show <id>                   one row in full, with the files to read before using it
    python pocket.py pick <id> [<id> ...]        record what the user chose (picked rows rank higher later)
    python pocket.py stats                       rows per kind and per engine

Search is keyword (SQLite FTS5) merged with meaning (multilingual-e5-small sentence vectors, run locally with
ONNX) by reciprocal rank, so "sad goodbye, hand-made" finds a watercolour farewell with no word in common, and
Chinese style notes are found from English words. Without the model it falls back to keywords alone.
The index lives in <workbench>/pocket/ and is rebuilt from the engines, never edited by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

import vm_env
import vm_engines

MODEL_REPO = "Xenova/multilingual-e5-small"
MODEL_FILES = ("onnx/model_quantized.onnx", "tokenizer.json")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "target", "vendor", "__pycache__", ".venv", "tests", "test"}


def pocket_dir() -> Path:
    d = vm_env.workbench() / "pocket"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ----------------------------------------------------------------------------------------------- rows

def row(rid, kind, name, engine, summary, tags=(), path="", preview="", read=(), extra=""):
    summary = re.sub(r"\s+", " ", str(summary or "")).strip()
    return {
        "id": rid, "kind": kind, "name": str(name).strip(), "engine": engine,
        "summary": summary[:600], "tags": ", ".join(dict.fromkeys(str(t).strip() for t in tags if str(t).strip())),
        "path": str(path).replace("\\", "/"), "preview": str(preview).replace("\\", "/"),
        "read": json.dumps(list(read), ensure_ascii=False), "extra": extra[:1500],
    }


def read_text(p: Path, limit: int = 200_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def first_para(md: str) -> tuple[str, str]:
    """(title, first paragraph) of a Markdown file."""
    title, para = "", []
    for line in md.splitlines():
        s = line.strip()
        if not title and s.startswith("#"):
            title = s.lstrip("#").strip()
            continue
        if title:
            if not s:
                if para:
                    break
                continue
            if s.startswith(("#", "|", "```", "<", "[", "---")) and not para:
                continue
            if s.startswith("#"):
                break
            para.append(s.lstrip("> ").strip())
    return title, " ".join(para)


def frontmatter(md: str) -> dict:
    if not md.startswith("---"):
        return {}
    end = md.find("\n---", 3)
    if end < 0:
        return {}
    out, key = {}, None
    for line in md[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            v = m.group(2).strip()
            out[key] = "" if v in (">", "|", ">-", "|-") else v.strip("'\"")
        elif key and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base)).replace("\\", "/")
    except ValueError:
        return str(p)


# ------------------------------------------------------------------------------------------ extractors
# Each takes (engine dict, engine folder) and yields rows. A missing file yields nothing: an engine that
# changes its layout loses rows, never breaks the build.

def x_lemo(e, d):
    for sj in sorted((d / "styles").glob("*/style.json")):
        try:
            s = json.loads(read_text(sj))
        except json.JSONDecodeError:
            continue
        slug = s.get("slug") or sj.parent.name
        poster = sj.parent / "poster.jpg"
        yield row(f"lemo/{slug}", "style", s.get("en") or slug, e["id"],
                  f"{s.get('line', '')} Demo film: {s.get('film', '')}.",
                  [s.get("category_en", ""), *s.get("uses", []), s.get("cn", ""), "film style"],
                  rel(sj.parent / "STYLE.md", d), poster if poster.exists() else "",
                  ["DIRECTOR.md", "TECHNIQUE.md", f"styles/{slug}/STYLE.md", f"styles/{slug}/DEMO.md"])


def x_huashu(e, d):
    for folder, kind in (("风格配方", "style"), ("动画语法", "grammar")):
        for f in sorted((d / "references" / folder).glob("*.md")):
            title, para = first_para(read_text(f))
            stem = f.stem
            en = re.sub(r"^[a-z]?\d+_", "", stem).replace("_", " ")
            k = "grammar" if (kind == "grammar" or re.match(r"^[ty]\d", stem)) else "style"
            yield row(f"huashu/{stem}", k, f"{en} ({title})" if title else en, e["id"], para or title,
                      [en, "painting" if k == "style" else "explainer grammar", "art in motion"],
                      rel(f, d), "", ["SKILL.md", rel(f, d)])


def x_drawing(e, d):
    md = read_text(d / "docs" / "STYLES.md")
    for m in re.finditer(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*`(lib/[\w.]+)`[^|]*\|\s*(.+?)\s*\|?\s*$", md, re.M):
        name, mod, what = m.group(1), m.group(2), m.group(3)
        slug = Path(mod).stem
        yield row(f"drawing/{slug}", "style", name, e["id"], what,
                  ["drawing", "stroke by stroke", "no image model", slug], mod, "",
                  ["SKILL.md", "docs/PRINCIPLES.md", mod])


def x_openfilm(e, d):
    lib = d / "packages" / "openfilm" / "library"
    files = [lib / "index.json", *sorted((lib / "catalogs").glob("*.json")), lib / "audio.json", lib / "stickers.json"]
    for f in files:
        try:
            items = json.loads(read_text(f, 80_000_000)).get("items", [])
        except (json.JSONDecodeError, AttributeError):
            continue
        for it in items:
            name = it.get("name")
            name = name.get("en") if isinstance(name, dict) else name
            about = it.get("about")
            about = about.get("en") if isinstance(about, dict) else about
            cat = it.get("cat") or it["id"].split("/")[0]
            if cat in ("music", "sound") and not about:
                secs = round((it.get("durationMs") or 0) / 1000)
                about = f"{'Music' if cat == 'music' else 'Sound effect'}: {name}, {secs} s" + \
                        (f", {it['bpm']} bpm" if it.get("bpm") else "") + (f", energy {it['energy']} of 5" if it.get("energy") else "") + "."
            elif cat == "sticker" and not about:
                about = f"Sticker: {name}."
            preview = it.get("poster") or it.get("cover") or ""
            yield row(f"openfilm/{it['id']}", cat, name or it["id"], e["id"], about or "",
                      [*(it.get("tags") or []), it.get("group", ""), it.get("kind", ""), cat],
                      f"packages/openfilm/library/{it['id']}",
                      f"packages/openfilm/library/{preview}" if preview else "",
                      ["packages/openfilm/manual/media", "openfilm get (CLI)"])


def x_motionmaxxing(e, d):
    f = d / "library" / "moments.jsonl"
    for line in read_text(f, 5_000_000).splitlines():
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        if m.get("_meta") or not m.get("id"):
            continue
        rule = m.get("rule") or m.get("why") or ""
        mech = m.get("mechanic") or m["id"]
        name = (", ".join(map(str, mech)) if isinstance(mech, list) else str(mech)).replace("-", " ")

        def lst(v):
            return v if isinstance(v, list) else ([v] if v else [])
        yield row(f"moment/{m['id']}", "moment", name, e["id"], rule,
                  [str(m.get("beat", "")), *map(str, lst(m.get("content"))), *map(str, lst(m.get("tags"))), str(m.get("src", ""))],
                  "library/moments.jsonl", "", ["SKILL.md", "references/"], extra=json.dumps(m, ensure_ascii=False))


def x_awesome(e, d):
    try:
        vids = json.loads(read_text(d / "data" / "videos.json", 20_000_000))
    except json.JSONDecodeError:
        return
    for v in vids:
        prompt = v.get("prompt") or ""
        if len(prompt) < 40:
            continue
        yield row(f"prompt/{v['slug']}", "prompt", f"{v.get('category', 'video')} by {v.get('author', '?')}",
                  e["id"], prompt, [v.get("category", ""), *(v.get("tech_tags") or [])],
                  f"prompts/{v['slug']}.md", v.get("poster_url", ""), [f"prompts/{v['slug']}.md"])


def x_hypit(e, d):
    base = d / "skills" / "hypit" / "references" / "playbooks"
    for sub, kind in (("formats", "format"), ("craft", "craft")):
        for f in sorted((base / sub).glob("*.md")):
            title, para = first_para(read_text(f))
            yield row(f"hypit/{sub}/{f.stem}", kind, title or f.stem, e["id"], para,
                      [f.stem.replace("-", " "), kind], rel(f, d), "",
                      ["skills/hypit/SKILL.md", rel(f, d)])


def x_onetake(e, d):
    try:
        looks = json.loads(read_text(d / "looks" / "looks.json")).get("looks", {})
    except json.JSONDecodeError:
        looks = {}
    for name, lk in looks.items():
        yield row(f"onetake/look/{name}", "look", f"{name} look", e["id"], lk.get("mood", ""),
                  ["one take", "palette", "look", name], "looks/looks.json", "", ["SKILL.md", "looks/looks.json"])
    for c in sorted((d / "cases").glob("*")):
        if c.is_dir():
            title, para = first_para(read_text(next(iter(c.glob("*.md")), c / "none")))
            yield row(f"onetake/case/{c.name}", "example", title or c.name, e["id"], para or "A finished one-take film to study.",
                      ["one take", "launch film", "case"], rel(c, d), "", ["SKILL.md", rel(c, d)])


def x_pixel_studio(e, d):
    src = read_text(d / "src" / "pixel.js")
    i = src.find("PX.palettes")
    for name in re.findall(r"^\s{4}(\w+):\s*\[", src[i:i + 6000], re.M) if i >= 0 else []:
        yield row(f"pixel/palette/{name}", "palette", f"{name} pixel palette", e["id"],
                  f"12-colour pixel-art palette '{name}': an 8-step ramp plus a 4-step accent; swapping it recolours the whole scene.",
                  ["pixel", "palette", name], "src/pixel.js", "", ["skill/SKILL.md"])
    for f in sorted((d / "scenes").glob("*.js")):
        head = read_text(f, 1500)
        m = re.search(r"//\s*(.+)", head)
        gif = d / "media" / f"{f.stem}.gif"
        yield row(f"pixel/scene/{f.stem}", "example", f"{f.stem} pixel scene", e["id"],
                  m.group(1) if m else "A pixel-art scene with precomputed physics and chiptune sound.",
                  ["pixel", "scene", "example"], rel(f, d), gif if gif.exists() else "", ["skill/SKILL.md", rel(f, d)])


def x_raea(e, d):
    base = d / "sdk" / "guides" / "craft"
    for sub, kind in (("modes", "format"), ("verbs", "fix-move"), ("motion", "guide"), ("bevy", "guide")):
        for f in sorted((base / sub).glob("*.md")):
            title, para = first_para(read_text(f))
            yield row(f"raea/{sub}/{f.stem}", kind, title or f.stem, e["id"], para,
                      [sub, f.stem, "3d" if sub == "bevy" else ""], rel(f, d), "", [rel(f, d)])


def x_cooked(e, d):
    for f in sorted((d / "plugins" / "ai-editor" / "presets" / "captions").glob("*.json")):
        try:
            c = json.loads(read_text(f))
        except json.JSONDecodeError:
            continue
        yield row(f"cooked/captions/{f.stem}", "caption-style", f"{f.stem} captions", e["id"],
                  f"{c.get('style', f.stem)} captions: {c.get('words_per_caption', '?')} words per caption, weight {c.get('weight', '?')}, font like {c.get('font_match', '?')}.",
                  ["captions", "subtitles", f.stem], rel(f, d), "", ["plugins/ai-editor/skills/style-edit/SKILL.md"])


def x_skills(e, d):
    """Every SKILL.md in the engine: name + description from its front matter."""
    seen = 0
    stack = [d]
    while stack and seen < 80:
        cur = stack.pop()
        try:
            entries = sorted(cur.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_dir():
                if p.name not in SKIP_DIRS and not p.name.startswith(".") and len(p.relative_to(d).parts) < 6:
                    stack.append(p)
            elif p.name == "SKILL.md":
                md = read_text(p, 20_000)
                fm = frontmatter(md)
                title, para = first_para(md[md.find("\n---", 3) + 4:] if fm else md)
                name = fm.get("title") or fm.get("name") or title or p.parent.name
                desc = fm.get("description") or para
                if not desc:
                    continue
                seen += 1
                yield row(f"skill/{e['id']}/{rel(p.parent, d) or 'root'}", "skill", name, e["id"], desc,
                          [*e["lanes"], "skill"], rel(p, d), "", [rel(p, d)])


def x_engine(e, d):
    title, para = first_para(read_text(d / "README.md", 30_000))
    yield row(f"engine/{e['id']}", "engine", e["id"], e["id"],
              f"{para} Output: {e.get('output', '?')}. Needs: {'; '.join(e.get('needs', [])) or 'nothing extra'}.",
              [*e["lanes"], "engine"], "README.md", "", e.get("entry", []))


EXTRACTORS = {
    "lemo-opuscar": [x_lemo], "huashu-art-motion": [x_huashu], "claude-drawing-skill": [x_drawing],
    "openfilm": [x_openfilm], "motionmaxxing": [x_motionmaxxing], "awesome-opus5-5-videos": [x_awesome],
    "hypit": [x_hypit], "onetake": [x_onetake], "pixel-studio": [x_pixel_studio], "raea": [x_raea],
    "ai-video-editor-cooked": [x_cooked],
}
NO_SKILL_WALK = {"hyperframes", "OpenMontage", "raea", "openfilm", "awesome-opus5-5-videos"}


def own_rows():
    """Video Mania's own treatments, style cards and templates."""
    sd = vm_env.SKILL_DIR
    try:
        tr = json.loads(read_text(sd / "engines" / "treatments.json")).get("treatments", [])
    except json.JSONDecodeError:
        tr = []
    for t in tr:
        yield row(f"treatment/{t['id']}", "treatment", t["name"], "videomania", t["summary"],
                  [*t.get("tags", []), *("fits " + f for f in t.get("fits", []))], "engines/treatments.json", "",
                  t.get("read", []), extra=json.dumps({"fits": t.get("fits", []), "engines": t.get("engines", [])}))
    try:
        mv = json.loads(read_text(sd / "engines" / "moves.json")).get("moves", [])
    except json.JSONDecodeError:
        mv = []
    for m in mv:
        yield row(f"move/{m['id']}", "move", m["name"], "videomania", f"Use when {m['use_when']}. How: {m['how']}",
                  [*m.get("tags", []), m["kind"] + " move", "move"], "engines/moves.json", "",
                  ["templates/voxel-diorama/README.md", "engines/moves.json"], extra=json.dumps({"kind": m["kind"], "how": m["how"]}))
    for f in sorted((sd / "references" / "styles").glob("*.md")):
        md = read_text(f)
        fm = frontmatter(md)
        title, para = first_para(md[md.find("\n---", 3) + 4:] if fm else md)
        yield row(f"vm/style/{f.stem}", "style", fm.get("name") or title or f.stem, "videomania",
                  fm.get("description") or para, [*(fm.get("tags", "").split(",")), "house style"],
                  f"references/styles/{f.name}", "", [f"references/styles/{f.name}"])
    for t in sorted((sd / "templates").glob("*")):
        if t.is_dir():
            title, para = first_para(read_text(next(iter(t.glob("*.md")), t / "none")))
            yield row(f"vm/template/{t.name}", "template", title or t.name, "videomania",
                      para or f"Video Mania composition template '{t.name}'.", ["template", t.name],
                      f"templates/{t.name}", "", [f"templates/{t.name}"])


def collect() -> list[dict]:
    rows, seen = [], set()
    for e in vm_engines.registry()["engines"]:
        d = vm_engines.engine_dir(e)
        if not d.exists():
            print(f"  {e['id']}: not cloned, skipped")
            continue
        fns = [x_engine, *EXTRACTORS.get(e["id"], [])]
        if e["id"] not in NO_SKILL_WALK:
            fns.append(x_skills)
        n = 0
        for fn in fns:
            try:
                for r in fn(e, d):
                    if r["id"] not in seen and r["name"]:
                        seen.add(r["id"])
                        rows.append(r)
                        n += 1
            except Exception as ex:  # one broken catalog must not stop the build
                print(f"  {e['id']}: {fn.__name__} failed: {type(ex).__name__}: {ex}")
        print(f"  {e['id']}: {n} rows")
    n0 = len(rows)
    for r in own_rows():
        if r["id"] not in seen:
            seen.add(r["id"])
            rows.append(r)
    print(f"  videomania: {len(rows) - n0} rows")
    return rows


# --------------------------------------------------------------------------------------------- vectors

class Embedder:
    def __init__(self):
        import numpy as np
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer
        cache = pocket_dir() / "model"
        try:  # after the first download, never touch the network again
            onnx, tok = (hf_hub_download(MODEL_REPO, f, cache_dir=str(cache), local_files_only=True) for f in MODEL_FILES)
        except Exception:
            onnx, tok = (hf_hub_download(MODEL_REPO, f, cache_dir=str(cache)) for f in MODEL_FILES)
        self.np = np
        self.tok = Tokenizer.from_file(tok)
        self.tok.enable_truncation(max_length=256)
        self.tok.enable_padding(pad_id=1, pad_token="<pad>")
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        self.sess = ort.InferenceSession(onnx, sess_options=so, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def embed(self, texts: list[str], prefix: str, batch: int = 32):
        np = self.np
        out = []
        for i in range(0, len(texts), batch):
            enc = self.tok.encode_batch([prefix + t for t in texts[i:i + batch]])
            ids = np.array([x.ids for x in enc], dtype=np.int64)
            mask = np.array([x.attention_mask for x in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, feed)[0]
            m = mask[..., None].astype(np.float32)
            v = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-6, None)
            v /= np.clip(np.linalg.norm(v, axis=1, keepdims=True), 1e-9, None)
            out.append(v.astype(np.float32))
            if i and i % 640 == 0:
                print(f"    embedded {i} of {len(texts)}")
        return np.concatenate(out) if out else np.zeros((0, 384), dtype=np.float32)


def passage(r: dict) -> str:
    return f"{r['name']}. {r['kind']}. {r['summary']} Tags: {r['tags']}"


# ----------------------------------------------------------------------------------------------- build

def db() -> sqlite3.Connection:
    con = sqlite3.connect(pocket_dir() / "pocket.db")
    con.row_factory = sqlite3.Row
    return con


def cmd_build(a) -> int:
    print("Collecting")
    rows = collect()
    con = db()
    con.executescript("""
        DROP TABLE IF EXISTS items; DROP TABLE IF EXISTS fts;
        CREATE TABLE items (n INTEGER PRIMARY KEY, id TEXT UNIQUE, kind TEXT, name TEXT, engine TEXT, summary TEXT,
                            tags TEXT, path TEXT, preview TEXT, read TEXT, extra TEXT);
        CREATE VIRTUAL TABLE fts USING fts5(name, summary, tags, kind, engine, tokenize='unicode61 remove_diacritics 2');
        CREATE TABLE IF NOT EXISTS picks (id TEXT, at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    for n, r in enumerate(rows):
        con.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (n, r["id"], r["kind"], r["name"], r["engine"], r["summary"], r["tags"], r["path"], r["preview"], r["read"], r["extra"]))
        con.execute("INSERT INTO fts (rowid, name, summary, tags, kind, engine) VALUES (?,?,?,?,?,?)",
                    (n, r["name"], r["summary"], r["tags"], r["kind"], r["engine"]))
    con.commit()
    vec_path = pocket_dir() / "vectors.npy"
    if a.no_vectors:
        vec_path.unlink(missing_ok=True)
        print(f"Indexed {len(rows)} rows (keywords only).")
        return 0
    try:
        print("Embedding (first run downloads the model, about 120 MB)")
        emb = Embedder()
        vecs = emb.embed([passage(r) for r in rows], "passage: ")
        emb.np.save(vec_path, vecs)
        print(f"Indexed {len(rows)} rows with vectors {vecs.shape}.")
    except Exception as ex:
        vec_path.unlink(missing_ok=True)
        print(f"Indexed {len(rows)} rows. Vectors skipped ({type(ex).__name__}: {ex}); search uses keywords only.")
    return 0


# ---------------------------------------------------------------------------------------------- search

STOP = set("a an the of for to in on and or with my me i we it is are be this that make video edit want like please some".split())


def fts_query(q: str) -> str:
    words = [w for w in re.findall(r"[\w一-鿿]+", q.lower()) if w not in STOP and len(w) > 1]
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


def search(q: str, k: int = 10, kinds: set[str] | None = None, engines: set[str] | None = None, pool: int = 400):
    con = db()
    n_items = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    ranks: dict[int, float] = {}

    def allowed(n: int) -> bool:
        if not kinds and not engines:
            return True
        r = con.execute("SELECT kind, engine FROM items WHERE n=?", (n,)).fetchone()
        return (not kinds or r["kind"] in kinds) and (not engines or r["engine"] in engines)

    fq = fts_query(q)
    if fq:
        try:
            hits = [r[0] for r in con.execute(
                "SELECT rowid FROM fts WHERE fts MATCH ? ORDER BY bm25(fts, 6.0, 2.0, 4.0, 3.0, 1.0) LIMIT ?", (fq, pool * 4))]
        except sqlite3.OperationalError:
            hits = []
        for i, n in enumerate(h for h in hits if allowed(h)):
            if i >= pool:
                break
            ranks[n] = ranks.get(n, 0) + 1 / (60 + i)
    vec_path = pocket_dir() / "vectors.npy"
    if vec_path.exists():
        try:
            import numpy as np
            vecs = np.load(vec_path)
            if len(vecs) == n_items:
                global _EMB
                _EMB = globals().get("_EMB") or Embedder()
                qv = _EMB.embed([q], "query: ")[0]
                order = np.argsort(-(vecs @ qv))
                i = 0
                for n in order:
                    n = int(n)
                    if allowed(n):
                        ranks[n] = ranks.get(n, 0) + 1 / (60 + i)
                        i += 1
                        if i >= pool:
                            break
        except Exception as ex:
            print(f"(meaning search unavailable: {type(ex).__name__}: {ex})", file=sys.stderr)
    picked = {r[0]: r[1] for r in con.execute("SELECT id, COUNT(*) FROM picks GROUP BY id")}
    out = []
    for n, score in ranks.items():
        r = dict(con.execute("SELECT * FROM items WHERE n=?", (n,)).fetchone())
        r["score"] = score * (1 + 0.15 * min(picked.get(r["id"], 0), 4))
        out.append(r)
    out.sort(key=lambda r: -r["score"])
    return out[:k]


def diverse(rows: list[dict], k: int, per_engine: int = 2) -> list[dict]:
    out, count = [], {}
    for r in rows:
        if count.get(r["engine"], 0) < per_engine:
            out.append(r)
            count[r["engine"]] = count.get(r["engine"], 0) + 1
        if len(out) >= k:
            break
    return out


def line(r: dict) -> str:
    return f"- **{r['name']}** `{r['id']}` ({r['engine']}): {r['summary'][:190]}"


def cmd_search(a) -> int:
    kinds = set(a.kind.split(",")) if a.kind else None
    engines = set(a.engine.split(",")) if a.engine else None
    rows = search(a.query, a.k, kinds, engines)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"[{r['kind']}] {line(r)[2:]}")
    return 0 if rows else 1


MENU = [
    ("Ways to treat it", {"treatment"}, 5, 5),
    ("Film and art styles", {"style", "look", "grammar"}, 8, 2),
    ("Moves", {"move"}, 6, 6),
    ("Formats", {"format"}, 3, 2),
    ("Transitions", {"transition"}, 4, 4),
    ("Text animations", {"text", "caption-style"}, 4, 3),
    ("Effects and filters", {"effect", "filter", "motion"}, 4, 4),
    ("Templates", {"template"}, 3, 3),
    ("Music and sound", {"music", "sound"}, 4, 4),
    ("Proven moves and prompts to borrow from", {"moment", "prompt"}, 4, 2),
]


def cmd_menu(a) -> int:
    has = {h.strip() for h in (a.has or "").split(",") if h.strip()}
    q = a.brief + (" " + " ".join("fits " + h for h in has) if has else "")
    menu = []
    for title, kinds, k, per in MENU:
        if "treatment" in kinds:
            # treatments are few: show every one that fits what the user gave, best match first
            rows = search(q, 40, kinds)

            def fit(r):
                try:
                    return not has or bool(has & set(json.loads(r["extra"] or "{}").get("fits", [])))
                except json.JSONDecodeError:
                    return True
            rows = ([r for r in rows if fit(r)] or rows)[:8]
        else:
            rows = diverse(search(q, 40, kinds), k, per)
        if rows:
            menu.append({"section": title, "options": rows})
    if a.json:
        print(json.dumps(menu, ensure_ascii=False, indent=1))
        return 0
    print(f"# Menu for: {a.brief}\n")
    for sec in menu:
        print(f"## {sec['section']}")
        for r in sec["options"]:
            print(line(r))
        print()
    print("Show the user 'Ways to treat it' and 'Film and art styles' first (previews: the row's `preview`), ask them to pick,")
    print("then `python pocket.py show <id>` for each pick and read the files it lists before planning.")
    return 0


def cmd_show(a) -> int:
    con = db()
    r = con.execute("SELECT * FROM items WHERE id=?", (a.id,)).fetchone()
    if not r:
        raise SystemExit(f"no row '{a.id}'. Try: python pocket.py search \"...\"")
    r = dict(r)
    base = vm_env.SKILL_DIR if r["engine"] == "videomania" else vm_engines.engine_dir(vm_engines.find(r["engine"]))
    print(f"{r['name']}  [{r['kind']}]  {r['id']}\nengine:  {r['engine']}  ({base})\nsummary: {r['summary']}\ntags:    {r['tags']}")
    if r["path"]:
        print(f"path:    {base / r['path'] if not r['path'].startswith('http') else r['path']}")
    if r["preview"]:
        print(f"preview: {r['preview'] if r['preview'].startswith('http') else base / r['preview']}")
    print("read before using:")
    for p in json.loads(r["read"] or "[]"):
        print(f"  - {p}")
    if r["engine"] != "videomania":
        e = vm_engines.find(r["engine"])
        for n in e.get("needs", []):
            print(f"needs:   {n}")
        print(f"licence: {e['licence']}")
    return 0


def cmd_pick(a) -> int:
    con = db()
    for i in a.ids:
        if not con.execute("SELECT 1 FROM items WHERE id=?", (i,)).fetchone():
            raise SystemExit(f"no row '{i}'")
        con.execute("INSERT INTO picks (id) VALUES (?)", (i,))
    con.commit()
    print(f"recorded {len(a.ids)} pick(s)")
    return 0


def cmd_stats(_) -> int:
    con = db()
    print("By kind")
    for r in con.execute("SELECT kind, COUNT(*) c FROM items GROUP BY kind ORDER BY c DESC"):
        print(f"  {r['kind']:<16} {r['c']}")
    print("By engine")
    for r in con.execute("SELECT engine, COUNT(*) c FROM items GROUP BY engine ORDER BY c DESC"):
        print(f"  {r['engine']:<26} {r['c']}")
    print(f"Total {con.execute('SELECT COUNT(*) FROM items').fetchone()[0]}; vectors: {'yes' if (pocket_dir() / 'vectors.npy').exists() else 'no'}")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("build"); s.add_argument("--no-vectors", action="store_true"); s.set_defaults(fn=cmd_build)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-k", type=int, default=10)
    s.add_argument("--kind"); s.add_argument("--engine"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_search)
    s = sub.add_parser("menu"); s.add_argument("brief"); s.add_argument("--has"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_menu)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("pick"); s.add_argument("ids", nargs="+"); s.set_defaults(fn=cmd_pick)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

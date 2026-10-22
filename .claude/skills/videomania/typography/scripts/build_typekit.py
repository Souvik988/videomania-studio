"""Build the type kit for a HyperFrames composition from the typography config.

Writes into a composition's source folder:
  tk/type-kit.js          the runtime (src/type-kit.js)
  tk/type-kit.config.js   window.TK_CONFIG: resolved roles, the 8 pairings, the 10 presets
  fonts/vm/*              the open-source files the CSS needs (+ OFL texts)
and inlines the @font-face block into index.html between the markers
  /* type-kit:begin */ … /* type-kit:end */   (added before </style> the first time).

Faces resolve per role (audit state on this machine):
  EXACT_AVAILABLE      src: local(<the installed face's names>), url(<fallback file>)   the file is never copied
  OPEN_SOURCE_INSTALLED / FALLBACK_ACTIVE / LICENSE_REQUIRED   src: url(<OFL file>)
Every role family also gets unicode-range faces for Devanagari (Noto Sans Devanagari) and Bengali
(Hind Siliguri), so Hindi / Bengali words in any role render real glyphs, not boxes.

Usage: python -P build_typekit.py --src <composition source dir> [--no-inline]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import typography as T  # noqa: E402

GENERIC = {"impact_hook": "Impact, 'Arial Narrow', sans-serif", "elegant_script": "cursive", "editorial_slab": "serif",
           "clean_caption": "'Helvetica Neue', Arial, sans-serif", "classical_highlight": "Georgia, serif",
           "luxury_serif": "Georgia, serif", "expressive_script": "cursive"}
SAMPLE = "Aa₹"


def web_name(rel: str) -> str:
    return re.sub(r"\[[^\]]*\]", "-VF", Path(rel).name)


def face_keys(key: str):
    """'400' → (400,400,False); '100-900' → (100,900,False); '400-800i' → (400,800,True)."""
    ital = key.endswith("i")
    lo, _, hi = key.rstrip("i").partition("-")
    return int(lo), int(hi or lo), ital


PATCH_SCAN = list(range(0x20, 0x250)) + list(range(0x2000, 0x2070)) + list(range(0x20A0, 0x20D0)) + list(range(0x2190, 0x2200))


def patch_range(system_file: str, fallback_file: Path) -> str:
    """unicode-range of code points the fallback has and the system face lacks."""
    have, fb = T._cmap(str(system_file)), T._cmap(str(fallback_file))
    cps = [c for c in PATCH_SCAN if c in fb and c not in have]
    runs = []
    for c in cps:
        if runs and c == runs[-1][1] + 1:
            runs[-1][1] = c
        else:
            runs.append([c, c])
    return ", ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in runs)


def css_for(res: dict, reg: dict) -> tuple[str, set[str]]:
    out, files = [], set()
    for role, r in res.items():
        spec = reg["roles"][role]
        fam = spec["css_family"]
        fb = spec["fallback"]
        exact = r["state"] == "EXACT_AVAILABLE"
        local_by = {}
        if exact:
            faces = T.find_system(r["requested"], T.scan_system_fonts())
            for f in faces:
                local_by.setdefault((f["weight"], f["italic"]), []).extend(n for n in (f["full"], f["ps"]) if n)
        for key, rel in fb["files"].items():
            lo, hi, ital = face_keys(key)
            files.add(rel)
            locs = []
            if exact:
                for (w, it), names in local_by.items():
                    if it == ital and lo <= w <= hi:
                        locs += [f'local("{n}")' for n in dict.fromkeys(names)]
            fmt = "woff2" if rel.endswith(".woff2") else "truetype"
            src = ", ".join(locs + [f'url("fonts/vm/{web_name(rel)}") format("{fmt}")'])
            wt = f"{lo}" if lo == hi else f"{lo} {hi}"
            out.append(f'@font-face {{ font-family: "{fam}"; font-style: {"italic" if ital else "normal"}; font-weight: {wt}; src: {src}; font-display: block; }}')
            if locs:   # glyphs the system font lacks (Impact has no ₹) come from the fallback, declared later so it wins
                patch = patch_range(r["reference"][0], T.OPEN_SOURCE / rel)
                if patch:
                    out.append(f'@font-face {{ font-family: "{fam}"; font-style: {"italic" if ital else "normal"}; font-weight: {wt}; '
                               f'src: url("fonts/vm/{web_name(rel)}") format("{fmt}"); unicode-range: {patch}; font-display: block; }}')
        for sk in ("devanagari", "bengali"):
            s = reg["script_fallbacks"][sk]
            for key, rel in s["files"].items():
                lo, hi, _ = face_keys(key)
                files.add(rel)
                wt = f"{lo}" if lo == hi else f"{lo} {hi}"
                out.append(f'@font-face {{ font-family: "{fam}"; font-weight: {wt}; src: url("fonts/vm/{web_name(rel)}") format("truetype"); unicode-range: {s["unicode_range"]}; font-display: block; }}')
    for key, spec in reg["script_fallbacks"].items():
        for rel in spec["files"].values():
            files.add(rel)
    return "\n".join(out), files


def config_js(res: dict, reg: dict) -> str:
    roles = {}
    for role, r in res.items():
        spec = reg["roles"][role]
        loads = []
        for key in spec["fallback"]["files"]:
            lo, hi, ital = face_keys(key)
            for w in spec["weights"]:
                if lo <= w <= hi:
                    loads.append(f"{'italic ' if ital else ''}{w}")
        roles[role] = {"css": spec["css_family"], "stack": GENERIC[role], "requested": r["requested"], "resolved": r["resolved"],
                       "state": r["state"], "exact": r["exact"], "category": spec["category"], "weights": spec["weights"],
                       "weight": spec["weights"][0] if len(spec["weights"]) == 1 else 600,
                       "load": sorted(set(loads)), "line_height": spec["line_height"], "tracking_em": spec["tracking_em"],
                       "uppercase": spec["uppercase"], "animations": spec["animations"], "readability": spec["readability"],
                       "sample": SAMPLE}
    cfg = {"roles": roles,
           "pairings": {p["id"]: p for p in T.load("pairing-presets.json")["pairings"]},
           "presets": {p["id"]: p for p in T.load("typography-presets.json")["presets"]}}
    return "// written by typography/scripts/build_typekit.py; edit typography/config/*.json instead\nwindow.TK_CONFIG = " + json.dumps(cfg, ensure_ascii=False, indent=1) + ";\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="composition source folder (holds index.html)")
    ap.add_argument("--no-inline", action="store_true", help="only write tk/type-kit.css; do not edit index.html")
    a = ap.parse_args()
    src = Path(a.src).resolve()
    reg = T.registry()
    res = T.resolve_all()
    css, files = css_for(res, reg)
    (src / "tk").mkdir(parents=True, exist_ok=True)
    (src / "fonts" / "vm").mkdir(parents=True, exist_ok=True)
    shutil.copy2(T.TYPO_DIR / "src" / "type-kit.js", src / "tk" / "type-kit.js")
    (src / "tk" / "type-kit.config.js").write_text(config_js(res, reg), encoding="utf-8")
    block = "/* type-kit:begin (typography/scripts/build_typekit.py) */\n" + css + "\n/* type-kit:end */"
    (src / "tk" / "type-kit.css").write_text(block.replace('url("fonts/vm/', 'url("../fonts/vm/') + "\n", encoding="utf-8")
    licences = set()
    for rel in sorted(files):
        p = T.OPEN_SOURCE / rel
        if not p.exists():
            print(f"missing {p}: run setup_fonts.py", file=sys.stderr)
            return 1
        shutil.copy2(p, src / "fonts" / "vm" / web_name(rel))
        licences.add(Path(rel).parent.name)
    for fam in licences:
        lic = T.OPEN_SOURCE / fam / "OFL.txt"
        if lic.exists():
            shutil.copy2(lic, src / "fonts" / "vm" / f"OFL-{fam}.txt")
    if not a.no_inline:
        idx = src / "index.html"
        html = idx.read_text(encoding="utf-8")
        if "/* type-kit:begin" in html:
            html = re.sub(r"/\* type-kit:begin.*?/\* type-kit:end \*/", lambda m: block, html, flags=re.S)
        else:
            html = html.replace("</style>", block + "\n</style>", 1)
        for tag in ('<script src="tk/type-kit.config.js"></script>', '<script src="tk/type-kit.js"></script>'):
            if tag not in html:
                html = html.replace("</head>", f"    {tag}\n  </head>", 1)
        idx.write_text(html, encoding="utf-8")
    for role, r in res.items():
        print(f"{role:20} {r['state']:22} renders {r['resolved']}")
    print(f"type kit installed in {src} ({len(files)} font files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

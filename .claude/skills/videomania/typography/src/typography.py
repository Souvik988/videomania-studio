"""Video Mania typography engine: font resolver, selector, text measurement.

One registry (config/font-registry.json) names seven semantic roles. Each role resolves, on the
machine that renders, to one of these states:

  EXACT_AVAILABLE        the requested font is installed here (system font, used in place)
  LICENSED_USER_FONT     a licensed copy the user dropped in fonts/private/ (never committed)
  OPEN_SOURCE_INSTALLED  the requested font is itself open source and bundled (Cormorant Garamond)
  FALLBACK_ACTIVE        the requested font is absent; the declared OFL fallback renders instead
  LICENSE_REQUIRED       the requested font needs a commercial licence we do not hold; fallback renders
  UNAVAILABLE            neither the requested font nor its fallback file is present

Proprietary files are only ever referenced in place (CSS local(), the OS font path); they are
never copied into a project, a delivery or the repo.

Needs fontTools (pip install fonttools brotli). Pure functions; scripts/ hold the CLIs.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

TYPO_DIR = Path(__file__).resolve().parent.parent
CONFIG = TYPO_DIR / "config"
FONTS = TYPO_DIR / "fonts"
OPEN_SOURCE = FONTS / "open-source"
PRIVATE = FONTS / "private"
CACHE = TYPO_DIR / ".cache"

STATES = ("EXACT_AVAILABLE", "LICENSED_USER_FONT", "OPEN_SOURCE_INSTALLED", "FALLBACK_ACTIVE",
          "LICENSE_REQUIRED", "UNAVAILABLE")


def load(name: str) -> dict:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


def registry() -> dict:
    return load("font-registry.json")


def local_config() -> dict:
    """config/local.json (git-ignored): {"licensed_user_fonts": {"Blacksword": "fonts/private/x.otf"}}."""
    p = CONFIG / "local.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ---------------------------------------------------------------- system font scan

def system_font_dirs() -> list[Path]:
    home = Path.home()
    sysname = platform.system()
    if sysname == "Windows":
        win = Path(os.environ.get("WINDIR", r"C:\Windows"))
        dirs = [win / "Fonts", Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "Microsoft/Windows/Fonts"]
    elif sysname == "Darwin":
        dirs = [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"),
                home / "Library/Fonts"]
    else:
        dirs = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".local/share/fonts", home / ".fonts"]
    return [d for d in dirs if d.exists()]


def _names(path: Path) -> list[dict]:
    """Family / subfamily / full / PostScript names of every face in a font file."""
    from fontTools.ttLib import TTCollection, TTFont
    out = []
    try:
        fonts = TTCollection(str(path), lazy=True).fonts if path.suffix.lower() in (".ttc", ".otc") else [TTFont(str(path), lazy=True)]
    except Exception:
        return out
    for f in fonts:
        try:
            n = f["name"]
            fam = n.getDebugName(16) or n.getDebugName(1)
            sub = n.getDebugName(17) or n.getDebugName(2)
            wght = f["OS/2"].usWeightClass if "OS/2" in f else 400
            ital = bool(f["OS/2"].fsSelection & 1) if "OS/2" in f else False
            out.append({"family": fam, "style": sub, "full": n.getDebugName(4), "ps": n.getDebugName(6),
                        "weight": wght, "italic": ital, "path": str(path), "variable": "fvar" in f})
        except Exception:
            continue
    return out


def scan_system_fonts(refresh: bool = False) -> list[dict]:
    """Every installed face (cached in .cache/system-fonts.json; refresh after installing fonts)."""
    CACHE.mkdir(exist_ok=True)
    cache = CACHE / "system-fonts.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    faces = []
    for d in system_font_dirs():
        for p in d.rglob("*"):
            if p.suffix.lower() in (".ttf", ".otf", ".ttc", ".otc"):
                faces += _names(p)
    cache.write_text(json.dumps(faces, indent=0), encoding="utf-8")
    return faces


def find_system(family: str, faces: list[dict]) -> list[dict]:
    """Exact family match only: 'Helvetica' never matches 'Helvetica Neue' or 'Helvetica Now'."""
    f = family.casefold()
    return [x for x in faces if (x["family"] or "").casefold() == f]


# ---------------------------------------------------------------- resolution

def _file_ok(rel: str) -> bool:
    p = OPEN_SOURCE / rel
    return p.exists() and p.stat().st_size > 1000


def resolve_role(role: str, spec: dict, faces: list[dict], local: dict | None = None) -> dict:
    local = local if local is not None else local_config()
    pref, fb = spec["preferred"], spec["fallback"]
    fb_files = {k: str(OPEN_SOURCE / v) for k, v in fb["files"].items()}
    fb_ok = all(_file_ok(v) for v in fb["files"].values())
    out = {"role": role, "requested": pref["family"], "css_family": spec["css_family"], "category": spec["category"],
           "usage": spec["usage"], "animations": spec["animations"], "readability": spec["readability"],
           "fallback_family": fb["family"], "fallback_files": fb_files if fb_ok else {}, "license": pref["license"],
           "fallback_license": fb["license"], "purchase": pref.get("purchase")}
    lic = (local.get("licensed_user_fonts") or {}).get(pref["family"])
    if lic and (TYPO_DIR / lic).exists():
        return {**out, "state": "LICENSED_USER_FONT", "resolved": pref["family"], "exact": True,
                "reference": str(TYPO_DIR / lic), "commercial_ok": True, "faces": []}
    if pref.get("bundled") and fb_ok:
        return {**out, "state": "OPEN_SOURCE_INSTALLED", "resolved": pref["family"], "exact": True,
                "reference": fb_files, "commercial_ok": True, "faces": []}
    hits = [] if pref["license"].startswith("LICENSE_REQUIRED") else find_system(pref["family"], faces)
    if hits:
        return {**out, "state": "EXACT_AVAILABLE", "resolved": pref["family"], "exact": True,
                "reference": sorted({h["path"] for h in hits}), "commercial_ok": True,
                "faces": sorted({(h["weight"], h["italic"]) for h in hits}),
                "local_names": sorted({n for h in hits for n in (h["full"], h["ps"]) if n})}
    state = "LICENSE_REQUIRED" if pref["license"].startswith("LICENSE_REQUIRED") else "FALLBACK_ACTIVE"
    if not fb_ok:
        return {**out, "state": "UNAVAILABLE", "resolved": None, "exact": False, "reference": None,
                "commercial_ok": False, "faces": [], "blocked": state}
    return {**out, "state": state, "resolved": fb["family"], "exact": False, "reference": fb_files,
            "commercial_ok": True, "faces": []}


def resolve_all(refresh: bool = False) -> dict:
    reg = registry()
    faces = scan_system_fonts(refresh)
    local = local_config()
    return {role: resolve_role(role, spec, faces, local) for role, spec in reg["roles"].items()}


# ---------------------------------------------------------------- scripts / multilingual

def detect_script(text: str) -> str:
    """latin (English + romanised Hinglish), devanagari (Hindi), bengali, or mixed."""
    seen = set()
    for ch in text:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F or 0xA8E0 <= o <= 0xA8FF:
            seen.add("devanagari")
        elif 0x0980 <= o <= 0x09FF:
            seen.add("bengali")
        elif ch.isalpha():
            seen.add("latin")
    if not seen:
        return "latin"
    return seen.pop() if len(seen) == 1 else "mixed"


@lru_cache(maxsize=64)
def _cmap(path: str) -> frozenset:
    from fontTools.ttLib import TTFont
    return frozenset(TTFont(path, lazy=True).getBestCmap().keys())


def missing_glyphs(text: str, font_path: str) -> list[str]:
    cmap = _cmap(font_path)
    skip = {"Zs", "Cc", "Cf", "Mn"}   # spaces, controls, joiners; combining marks are checked by the shaper
    return sorted({ch for ch in text if unicodedata.category(ch) not in skip and ord(ch) not in cmap})


def font_path_for(role_res: dict, weight: int = 400, italic: bool = False) -> str | None:
    """A file to measure with: the system face for an exact font, else the fallback file."""
    if role_res["state"] == "EXACT_AVAILABLE":
        return role_res["reference"][0]
    ref = role_res.get("reference")
    if isinstance(ref, str):
        return ref
    files = role_res.get("fallback_files") or {}
    want_i = [k for k in files if k.endswith("i")] if italic else [k for k in files if not k.endswith("i")]
    if not want_i:
        want_i = list(files)
    for k in want_i:
        rng = k.rstrip("i")
        lo, _, hi = rng.partition("-")
        if hi and int(lo) <= weight <= int(hi):
            return files[k]
    best = min(want_i, key=lambda k: abs(int(k.rstrip("i").split("-")[0]) - weight))
    return files[best]


# ---------------------------------------------------------------- measurement + wrapping

@lru_cache(maxsize=32)
def _metrics(path: str):
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True)
    upm = f["head"].unitsPerEm
    hmtx = f["hmtx"].metrics
    cmap = f.getBestCmap()
    hhea = f["hhea"]
    return upm, hmtx, cmap, hhea.ascent, hhea.descent


def measure(text: str, font_path: str, px: float, tracking_em: float = 0.0) -> dict:
    """Advance width (no kerning: a slight over-estimate, which is the safe side) and line box."""
    upm, hmtx, cmap, asc, desc = _metrics(font_path)
    w = 0
    for ch in text:
        g = cmap.get(ord(ch))
        w += hmtx[g][0] if g in hmtx else upm * 0.5
    width = w / upm * px + max(0, len(text) - 1) * tracking_em * px
    return {"width": round(width, 1), "ascent": round(asc / upm * px, 1), "descent": round(-desc / upm * px, 1)}


def wrap(text: str, font_path: str, px: float, max_width: float, max_lines: int = 2, tracking_em: float = 0.0) -> list[str]:
    """Greedy word wrap by measured width; never splits a word; balances two-line captions."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        cand = (cur + " " + wd).strip()
        if cur and measure(cand, font_path, px, tracking_em)["width"] > max_width:
            lines.append(cur)
            cur = wd
        else:
            cur = cand
    if cur:
        lines.append(cur)
    if len(lines) == 2:   # balance: move words down while the top line stays the longer one
        a, b = lines[0].split(), lines[1].split()
        while len(a) > 1:
            na, nb = a[:-1], [a[-1]] + b
            if measure(" ".join(nb), font_path, px, tracking_em)["width"] > measure(" ".join(na), font_path, px, tracking_em)["width"]:
                break
            a, b = na, nb
        lines = [" ".join(a), " ".join(b)]
    return lines if len(lines) <= max_lines else lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:])]


def fit_size(text: str, font_path: str, max_width: float, start_px: float, min_px: float, tracking_em: float = 0.0) -> float:
    """Largest size ≤ start_px at which `text` fits on one line (responsive headline sizing)."""
    px = start_px
    while px > min_px and measure(text, font_path, px, tracking_em)["width"] > max_width:
        px -= 2
    return px


# ---------------------------------------------------------------- selection (deterministic rules)

PAIR_BY_ID = None


def pairings() -> dict:
    global PAIR_BY_ID
    if PAIR_BY_ID is None:
        PAIR_BY_ID = {p["id"]: p for p in load("pairing-presets.json")["pairings"]}
    return PAIR_BY_ID


def presets() -> dict:
    return {p["id"]: p for p in load("typography-presets.json")["presets"]}


_LUX = re.compile(r"\b(luxury|premium|elegan|timeless|crafted|designed for|collection)\w*", re.I)
_PRICE = re.compile(r"(₹|\$|€|£|\brs\.?\s?\d|\d[\d,]*\s?(k|lakh|crore)?\s?(off|%))", re.I)


def select(req: dict) -> dict:
    """Rule-based typography decision. Input keys (all optional except text):
    text, video_type (talking_head|viral|luxury|cinematic|promo|saas|educational|explainer),
    scene_type (hook|body|highlight|emotional|cta|title|price), emotion, emphasis (low|medium|high),
    language (english|hinglish|hindi|bengali), aspect_ratio, background_complexity (low|medium|high).
    """
    text = req.get("text", "")
    vt = (req.get("video_type") or "talking_head").lower()
    scene = (req.get("scene_type") or "body").lower()
    emph = (req.get("emphasis") or "medium").lower()
    emotion = (req.get("emotion") or "").lower()
    lang = (req.get("language") or "english").lower()
    ar = req.get("aspect_ratio") or "9:16"
    bg = (req.get("background_complexity") or "medium").lower()
    script = detect_script(text)
    words = len(text.split())

    if vt in ("luxury", "fashion", "beauty") or _LUX.search(text):
        prim, sec, pair, anim, preset = "luxury_serif", "clean_caption", "helvetica_cormorant", "luxuryReveal", "HELVETICA_CORMORANT_PREMIUM"
        reason = "Premium tone: Cormorant Garamond headline, Helvetica-style support"
        if scene in ("title", "emotional"):
            sec, pair, preset = "elegant_script", "cormorant_snell", "LUXURY_CORMORANT"
            reason = "Luxury title: Cormorant Garamond with a Snell-style script accent"
    elif scene in ("hook", "cta", "price") or _PRICE.search(text) or (vt in ("viral", "promo", "saas", "ad") and emph == "high"):
        prim, sec, pair, anim, preset = "impact_hook", "clean_caption", "impact_helvetica_garamond", "punchIn", "VIRAL_IMPACT_HOOK"
        reason = "Hook / price / CTA: Impact for stopping power, Helvetica-style for the explanation"
        if vt in ("promo", "saas", "ad") and scene not in ("cta", "price"):
            sec, pair, preset = "editorial_slab", "impact_rockwell", "IMPACT_ROCKWELL_AD"
            reason = "Ad hook: Impact headline over a Rockwell-style editorial line"
    elif vt == "cinematic" or scene == "title":
        prim, sec, pair, anim, preset = "editorial_slab", "elegant_script", "rockwell_helvetica", "editorialSlide", "ROCKWELL_EDITORIAL"
        reason = "Cinematic storytelling: Rockwell-style structure, Snell-style accent"
        if emotion in ("tender", "nostalgic", "romantic", "hopeful"):
            prim, pair, anim, preset = "luxury_serif", "cormorant_snell", "softTitle", "SNELL_CINEMATIC"
            reason = "Soft cinematic title: Cormorant Garamond with a script accent"
    elif scene == "emotional" or emotion in ("love", "romantic", "grateful", "inspired", "proud"):
        prim, sec, pair, anim, preset = "clean_caption", "expressive_script", "helvetica_blacksword", "expressiveReveal", "BLACKSWORD_ELEGANT_ACCENT"
        reason = "Emotional highlight: clean caption with one expressive script word"
    elif vt in ("promo", "saas", "ad"):
        prim, sec, pair, anim, preset = "clean_caption", "editorial_slab", "rockwell_helvetica", "cleanWordReveal", "IMPACT_ROCKWELL_AD"
        reason = "Ad body copy: Helvetica-style explanation with Rockwell-style feature lines"
    else:
        prim, sec, pair, anim, preset = "clean_caption", "classical_highlight", "helvetica_garamond", "cleanWordReveal", "HELVETICA_GARAMOND_HIGHLIGHT"
        reason = "Talking head: minimal readable captions with selective Garamond emphasis"
        if emph == "low":
            sec, preset = None, "CLEAN_TALKING_HEAD"
            reason = "Talking head, low emphasis: clean captions only"
        if vt in ("storytelling", "explainer") and words <= 8 and emph == "high":
            pair, preset = "impact_helvetica_garamond", "MULTI_FONT_STORYTELLING"
            reason = "High-retention hierarchy: Impact / Helvetica / Garamond"

    script_role = None
    if script in ("devanagari", "mixed") and any(0x0900 <= ord(c) <= 0x097F for c in text):
        script_role = "devanagari"
    elif script == "bengali" or any(0x0980 <= ord(c) <= 0x09FF for c in text):
        script_role = "bengali"
    if script_role:   # the seven display faces are Latin-only: body text goes to the script face
        reason += f"; {script_role} text renders in the {script_role} fallback (the seven faces have no {script_role} glyphs)"

    portrait = ar in ("9:16", "4:5")
    if scene in ("hook", "title", "price"):
        layout = "hero_center" if portrait else "hero_side_of_subject"
    elif vt in ("talking_head", "promo", "saas", "ad", "educational", "explainer"):
        layout = "safe_lower_middle" if portrait else "open_third_opposite_subject"
    else:
        layout = "safe_lower_middle"
    treatment = "depth_shadow_strong" if bg == "high" else "depth_shadow"
    return {"primary_font_role": prim, "secondary_font_role": sec, "pairing": pair, "preset": preset,
            "animation": anim, "layout": layout, "treatment": treatment, "script": script,
            "script_fallback_role": script_role, "language": lang, "reason": reason}


if __name__ == "__main__":
    print(json.dumps(select(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"text": "Your brand deserves better"}), indent=2, ensure_ascii=False))

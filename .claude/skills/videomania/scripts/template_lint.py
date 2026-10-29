"""Static anti-template lint for a HyperFrames composition's source (heuristic, not a verdict).

Usage:
  template_lint.py SOURCE_DIR [--json OUT.json]

Reads index.html and every *.js under SOURCE_DIR (skipping vendor/, node_modules/, fonts/,
mk/, tk/) and checks the mechanical rules from references/research-digest-2026-10.md section 1
and the determinism rules from motion-design-playbook.md section 13:

  deck          scenes faded with opacity only, no camera/world motion in the source
  transitions   fewer than two kinds of transition, or a light leak used more than once
  motion_range  only scale+opacity tweens (Ken Burns / fade deck)
  metadata      package names or long URLs on screen
  placeholders  lorem, TODO, grey bar placeholders
  determinism   Math.random, Date.now, performance.now, repeat:-1 (not seek-safe)

Exit code 0 always; the summary lists WARN lines. A WARN is a prompt to look at the frames, not
proof of a defect: the independent critic and qa.py still decide.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"vendor", "node_modules", "fonts", "mk", "tk", "media", "audio", ".git"}

TRANSITION_KINDS = {
    "iris": r"\biris\s*\(|clip-?path\s*:\s*[\"'`]?circle|keyhole",
    "focus_pull": r"focusPull|rack\s*focus|blur\([^)]*\)[^;]*scale",
    "flash": r"\bflash\s*\(|whiteFlash|dipTo",
    "letterbox": r"letterbox|bars?In\b",
    "whip": r"whip|panBlur|motionBlurPan",
    "zoom_through": r"zoomThrough|pushThrough|diveInto|diveThrough",
    "object_wipe": r"objectWipe|object-wipe|wipeWith|shapeWipe",
    "match_cut": r"matchCut|morph\s*\(|MK\.morph",
    "page_flip": r"pageFlip|flipPage|cardFlip",
    "light_leak": r"light-?leak|lightLeak|leak\s*\(",
}
MOTION_PROPS = {
    "x/y": r"\b(x|y|xPercent|yPercent)\s*:",
    "scale": r"\bscale(X|Y)?\s*:",
    "rotation": r"\brotat(ion|e|ionX|ionY)\s*:",
    "opacity": r"\b(opacity|autoAlpha)\s*:",
    "clip": r"clipPath\s*:|maskImage|mask-image",
    "filter": r"filter\s*:|blur\(",
    "path/draw": r"strokeDashoffset|drawSVG|MotionPath|motionPath",
    "3d": r"rotationX|rotationY|perspective|z\s*:|translateZ",
    "text": r"SplitText|per-?letter|stagger\s*:|letterSpacing",
}


def read_sources(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in {".html", ".js", ".mjs", ".css"}:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        if p.stat().st_size > 800_000:
            continue
        out[str(p.relative_to(root)).replace("\\", "/")] = p.read_text(encoding="utf-8", errors="ignore")
    return out


def lint(files: dict[str, str]) -> dict:
    code = "\n".join(files.values())
    res: dict = {"files": list(files), "checks": []}

    def add(name: str, status: str, detail: str):
        res["checks"].append({"check": name, "status": status, "detail": detail})

    # deck: scene containers + opacity toggles, with no world/camera motion
    scenes = len(re.findall(r"class=[\"']scene[\"']|className\s*=\s*[\"']scene[\"']|<section\b", code))
    opacity_sw = len(re.findall(r"(autoAlpha|opacity)\s*:\s*[01]\b", code))
    camera = len(re.findall(r"camera|world\b|stage\b|zoomThrough|pushThrough|vertigo|orbit|pullbackReveal", code, re.I))
    if scenes >= 3 and camera < 3:
        add("deck", "WARN", f"{scenes} scene containers, {opacity_sw} opacity switches, only {camera} camera/world references: reads as a slide deck")
    else:
        add("deck", "PASS", f"{scenes} scene containers, {camera} camera/world references")

    # transitions
    kinds = {k: len(re.findall(rx, code, re.I)) for k, rx in TRANSITION_KINDS.items()}
    used = {k: n for k, n in kinds.items() if n}
    non_leak = [k for k in used if k != "light_leak"]
    msgs = []
    if len(non_leak) < 2:
        msgs.append(f"only {len(non_leak)} transition kind(s) found: {sorted(non_leak) or 'none'}")
    if used.get("light_leak", 0) > 1:
        msgs.append(f"light leak used {used['light_leak']} times (save it for one moment)")
    add("transitions", "WARN" if msgs else "PASS", "; ".join(msgs) or f"kinds: {used}")

    # motion range
    props = {k: len(re.findall(rx, code)) for k, rx in MOTION_PROPS.items()}
    families = [k for k, n in props.items() if n]
    if set(families) <= {"scale", "opacity"}:
        add("motion_range", "WARN", f"only {families} are animated: Ken Burns / fade deck")
    elif len(families) < 4:
        add("motion_range", "WARN", f"narrow motion vocabulary {families}; add depth, clip, filter or path motion")
    else:
        add("motion_range", "PASS", f"{len(families)} property families: {families}")

    # metadata on screen
    pkg = re.findall(r"\b(?:com|org|io|app)\.[a-z0-9_]+\.[a-z0-9_.]+\b", code)
    urls = [u for u in re.findall(r"https?://[^\s\"'<>)]+", code) if len(u) > 60 and not re.search(r"cdn|googleapis|gstatic|jsdelivr|unpkg|cloudflare|github", u)]
    if pkg or urls:
        add("metadata", "WARN", f"package-like names {pkg[:3]} / long URLs {len(urls)}: cut metadata from the screen")
    else:
        add("metadata", "PASS", "no package names or long URLs")

    # placeholders
    ph = re.findall(r"lorem ipsum|\bTODO\b|\bFIXME\b|placeholder", code, re.I)
    add("placeholders", "WARN" if ph else "PASS", f"{len(ph)} placeholder markers" if ph else "none")

    # determinism
    bad = {
        "Math.random": len(re.findall(r"Math\.random\s*\(", code)),
        "Date.now": len(re.findall(r"Date\.now\s*\(|new Date\s*\(", code)),
        "performance.now": len(re.findall(r"performance\.now\s*\(", code)),
        "repeat:-1": len(re.findall(r"repeat\s*:\s*-1", code)),
    }
    badn = {k: n for k, n in bad.items() if n}
    add("determinism", "WARN" if badn else "PASS", f"not seek-safe: {badn}" if badn else "no wall-clock or infinite loops")
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="composition source directory (contains index.html)")
    ap.add_argument("--json", help="write the report here")
    a = ap.parse_args()
    root = Path(a.source)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    files = read_sources(root)
    if not files:
        print(f"no html/js sources under {root}", file=sys.stderr)
        return 2
    res = lint(files)
    for c in res["checks"]:
        print(f"[{c['status']:<4}] {c['check']:<13} {c['detail']}")
    warns = sum(c["status"] == "WARN" for c in res["checks"])
    print(f"template_lint: {warns} warning(s) over {len(files)} file(s). Heuristic: look at the frames before acting.")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

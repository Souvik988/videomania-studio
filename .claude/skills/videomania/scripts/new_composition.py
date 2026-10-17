"""Start a film's HyperFrames composition from the Video Mania scaffold.

Usage:
  new_composition.py --project ID --look warm-editorial|apple-product|dark-lit|minimal-dimensional
                     --format 9:16|16:9 --duration SECONDS [--title "..."] [--captions chunk|phrase]
                     [--grain 0.06] [--brand SLUG] [--force]

Creates projects/ID/source/ with:
  index.html          scaffold: one paused timeline, scene() helper, caption module, grain, safe zone
  mk/motion-kit.js    toolkit (springs, morph+ghost, camera windows, spotlight, mask reveals, …)
  mk/motion-fx.js     premium effects (headline, chartMorph, dashboardZoom, cardToWorkspace,
                      springStack, flowingPaths, counterTag, notifications, cursorClick, irisPass,
                      particleWord)
  fonts/, vendor/gsap-3.14.2.min.js
The look's tokens (and the brand's MOTION.md tokens when --brand is given and
brands/SLUG/tokens.css exists) are inlined into index.html, so fonts and colours are in-file.
Never overwrites an existing index.html without --force.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

KIT = vm_env.SKILL_DIR / "assets" / "motion-kit"
TEMPLATE = vm_env.SKILL_DIR / "templates" / "composition" / "index.html"
NL = chr(10)
LOOKS = ["warm-editorial", "apple-product", "dark-lit", "minimal-dimensional"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--look", required=True, choices=LOOKS)
    ap.add_argument("--format", required=True, choices=["9:16", "16:9"])
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--title", default="Video Mania film")
    ap.add_argument("--captions", choices=["chunk", "phrase"])
    ap.add_argument("--grain", type=float, default=0.06)
    ap.add_argument("--brand", help="brands/SLUG with tokens.css (from MOTION.md) to layer over the look")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--scenes-js", help="file with scene(...) calls to inject at the scenes marker")
    ap.add_argument("--gallery", action="store_true", help="build the motion-kit look book (11 scene divs, no audio)")
    a = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(a.project)
    src = proj / "source"
    src.mkdir(parents=True, exist_ok=True)
    if (src / "index.html").exists() and not a.force:
        print(f"{src / 'index.html'} exists; pass --force to replace it")
        return 1
    portrait = a.format == "9:16"
    W, H = (1080, 1920) if portrait else (1920, 1080)
    caps = a.captions or ("chunk" if portrait else "phrase")
    (src / "mk").mkdir(exist_ok=True)
    for f in ("motion-kit.js", "motion-fx.js"):
        shutil.copy2(KIT / f, src / "mk" / f)
    shutil.copytree(KIT / "fonts", src / "fonts", dirs_exist_ok=True)
    (src / "vendor").mkdir(exist_ok=True)
    shutil.copy2(KIT / "vendor" / "gsap-3.14.2.min.js", src / "vendor" / "gsap-3.14.2.min.js")
    look_css = (KIT / "looks" / f"{a.look}.css").read_text(encoding="utf-8")
    if a.brand:
        bt = vm_env.SKILL_DIR / "brands" / a.brand / "tokens.css"
        if bt.exists():
            look_css += "\n/* brand tokens: brands/" + a.brand + "/tokens.css */\n" + bt.read_text(encoding="utf-8")
        else:
            print(f"note: {bt} not found; using the look's tokens only", file=sys.stderr)
    html = TEMPLATE.read_text(encoding="utf-8")
    subs = {
        "{{W}}": str(W), "{{H}}": str(H), "{{DUR}}": f"{a.duration:g}", "{{TITLE}}": a.title,
        "{{FONT_CSS}}": (KIT / "looks" / "fonts.css").read_text(encoding="utf-8"),
        "{{LOOK_CSS}}": look_css,
        "{{CAP_TOP}}": "1372" if portrait else "880", "{{CAP_MAXW}}": "960" if portrait else "1500",
        "{{CAP_PX}}": "52" if portrait else "44", "{{CHUNK_PX}}": "64" if portrait else "56",
        "{{CHUNK}}": "true" if caps == "chunk" else "false", "{{GRAIN}}": f"{a.grain:g}",
    }
    for k, v in subs.items():
        html = html.replace(k, v)
    if a.scenes_js:
        marker = "      // ---- scenes go here (one per beat of the motion brief's scene chain) ----"
        sj = Path(a.scenes_js)
        sj = sj if sj.exists() else vm_env.SKILL_DIR / a.scenes_js
        html = html.replace(marker, marker + NL + sj.read_text(encoding="utf-8"))
    if a.gallery:
        divs = "".join(f'<div class="scene" id="s{i:02d}"></div>' for i in range(1, 12))
        html = html.replace('        <!-- one <div class="scene" id="s01"> per beat; footage <video> layers sit in non-timed wrappers -->', "        " + divs)
        html = NL.join(l for l in html.split(NL) if '<audio id="mix"' not in l)
        (src / "data.js").write_text('window.CUES = [{"s":0.4,"e":1.4,"c":"","lines":[[{"w":"One","s":0.45,"e":0.7,"c":""},{"w":"object","s":0.7,"e":1.1,"c":""}]]},'
                                     '{"s":1.45,"e":2.9,"c":"go","lines":[[{"w":"changes","s":1.5,"e":1.9,"c":"go"},{"w":"shape","s":1.9,"e":2.4,"c":"go"}]]}];'
                                     + NL + "window.CAP_OFF = [];" + NL, encoding="utf-8")
    (src / "index.html").write_text(html, encoding="utf-8")
    if not (src / "data.js").exists():
        (src / "data.js").write_text("// caption_track.py writes window.CUES here\nwindow.CUES = [];\nwindow.CAP_OFF = [];\n", encoding="utf-8")
    print(f"scaffold ready: {src} ({W}x{H}, {a.duration:g}s, look {a.look}, captions {caps})")
    print(f"next: caption_track.py --project {a.project} --mode {caps}; add scenes; npx hyperframes check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

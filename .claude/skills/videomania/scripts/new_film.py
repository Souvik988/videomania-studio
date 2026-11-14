"""Start a voxel-diorama film project in one command (runbook Step 5, plus the asset reuse of Step 3).

    python new_film.py <project_dir> --duration 10.16 [--size 1920x1080] [--assets-from <other_project_dir>] [--no-assets]

What it does (so a model cannot get the setup wrong):
  1. copies the voxel-diorama kit into <project_dir>/source/ (without the worked examples);
  2. sets #root data-duration, the canvas/viewport size and adds the audio tag
     <audio id="mix" src="mix.wav" ...> (sound_mix.py writes source/mix.wav later);
  3. writes a skeleton source/shots.js (size, duration, palette, lens, the creator mascot `me`, the stage
     backdrop plate, an empty meta and an empty shots list) to fill in, overwriting the kit's demo shots.js;
  4. makes the asset folders (assets/gen/icons, plates, clips, mascot) and storyboard/;
  5. assets: by default copies the skill's bundled starter set (assets/voxel-starter/: the mascot with depth maps,
     icons, screens, stage backdrop, plates). --assets-from <project> copies from an earlier film instead;
     --no-assets copies nothing. The reusable approved assets of an earlier film (the mascot `me` with its depth
     maps, gen/ icons + screens + backdrop, plates). REUSE BEFORE GENERATING: only make what is new.

Never put a second HTML file with data-composition-id inside source/ (hyperframes check rejects it).
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
KIT = SKILL / "templates" / "voxel-diorama"

SKELETON = """// {name}: shot list. Fields: templates/voxel-diorama/README.md. Worked film: examples/director-film-v5.shots.js
// Times are the voiceover's word times (transcript/words.json). Every shot needs a `why`.
window.SHOTS = {{
  size: [{w}, {h}], duration: {dur},
  palette: {{ voice: "#e11d2e", voice2: "#ff6a1a", accent: "#19c8b9" }},
  lens: {{ aperture: 0.35, grain: 0.02 }},
  cast: {{ me: {{ poses: "assets/mascot/me/poses.json", tall: 12.5, head: 0.8, ref: "talk", lift: 0.9 }} }},
  plates: [{{ set: "color-studio", src: "assets/gen/stage_backdrop.png", at: [0, 30, -31.9], w: 150, h: 84, glow: 0.62 }}],
  meta: {{ film: "{name}", concept: "", device: "", hook: "", signature: "", structure: "", constraint: "" }},
  shots: [
    // {{ id: "A", t0: 0, t1: 3.4, set: "studio", focus: "me", why: "...", cam: {{ keys: [...] }}, cast: [...], type: {{ depth: true, x: 0.52, y: 0.1, w: 0.44 }}, lines: [...], out: "flash" }},
  ],
}};
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--assets-from")
    ap.add_argument("--no-assets", action="store_true")
    a = ap.parse_args()
    P = Path(a.project).expanduser().resolve()
    src = P / "source"
    w, h = (int(x) for x in a.size.lower().split("x"))
    if (src / "shots.js").exists() and "{name}" not in (src / "shots.js").read_text(encoding="utf-8")[:200] \
            and "window.SHOTS" in (src / "shots.js").read_text(encoding="utf-8") and (src / "shots.js").stat().st_size > 2500:
        sys.exit(f"{src}/shots.js already holds a film ({(src / 'shots.js').stat().st_size} bytes); refusing to overwrite it")
    src.mkdir(parents=True, exist_ok=True)
    for item in KIT.iterdir():
        if item.name == "examples":
            continue
        dst = src / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst)
    for d in ("assets/gen/icons", "assets/plates", "assets/clips", "assets/mascot"):
        (src / d).mkdir(parents=True, exist_ok=True)
    (P / "storyboard").mkdir(exist_ok=True)

    html = (src / "index.html").read_text(encoding="utf-8")
    dur = f"{a.duration:g}"
    html = re.sub(r'width=\d+, height=\d+', f"width={w}, height={h}", html, count=1)
    html = re.sub(r'data-width="\d+" data-height="\d+" data-duration="[\d.]+"',
                  f'data-width="{w}" data-height="{h}" data-duration="{dur}"', html, count=1)
    html = re.sub(r'(<canvas id="vd-canvas") width="\d+" height="\d+"', rf'\1 width="{w}" height="{h}"', html, count=1)
    if "<audio" not in html:
        html = re.sub(r'(<canvas id="vd-canvas"[^>]*></canvas>)',
                      rf'\1\n      <audio id="mix" src="mix.wav" data-start="0" data-duration="{dur}" data-volume="1"></audio>',
                      html, count=1)
    (src / "index.html").write_text(html, encoding="utf-8")
    (src / "shots.js").write_text(SKELETON.format(name=P.name, w=w, h=h, dur=dur), encoding="utf-8")

    if not a.no_assets:
        if a.assets_from:
            o = Path(a.assets_from).expanduser().resolve() / "source" / "assets"
        else:
            o = SKILL / "assets" / "voxel-starter"
        n = 0
        for rel in ("mascot/me", "gen", "plates", "cast"):
            if (o / rel).exists():
                shutil.copytree(o / rel, src / "assets" / rel, dirs_exist_ok=True)
                n += 1
        print(f"assets copied from {o} ({n} folders): mascot, gen, plates, cast")
    print(f"project ready: {P}\n  source/index.html {w}x{h} {dur}s with audio tag;  source/shots.js skeleton to fill in")


if __name__ == "__main__":
    main()

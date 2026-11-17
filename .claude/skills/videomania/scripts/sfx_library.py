"""The hook-sound library: build it from the CC0 SFX Kit + Video Mania's own synth sounds, and search it.

    python sfx_library.py build --kit <research>/wyzowl_sfx-kit     # (re)bundles the picked sounds as OGG
    python sfx_library.py find "ominous hit"                         # search ids, descriptions, use_for, tags
    python sfx_library.py show braam                                 # one sound's data (sync point, loudness)

Library: <skill>/assets/sfx-hook/ (kit/*.ogg, synth/*.wav, manifest.json). Every entry has `sync_at` (the moment of
the sound that must land on the picture event: a hit's peak, a riser's END) and `lufs` (measured), so fx_pass.py can
place and level-match it. Sources: SFX Kit by Wyzowl (CC0-1.0, github.com/wyzowl/sfx-kit) and hook_sounds.py (CC0).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "assets" / "sfx-hook"

PICK = [
    # cinematic hits and booms (the hook layer)
    "cinematic-drum-big", "cinematic-drum-massive", "cinematic-metal-big", "cinematic-slam-big", "cinematic-thunder-big",
    "bass-808-short", "bass-808-medium", "bass-sub-drop-short", "bass-sub-drop-medium", "bass-rumble-short",
    "boom-hit-soft", "boom-hit-medium", "boom-hit-strong", "boom-drop-medium", "boom-drop-strong",
    # build-ups and pulls
    "riser-1s-soft", "riser-1s-strong", "riser-2s-strong", "riser-4s-strong", "faller-1s-strong",
    "reverse-whoosh-short-strong", "reverse-whoosh-medium-strong", "reverse-whoosh-medium-soft", "reverse-whoosh-long-strong",
    # movement
    "whoosh-fast-hard", "whoosh-fast-medium", "whoosh-medium-hard", "whoosh-medium-medium", "whoosh-slow-hard",
    "move-zoom-in", "move-zoom-out", "move-spin",
    # digital / glitch texture
    "digital-glitch-clear", "digital-glitch-subtle", "digital-corrupt", "digital-static", "digital-interference",
    "digital-signal-drop", "digital-scramble", "digital-power-up", "digital-power-down", "digital-scan-clear",
    # stings and accents
    "sting-bold-short", "sting-tech-short", "sting-bright-short",
    "impact-deep-hard", "impact-medium-soft", "impact-light-firm",
    "shimmer-short-soft", "pop-medium-in", "swish-medium",
]


def lufs(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def build(kit):
    kit = Path(kit)
    data = json.loads((kit / "sounds.json").read_text(encoding="utf-8"))
    data = data["sounds"] if isinstance(data, dict) else data
    by = {s["id"]: s for s in data}
    (LIB / "kit").mkdir(parents=True, exist_ok=True)
    man = []
    for sid in PICK:
        s = by.get(sid)
        if not s:
            print("not in kit:", sid)
            continue
        src = kit / s["file"]
        dst = LIB / "kit" / f"{sid}.ogg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-c:a", "libvorbis", "-q:a", "6", "-ar", "48000", str(dst)], check=True)
        man.append({
            "id": sid, "file": f"kit/{sid}.ogg", "category": s["category"], "duration": s["duration"],
            "sync_at": (s.get("sync") or {}).get("at", (s.get("timing") or {}).get("peak", 0.0)),
            "sync_meets": (s.get("sync") or {}).get("meets"),
            "tier": (s.get("level") or {}).get("tier"), "lufs": (s.get("level") or {}).get("lufs"),
            "under_voiceover_db": s.get("under_voiceover_db"),
            "description": s["description"], "use_for": s.get("use_for", []), "avoid_for": s.get("avoid_for", []),
            "tags": s.get("tags", []), "source": "SFX Kit by Wyzowl, github.com/wyzowl/sfx-kit", "license": "CC0-1.0",
        })
    synth_m = LIB / "manifest_synth.json"
    if synth_m.exists():
        for s in json.loads(synth_m.read_text(encoding="utf-8")):
            s["lufs"] = lufs(LIB / s["file"])
            man.append(s)
    (LIB / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"{len(man)} sounds -> {LIB / 'manifest.json'}")


def load():
    return json.loads((LIB / "manifest.json").read_text(encoding="utf-8"))


def find(q):
    words = q.lower().split()
    rows = []
    for s in load():
        hay = " ".join([s["id"], s.get("category", ""), s.get("description", ""), " ".join(s.get("use_for", [])), " ".join(s.get("tags", []))]).lower()
        score = sum(w in hay for w in words)
        if score:
            rows.append((score, s))
    for score, s in sorted(rows, key=lambda r: -r[0])[:15]:
        print(f"{s['id']:30s} {s['duration']:5.2f}s sync {s['sync_at']:.2f}  {s['description'][:70]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build"); b.add_argument("--kit", required=True)
    f = sp.add_parser("find"); f.add_argument("query")
    s = sp.add_parser("show"); s.add_argument("id")
    a = ap.parse_args()
    if a.cmd == "build":
        build(a.kit)
    elif a.cmd == "find":
        find(a.query)
    else:
        hit = [x for x in load() if x["id"] == a.id]
        print(json.dumps(hit[0] if hit else {"error": "no such id"}, indent=1))


if __name__ == "__main__":
    main()

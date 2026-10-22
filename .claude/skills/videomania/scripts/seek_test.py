"""Seek-determinism test for a HyperFrames composition.

Usage: seek_test.py --source PROJECT_SOURCE_DIR [--times 0.5,3.3,...] [--out DIR] [--software]

Captures the same timestamps twice in two different shuffled orders, in two
separate snapshot runs (fresh browser each), then compares SHA-256 of the
decoded RGBA pixels per timestamp. Identical requested time + inputs must give
identical pixels regardless of seek order. Exit 0 = all identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def pixel_hash(png: Path) -> str:
    from PIL import Image
    with Image.open(png) as im:
        return hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()


def capture(source: Path, times: list[float], out: Path, software: bool) -> dict[float, Path]:
    # heavy compositions (alpha video, many fonts) need longer than the 5 s default to initialise
    args = ["snapshot", "--at", ",".join(f"{t:g}" for t in times), "--no-end", "--timeout", "45000", "--describe", "false", "-o", str(out)]
    if software:
        args.append("--no-browser-gpu")
    vm_env.npx_hf(args, cwd=source, timeout=900)
    found = {}
    for p in out.glob("frame-*-at-*s.png"):
        m = re.search(r"-at-([\d.]+)s\.png$", p.name)
        found[float(m.group(1))] = p
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--times", default="0.5,2.4,3.4,5.7,9.9,14.6,16.9,18.9,21.0,21.95,23.8,26.5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--software", action="store_true", help="force SwiftShader (deterministic CPU raster)")
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    source = Path(args.source).resolve()
    times = [float(x) for x in args.times.split(",")]
    # absolute: snapshot runs with cwd=source, so a relative -o would land inside source/
    out = (Path(args.out) if args.out else source.parent / "qa" / "seek_test").resolve()
    rnd = random.Random(1234)
    order_a = times[:]
    rnd.shuffle(order_a)
    order_b = list(reversed(order_a))
    a = capture(source, order_a, out / "run_a", args.software)
    b = capture(source, order_b, out / "run_b", args.software)
    rows, ok = [], True
    for t in times:
        ha = pixel_hash(a[t]) if t in a else None
        hb = pixel_hash(b[t]) if t in b else None
        same = ha is not None and ha == hb
        ok &= same
        rows.append({"t": t, "identical": same, "hash_a": ha, "hash_b": hb})
    report = {"source": str(source), "order_a": order_a, "order_b": order_b, "software_raster": args.software,
              "all_identical": ok, "frames": rows}
    vm_env.write_json(out / "seek_report.json", report)
    print(json.dumps({"all_identical": ok, "compared": len(rows),
                      "mismatches": [r["t"] for r in rows if not r["identical"]]}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

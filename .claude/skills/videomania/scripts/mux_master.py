"""Replace a render's audio with the measured master mix (video stream copied).

Usage: mux_master.py --video RENDER.mp4 --mix audio/mix.wav --out final.mp4 [--bitrate 256k]

Why: a renderer may re-process embedded audio (HyperFrames' path measured
+3 LU over the master in this workbench). The master mix is the audited audio,
so the deliverable carries it bit-for-bit through a single AAC encode. The
video stream is copied, never re-encoded. Duration is clipped to the video.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--mix", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bitrate", default="256k")
    args = ap.parse_args()
    vdur = float(vm_env.ffprobe(args.video)["format"]["duration"])
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", args.video, "-i", args.mix, "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", args.bitrate, "-ar", "48000", "-ac", "2",
                "-t", f"{vdur:.3f}", "-movflags", "+faststart", args.out])
    pr = vm_env.ffprobe(args.out)
    streams = [f"{s['codec_type']}:{s.get('codec_name')}" for s in pr["streams"]]
    print(json.dumps({"out": args.out, "duration_s": float(pr["format"]["duration"]), "streams": streams,
                      "loudness": vm_env.loudness(args.out)}, indent=2))
    return 0 if "audio:aac" in streams and any(s.startswith("video:") for s in streams) else 1


if __name__ == "__main__":
    raise SystemExit(main())

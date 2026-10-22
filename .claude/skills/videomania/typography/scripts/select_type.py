"""Pick typography for a line: the rule-based selector, plus the resolved faces and the preset.

Usage:
  python -P select_type.py '{"text": "Your brand deserves better", "video_type": "talking_head", "emphasis": "medium"}'
  python -P select_type.py --text "ONLY ₹50,000" --video-type promo --scene price
  python -P select_type.py --pairing helvetica_garamond      # show a pairing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import typography as T  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="?")
    ap.add_argument("--text")
    ap.add_argument("--video-type")
    ap.add_argument("--scene")
    ap.add_argument("--emotion")
    ap.add_argument("--emphasis")
    ap.add_argument("--language")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--pairing")
    a = ap.parse_args()
    if a.pairing:
        print(json.dumps(T.pairings()[a.pairing], indent=2, ensure_ascii=False))
        return 0
    req = json.loads(a.json) if a.json else {"text": a.text or "", "video_type": a.video_type, "scene_type": a.scene,
                                             "emotion": a.emotion, "emphasis": a.emphasis, "language": a.language,
                                             "aspect_ratio": a.aspect}
    out = T.select({k: v for k, v in req.items() if v})
    res = T.resolve_all()
    out["fonts"] = {k: f"{res[r]['requested']} → {res[r]['resolved']} [{res[r]['state']}]"
                    for k, r in (("primary", out["primary_font_role"]), ("secondary", out["secondary_font_role"])) if r}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

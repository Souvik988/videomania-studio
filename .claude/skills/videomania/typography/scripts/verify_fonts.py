"""Verify the typography install: files, licences, glyph coverage, real weights, presets wiring.

Exit 0 only when every check passes. Prints one line per check.
Usage: python -P verify_fonts.py [--text "caption text to glyph-check"] [--role clean_caption]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import typography as T  # noqa: E402

SAMPLES = {
    "latin": "THE QUICK BROWN FOX JUMPS 0123456789 ₹ ? ! the quick brown fox",
    "hinglish": "Har creator ye font use karta hai",
    "devanagari": "हर क्रिएटर ये फ़ॉन्ट इस्तेमाल करता है",
    "bengali": "প্রতিটি ক্রিয়েটর এই ফন্ট ব্যবহার করে",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--role")
    a = ap.parse_args()
    reg, res = T.registry(), T.resolve_all()
    fails = 0

    def check(ok: bool, msg: str) -> None:
        nonlocal fails
        fails += 0 if ok else 1
        print(("PASS " if ok else "FAIL ") + msg)

    check(len(reg["roles"]) == 7, f"7 roles registered ({len(reg['roles'])})")
    for role, r in res.items():
        check(r["state"] in T.STATES and r["state"] != "UNAVAILABLE", f"{role}: {r['requested']} → {r['resolved']} [{r['state']}]")
        check(r["exact"] == (r["resolved"] == r["requested"]), f"{role}: exact flag matches the resolved family (no fallback reported as original)")
        lic = T.OPEN_SOURCE / reg["roles"][role]["fallback"]["license_file"]
        check(lic.exists() and "Open Font License" in lic.read_text(encoding="utf-8", errors="ignore"), f"{role}: licence file kept ({lic.name})")
        path = T.font_path_for(r)
        miss = T.missing_glyphs(SAMPLES["latin"].replace("₹", "") + SAMPLES["hinglish"], path)
        check(not miss, f"{role}: Latin + Hinglish glyphs present in {Path(path).name} {miss or ''}")
        # weights: every registered weight must be a real face (static file or inside a variable font's axis)
        from fontTools.ttLib import TTFont
        files = r["fallback_files"] if not r["state"] == "EXACT_AVAILABLE" else {}
        for key, f in files.items():
            ft = TTFont(f, lazy=True)
            lo, _, hi = key.rstrip("i").partition("-")
            if "fvar" in ft:
                ax = {x.axisTag: (x.minValue, x.maxValue) for x in ft["fvar"].axes}
                check("wght" in ax and ax["wght"][0] <= int(lo) and ax["wght"][1] >= int(hi or lo), f"{role}: variable {Path(f).name} covers wght {key}")
            else:
                check(abs(ft["OS/2"].usWeightClass - int(lo)) <= 100, f"{role}: static {Path(f).name} is weight {ft['OS/2'].usWeightClass} (registered {key})")
    # script fallbacks
    for key, sample in (("devanagari", SAMPLES["devanagari"]), ("bengali", SAMPLES["bengali"])):
        spec = reg["script_fallbacks"][key]
        f = T.OPEN_SOURCE / list(spec["files"].values())[0]
        check(f.exists() and not T.missing_glyphs(sample, str(f)), f"script fallback {key}: {spec['family']} covers the sample")
    # proprietary files never inside the skill
    bad = [p for p in T.TYPO_DIR.rglob("*") if p.suffix.lower() in (".ttf", ".otf", ".ttc", ".woff", ".woff2")
           and "open-source" not in p.parts and "private" not in p.parts]
    check(not bad, f"no font files outside fonts/open-source and fonts/private {[str(b) for b in bad][:3]}")
    priv_ignored = (T.FONTS / "private" / ".gitignore").exists()
    check(priv_ignored, "fonts/private/ is git-ignored")
    # configs wired: 8 pairings, 10 presets, every preset role/pairing/animation exists
    pairs = T.pairings()
    pres = T.presets()
    check(len(pairs) == 8, f"8 pairings ({len(pairs)})")
    check(len(pres) == 10, f"10 presets ({len(pres)})")
    js = (T.TYPO_DIR / "src" / "type-kit.js").read_text(encoding="utf-8")
    for pid, p in pres.items():
        roles_ok = all(r in reg["roles"] for r in p["roles"].values())
        pair_ok = p["pairing"] is None or p["pairing"] in pairs
        anims = [v for k, v in p["animation"].items() if k.endswith("in") and isinstance(v, str)]
        anim_ok = all(f"A.{x} =" in js for x in anims)
        check(roles_ok and pair_ok and anim_ok, f"preset {pid}: roles, pairing and animations {anims} exist")
    for pid, p in pairs.items():
        check(all(r in reg["roles"] for r in p["tiers"].values()), f"pairing {pid}: tiers resolve")
    for role, spec in reg["roles"].items():
        missing = [x for x in spec["animations"] if f"A.{x} =" not in js]
        check(not missing, f"{role}: animation presets implemented {spec['animations']}")
    if a.text:
        role = a.role or "clean_caption"
        script = T.detect_script(a.text)
        path = T.font_path_for(res[role])
        miss = T.missing_glyphs(a.text, path)
        if script != "latin":
            sk = "devanagari" if any(0x0900 <= ord(c) <= 0x097F for c in a.text) else "bengali"
            f2 = T.OPEN_SOURCE / list(reg["script_fallbacks"][sk]["files"].values())[0]
            miss = [c for c in miss if c in T.missing_glyphs(a.text, str(f2))]
        check(not miss, f"--text in {role} ({script}): every glyph renders {miss or ''}")
    print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

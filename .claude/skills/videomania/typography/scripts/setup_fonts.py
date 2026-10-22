"""Install the open-source faces of the typography registry (idempotent, offline after the first run).

Downloads each OFL fallback (and the bundled Cormorant Garamond, Noto/Hind script faces) from the
google/fonts repository pinned to registry.google_fonts_commit, keeps its OFL.txt, verifies every
file parses as a font with the expected family name, and records sha256 in
fonts/open-source/MANIFEST.json. Files already present with a matching hash are skipped. Inter comes
from the motion kit (rsms/inter, already bundled).

Never downloads proprietary fonts. Never touches system font folders.

Usage: python -P setup_fonts.py [--verify-only] [--force]
(-P: the script folder is not put on sys.path, so nothing next to downloaded files is importable)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import typography as T  # noqa: E402

RAW = "https://raw.githubusercontent.com/google/fonts/{commit}/{gf_dir}/{name}"
KIT_FONTS = T.TYPO_DIR.parent / "assets" / "motion-kit" / "fonts"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def entries(reg: dict):
    for role, spec in reg["roles"].items():
        yield role, spec["fallback"]
    for key, spec in reg["script_fallbacks"].items():
        yield key, spec


def family_of(p: Path) -> str:
    from fontTools.ttLib import TTFont
    f = TTFont(str(p), lazy=True)
    return f["name"].getDebugName(16) or f["name"].getDebugName(1)


def fetch(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    curl = shutil.which("curl")
    if curl:   # urllib can stall for minutes on some Windows networks; curl does not
        subprocess.run([curl, "-gsSfL", "--retry", "2", "-o", str(tmp), url], check=True, timeout=180)
    else:
        with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as out:
            shutil.copyfileobj(r, out)
    tmp.replace(dest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    reg = T.registry()
    T.OPEN_SOURCE.mkdir(parents=True, exist_ok=True)
    (T.PRIVATE).mkdir(parents=True, exist_ok=True)
    man_p = T.OPEN_SOURCE / "MANIFEST.json"
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {}
    report, bad = [], 0
    for key, fb in entries(reg):
        names = list(fb["files"].values()) + [fb["license_file"]]
        for rel in names:
            dest = T.OPEN_SOURCE / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            known = manifest.get(rel, {}).get("sha256")
            if dest.exists() and not a.force and (not known or known == sha256(dest)):
                status = "present"
            elif a.verify_only:
                report.append((key, rel, "MISSING")); bad += 1
                continue
            elif fb.get("gf_dir"):
                url = RAW.format(commit=reg["google_fonts_commit"], gf_dir=fb["gf_dir"], name=urllib.parse.quote(Path(rel).name))
                try:
                    fetch(url, dest)
                    status = "downloaded"
                except Exception as e:  # network, 404
                    report.append((key, rel, f"FAILED {e}")); bad += 1
                    continue
            else:   # Inter: from the motion kit
                src = KIT_FONTS / ("OFL-inter.txt" if rel.endswith("OFL.txt") else Path(rel).name)
                if not src.exists():
                    report.append((key, rel, f"MISSING source {src}")); bad += 1
                    continue
                shutil.copy2(src, dest)
                status = "copied from motion kit"
            h = sha256(dest)
            if known and known != h and not a.force:
                report.append((key, rel, "HASH MISMATCH")); bad += 1
                continue
            entry = {"sha256": h, "bytes": dest.stat().st_size,
                     "source": (RAW.format(commit=reg["google_fonts_commit"], gf_dir=fb["gf_dir"], name=Path(rel).name)
                                if fb.get("gf_dir") else "https://github.com/rsms/inter (via motion kit)"),
                     "license": "SIL OFL 1.1"}
            if not rel.endswith(".txt"):
                try:
                    fam = family_of(dest)
                except Exception as e:
                    report.append((key, rel, f"NOT A FONT ({e})")); bad += 1
                    dest.unlink(missing_ok=True)
                    continue
                entry["family"] = fam
                if not fam.casefold().startswith(fb["family"].casefold()):   # "Inter Variable" is Inter
                    report.append((key, rel, f"FAMILY MISMATCH: file says {fam!r}, registry {fb['family']!r}")); bad += 1
                    continue
            manifest[rel] = entry
            report.append((key, rel, status))
    man_p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for key, rel, st in report:
        print(f"{key:22} {rel:58} {st}")
    print(f"\n{len(report) - bad} ok, {bad} problems. Manifest: {man_p}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

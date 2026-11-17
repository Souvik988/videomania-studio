"""Rebrand the OpenFilm source as OpsGen (idempotent). OpsGen is a fork of OpenFilm (MIT, Copyright (c) 2026 OpenFilm
contributors); the MIT notice is kept, links to the OpenFilm project stay pointing at it, and the OpenFilm name/logo
are replaced as its TRADEMARK.md asks of a fork published under its own name.

    python scripts/rebrand.py            (run from the opsgen folder)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = {".mjs", ".js", ".cjs", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".yaml", ".yml", ".txt", ".sh"}
SKIP_DIRS = {"node_modules", ".git", "dist", "out", ".film"}
KEEP_FILES = {"LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "UPSTREAM_COMMIT.txt", "NOTICE.md", "rebrand.py",
              "TRADEMARK.md", "OPSGEN.md", "opsgen-dev.sh",
              "subtitle-segments.test.mjs", "captions.test.mjs"}   # tests whose expected numbers depend on the sample word's length   # OpsGen's own files name OpenFilm on purpose

# links and addresses that must keep pointing at the OpenFilm project / service
PROTECT = [r"https?://[^\s)\"'`>]*openfilm[^\s)\"'`>]*", r"openfilm\.dev[^\s)\"'`>]*", r"github\.com/openfilm[^\s)\"'`>]*",
           r"support@openfilm\.dev"]

REPL = [
    ("@openfilm/", "@opsgen/"),
    ("OPENFILM_", "OPSGEN_"),
    ("npx -y openfilm@latest", "opsgen"),
    ("openfilm@latest", "opsgen"),
    ('"openfilm": "workspace:', '"opsgen": "workspace:'),
    ('"name": "openfilm"', '"name": "opsgen"'),
    ('"openfilm": "bin/openfilm.mjs"', '"opsgen": "bin/opsgen.mjs"'),
    ("bin/openfilm.mjs", "bin/opsgen.mjs"),
    ("from 'openfilm/", "from 'opsgen/"),
    ('from "openfilm/', 'from "opsgen/'),
    ("import('openfilm/", "import('opsgen/"),
    ("from 'openfilm'", "from 'opsgen'"),
    ('from "openfilm"', 'from "opsgen"'),
    ("openfilm-monorepo", "opsgen-monorepo"),
    ("node_modules/openfilm/", "node_modules/opsgen/"),            # Tailwind @source and other paths into the package
    (".bin.openfilm", ".bin.opsgen"),                    # the desktop reads the CLI entry from package.json
    ("'openfilm.cmd'", "'opsgen.cmd'"),                # the agents' command shim on Windows
    ("`${bin}/openfilm`", "`${bin}/opsgen`"),
    ("join(bin, 'openfilm')", "join(bin, 'opsgen')"),
    ("OpenFilm", "OpsGen"),
    ("OPENFILM", "OPSGEN"),
]
CLI_WORD = re.compile(r"(?<![\w./@-])openfilm(?=\s+(open|look|render|get|canvas|skills?|doctor|help|--)\b)")


def rebrand(text: str) -> str:
    saved = []

    def keep(m):
        saved.append(m.group(0))
        return f"\u0000{len(saved) - 1}\u0000"

    for pat in PROTECT:
        text = re.sub(pat, keep, text)
    for a, b in REPL:
        text = text.replace(a, b)
    text = CLI_WORD.sub("opsgen", text)
    # the data folder (~/.openfilm, '.openfilm'), never a property (x.openfilmNative)
    text = re.sub(r"(?<![A-Za-z0-9_)\]])\.openfilm\b", ".opsgen", text)
    # module specifiers in require / resolve / import calls (library ids like 'openfilm/transitions/x' stay)
    text = re.sub(r"((?:require|resolve|import)\(\s*['\"])openfilm(?=['\"/])", lambda m: m.group(1) + "opsgen", text)
    text = text.replace("'openfilm/package.json'", "'opsgen/package.json'").replace("'openfilm/skills-cli'", "'opsgen/skills-cli'")
    # the command name handed to skillCommand(...) / asRun(...) in code and tests
    text = re.sub(r"((?:skillCommand|asRun)\([^;\n]*?,\s*)'openfilm'", lambda m: m.group(1) + "'opsgen'", text)
    # the package's own export paths, wherever quoted (CSS @import, require, import): 'openfilm/studio-ui/...' etc.
    text = re.sub(r"""(['"`])openfilm/(film-doc|host|shared|look|render|problems|skills-cli|skills|studio-ui|studio|desktop-account|package\.json)""",
                  lambda m: m.group(1) + "opsgen/" + m.group(2), text)
    return re.sub("\u0000(\\d+)\u0000", lambda m: saved[int(m.group(1))], text)


def main():
    changed = 0
    for p in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts) or not p.is_file() or p.name in KEEP_FILES:
            continue
        if p.suffix.lower() not in EXT and p.name != "pnpm-lock.yaml":
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        n = rebrand(t)
        if n != t:
            p.write_text(n, encoding="utf-8")
            changed += 1
    # files named after the brand (imports were renamed above, so the files must follow)
    for f in sorted(ROOT.rglob("*OpenFilm*"), key=lambda x: -len(x.parts)):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        f.rename(f.with_name(f.name.replace("OpenFilm", "OpsGen")))
    # the CLI entry file
    old = ROOT / "packages" / "openfilm" / "bin" / "openfilm.mjs"
    if old.exists():
        old.rename(old.with_name("opsgen.mjs"))
    print(f"rebranded {changed} files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""No credential may reach a public repository. This one is public.

Written 27 September 2026, the hour a Trove API key arrived. The key lives in
.env, which is gitignored — but «it is in the gitignored file» is a fact about
today's arrangement, not a control. A key pasted into a note, a tool, a commit
message or a data file would be published to GitHub Pages within a minute of
the next push, and revoking it afterwards does not un-publish it.

So this reads what git ACTUALLY TRACKS and refuses if a credential is in it.
Tracked files only: .env is ignored and is supposed to hold the key, and
scanning the working tree would report it every run until somebody turned the
check off.
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outdir

outdir.strict_argv()   # a flag this gate does not take is an error, not a no-op

# Shapes, not values. A pattern carrying the real key would put the key in this
# file, which is the thing being prevented.
PATTERNS = [
    ("Trove API key", re.compile(r"\bTROVE_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9]{20,}")),
    ("a bare 32-char key beside the word trove",
     re.compile(r"(?i)trove[^\n]{0,40}\b[A-Za-z0-9]{32}\b")),
    ("an Authorization header with a literal token",
     re.compile(r"(?i)authorization\s*[:=]\s*['\"]?(bearer|basic)\s+[A-Za-z0-9._\-]{16,}")),
    ("X-API-KEY with a literal value",
     re.compile(r"(?i)x-api-key['\"]?\s*[:=]\s*['\"][A-Za-z0-9._\-]{16,}['\"]")),
]

SKIP = ("tools/check_secrets.py",)


def main():
    try:
        files = subprocess.run(["git", "ls-files", "-z"], capture_output=True,
                               text=True, check=True).stdout.split("\0")
    except Exception as e:
        print(f"  FAIL  secrets    cannot list tracked files — {e}")
        return 1
    files = [f for f in files if f and f not in SKIP]
    hits = []
    for f in files:
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for what, pat in PATTERNS:
            m = pat.search(txt)
            if m:
                line = txt[:m.start()].count("\n") + 1
                hits.append((f, line, what))
    if hits:
        for f, line, what in hits:
            print(f"  FAIL  secrets    {f}:{line} looks like {what}")
        print("          A credential in a tracked file is published on the next push and")
        print("          cannot be unpublished. Move it to .env, which is gitignored, and")
        print("          treat the exposed one as burnt: revoke and reissue it.")
        return 1
    print(f"  ok    secrets    {len(files)} tracked file(s) carry no credential")
    return 0


if __name__ == "__main__":
    sys.exit(main())

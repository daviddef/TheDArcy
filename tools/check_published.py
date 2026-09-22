#!/usr/bin/env python3
"""Has everything this archive researched actually reached the site?

Research is worth nothing to a reader if it stops in a data file. Three ways
that happens, and this checks all three:

  ORPHAN   a data file under site/src/data that no page imports. The research
           is written, committed, and invisible.
  DANGLING a row in searched.json, errands.json, coverage.json or questions.json
           whose `href` points at a page that is not built. The finding exists
           and its own signpost is broken.
  SILENT   a row whose href resolves, but whose subject cannot be found anywhere
           on that page. The signpost points at the right building and the thing
           is not inside it.

The third is the interesting one and the hardest to satisfy honestly, so it is
deliberately loose: it looks for a distinctive proper noun or reference from the
row's own text. A miss is reported as a warning, not a failure, because prose is
allowed to say a thing in its own words.

    python3 tools/check_published.py            # exits 1 on orphans or dangles
    python3 tools/check_published.py --warn     # always exits 0
"""
import json, os, re, sys, collections
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import outdir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")
SRC = os.path.join(ROOT, "site", "src")
DIST = outdir.out()

fails, warns = [], []


def built_pages():
    out = set()
    for r, _, fs in os.walk(DIST):
        for f in fs:
            if f == "index.html":
                p = "/" + os.path.relpath(r, DIST).replace(os.sep, "/")
                out.add("/" if p == "/." else p)
    return out


def imported_data():
    """Every data file named anywhere in src/ or tools/."""
    seen = set()
    for base in (SRC, os.path.join(ROOT, "tools")):
        for r, _, fs in os.walk(base):
            if "node_modules" in r:
                continue
            for f in fs:
                if not f.endswith((".astro", ".js", ".ts", ".py", ".mjs")):
                    continue
                txt = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
                for m in re.finditer(r'([a-z0-9\-]+)\.json', txt):
                    seen.add(m.group(1) + ".json")
    return seen


def main():
    warn_only = "--warn" in sys.argv
    pages = built_pages()
    if len(pages) < 400:
        print("  FAIL  published  site/dist looks unbuilt — nothing to check against")
        return 1

    # ── ORPHAN ──────────────────────────────────────────────────────────────
    used = imported_data()
    files = [f for f in sorted(os.listdir(DATA)) if f.endswith(".json")]
    for f in files:
        if f not in used:
            fails.append(("ORPHAN", f"site/src/data/{f} is imported by nothing — research nobody can read"))

    # ── DANGLING and SILENT ─────────────────────────────────────────────────
    SOURCES = {
        "searched.json": ("rows", "href", ("src", "what", "got")),
        "errands.json": ("rows", "href", ("what", "where", "settles")),
        "coverage.json": ("rows", "href", ("db", "where", "note")),
        "questions.json": ("rows", "href", ("q", "note")),
    }
    checked = 0
    for fn, (key, hkey, textkeys) in SOURCES.items():
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        rows = d.get(key, d) if isinstance(d, dict) else d
        for row in rows:
            if not isinstance(row, dict):
                continue
            href = (row.get(hkey) or "").split("#")[0].split("?")[0].rstrip("/")
            if not href:
                continue
            checked += 1
            if href not in pages:
                fails.append(("DANGLING", f"{fn}: href {href!r} is not a built page "
                                          f"— {str(row.get(textkeys[0]))[:60]}"))
                continue
            # SILENT: does the page carry a distinctive token from the row?
            #
            # THE FIRST VERSION OF THIS CERTIFIED A ROW BECAUSE A PAGE SAID
            # "WALES". Tokens were collected in the order they appeared, which
            # put the SOURCE'S OWN NAME first — "the National Library of Wales"
            # — and the test was `any(t in page for t in toks[:6])`. So a row
            # about Edward Sanniger's will, carrying the references IR
            # 26/352/152 and LL/1806/24, passed on the word Wales appearing once
            # on a page about spellings, and the will reached no page at all for
            # two days. A check that can pass for a reason unrelated to the
            # thing it is checking.
            #
            # So the finding is asked first and the references before the prose.
            # `got` is what was found; `src` is only where it was looked for.
            found_blob = str(row.get(textkeys[-1]) or "")
            where_blob = " ".join(str(row.get(k) or "") for k in textkeys[:-1])
            PAT = r"\b([A-Z][A-Za-z']{4,}|[A-Z]{2,}\s?\d+/\d+[\w/]*)\b"
            STOP = ("findmypast", "discovery", "archives", "archive", "england",
                    "gloucestershire", "national", "record", "records", "library",
                    "wales", "ireland", "scotland", "britain", "british",
                    "nothing", "control", "proved", "november", "october",
                    "september", "january", "february", "december")

            # AND STRIP THE POSSESSIVE, because "D'Arcy's" cannot match a page
            # that says "D'Arcy" and the row is not thereby unpublished. Five of
            # the eleven this test flagged on its first strengthened run were
            # possessives — the fix for a test passing for the wrong reason,
            # failing for one.
            def rank(ts):
                ts = [re.sub(r"'s$", "", t) for t in ts]
                refs = [t for t in ts if any(c.isdigit() for c in t)]
                caps = [t for t in ts if t.isupper() and t not in refs]
                rest = [t for t in ts if t not in refs and t not in caps]
                out = []
                for t in refs + caps + rest:
                    if t.lower() not in STOP and t not in out:
                        out.append(t)
                return out

            toks = rank(re.findall(PAT, found_blob)) or rank(re.findall(PAT, where_blob))
            if not toks:
                continue
            f = os.path.join(DIST, href.lstrip("/"), "index.html")
            if not os.path.exists(f):
                continue
            page = re.sub(r"<[^>]+>", " ", open(f, encoding="utf-8", errors="ignore").read())
            if not any(t.lower() in page.lower() for t in toks[:6]):
                warns.append(("SILENT", f"{fn}: {href} carries none of {toks[:3]} "
                                        f"— {str(row.get(textkeys[0]))[:50]}"))

    o = sum(1 for s, _ in fails if s == "ORPHAN")
    dg = sum(1 for s, _ in fails if s == "DANGLING")
    print(f"  {'ok  ' if not fails else 'FAIL'}  published  {len(files)} data file(s), "
          f"{checked} signpost(s) checked · {o} orphan(s), {dg} dangling, {len(warns)} quiet")
    for s, w in fails[:25]:
        print(f"   FAIL {s:9} {w}")
    for s, w in warns[:12]:
        print(f"   warn {s:9} {w}")
    if len(warns) > 12:
        print(f"   … and {len(warns) - 12} more quiet signposts")
    return 0 if (warn_only or not fails) else 1


if __name__ == "__main__":
    sys.exit(main())

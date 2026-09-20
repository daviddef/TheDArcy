#!/usr/bin/env python3
"""A withdrawn reading, stated again as fact.

An archive that publishes its own errors acquires a hazard peculiar to itself:
the retracted wording is still in the building. It sits on /corrections in
quotation marks, and it sits in every dated log that recorded it — and from
there it gets copied into new prose by somebody who read it and did not notice
the retraction around it.

This is checkable where a general prose gate is not, because A RETIRED PHRASE IS
THIS ARCHIVE'S OWN WORDING AND NEVER A DOCUMENT'S. Nobody quotes a source saying
"a blank of twenty-four years". If the string is on a page, this archive put it
there.

WHAT IT MUST NOT DO, and this is the larger half. Dated logs — the work list,
the searched register, the change log, the errands — record what was believed on
a day. They are evidence about this archive's own history and MUST NOT be edited
when the belief changes; a log rewritten to agree with a later finding is the
exact failure the method exists against. So those paths are allowed, and the
allowance is the point rather than a loophole.

    python3 tools/check_retired.py          # exits 1 on a retired phrase in live prose
    python3 tools/check_retired.py --warn   # report only
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "site", "dist")
CFG = os.path.join(ROOT, "site", "src", "data", "retired.json")
SCRIPTS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def main():
    warn = "--warn" in sys.argv
    cfg = json.load(open(CFG, encoding="utf-8"))
    allow = tuple(cfg["allow"])
    retired = cfg["retired"]

    pages = 0
    hits = []
    for r, _, fs in os.walk(DIST):
        for f in fs:
            if f != "index.html":
                continue
            page = "/" + os.path.relpath(r, DIST).replace(os.sep, "/")
            page = "/" if page == "/." else page
            pages += 1
            if page.rstrip("/") in allow or any(page.startswith(a + "/") for a in allow):
                continue
            raw = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
            text = html.unescape(re.sub(r"<[^>]+>", " ", SCRIPTS.sub(" ", raw)))
            text = re.sub(r"\s+", " ", text)
            low = text.lower()
            spans = []
            for op, cl in (("\u00ab", "\u00bb"), ("\u201c", "\u201d"), ('"', '"')):
                pos = 0
                while True:
                    a = text.find(op, pos)
                    if a < 0:
                        break
                    b = text.find(cl, a + 1)
                    if b < 0:
                        break
                    spans.append((a, b))
                    pos = b + 1
            for e in retired:
                ph = e["phrase"].lower()
                start = 0
                while True:
                    i = low.find(ph, start)
                    if i < 0:
                        break
                    start = i + 1
                    # QUOTED IS NOT ASSERTED. This archive's rule is that an
                    # error stays on the page where it was made, so a retired
                    # phrase is SUPPOSED to appear in live prose — inside the
                    # sentence that withdraws it. A quoted occurrence is the
                    # rule working, not a breach of it.
                    #
                    # Containment, not adjacency: the first version tested the
                    # two characters either side and missed «not published at
                    # all — absent from the build», where the closing quote is
                    # nine words further on. A quotation is a SPAN.
                    if any(a < i and i + len(ph) <= b for a, b in spans):
                        continue
                    hits.append((page, e))
                    break

    if pages < 400:
        print(f"  FAIL  retired    only {pages} pages in dist — nothing was really checked")
        return 1
    print(f"  {'ok  ' if not hits else 'FAIL'}  retired    "
          f"{len(retired)} withdrawn reading(s) checked against {pages} pages "
          f"({len(allow)} log paths allowed) — {len(hits)} restated")
    for page, e in hits[:20]:
        print(f"   RESTATED {page}  «{e['phrase']}»")
        print(f"            own error {e['err']} — {e['instead']}")
    return 0 if (warn or not hits) else 1


if __name__ == "__main__":
    sys.exit(main())

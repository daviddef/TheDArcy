#!/usr/bin/env python3
"""Does every chart box say what the page it links to says?

Written 16 October 2026 after /tree drew William Hartley Sneyd as 1838–1902 for
weeks while his own page, one click away, said 1837–1902.

THE CAUSE WAS NOT CARELESSNESS, IT WAS TWO SOURCES. This archive keeps a
corrections map (lib/corrections.js) for the places where its own research has
overturned the family tree, and the person pages read it. The chart is drawn by
the shared kit's ahnen(), which builds a box straight from the tree row and
knows nothing of that map. Both were right by their own lights and they
disagreed in public. A second case turned up in the same pass: James Wakefield
was drawn 1799–1857 with a wall reading «No parents are recorded», though five
records put his birth in 1806 and one of them names both parents.

No gate saw either, because every gate reads ONE source. The comparison that
catches this is between two OUTPUTS, so this reads only the built HTML: for
each box on a chart that links to a person page, the years in the box must be
the years that page prints. It never asks which is right — that is a research
question — only whether the archive agrees with itself.

A check that examined nothing must not pass: it prints how many boxes it
compared and refuses at zero.
"""
import os, re, sys, glob, html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(os.path.dirname(HERE), "site", _o) if _o else os.path.join(os.path.dirname(HERE), "site", "dist")

BOX = re.compile(r'<a href="/people/([a-z0-9-]+)/">[^<]*</a>\s*</div>\s*<div class="ac-m">\s*'
                 r'<span class="ac-d">([^<]*)</span>')
H1 = re.compile(r"<h1[^>]*>")
YEARS = re.compile(r"(\d{4}\s*[–-]\s*\d{4}|\d{4}\s*[–-]|b\.\s*\d{4}|d\.\s*\d{4})")


def norm(x):
    return re.sub(r"\s", "", html.unescape(x).replace("b.", "").replace("d.", ""))


def page_years(slug):
    f = os.path.join(DIST, "people", slug, "index.html")
    if not os.path.exists(f):
        return None
    s = open(f, encoding="utf-8", errors="ignore").read()
    m = H1.search(s)
    if not m:
        return None
    # the lifespan is printed in the eyebrow immediately above the heading
    found = YEARS.findall(re.sub(r"<[^>]+>", " ", s[max(0, m.start() - 400):m.start()]))
    return found[-1] if found else None


def main():
    pages = [f for f in glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)]
    if not pages:
        print(f"  FAIL  chartyears no built pages under {DIST} — nothing was examined")
        return 1
    compared, bad = 0, []
    for f in sorted(pages):
        s = open(f, encoding="utf-8", errors="ignore").read()
        if "ac-box" not in s:
            continue
        where = os.path.relpath(f, DIST).replace("/index.html", "") or "/"
        for slug, chart in BOX.findall(s):
            ph = page_years(slug)
            if ph is None:
                continue          # no lifespan printed there: nothing to compare against
            compared += 1
            if norm(chart) != norm(ph):
                bad.append((where, slug, html.unescape(chart).strip(), ph))
    if compared == 0:
        print("  FAIL  chartyears no chart box could be compared with a person page — the "
              "markup this reads has changed, or no chart was built, and that is this gate "
              "failing and not the archive passing")
        return 1
    if bad:
        print(f"  FAIL  chartyears {len(bad)} of {compared} chart box(es) disagree with the page they link to")
        for w, slug, c, p in bad[:6]:
            print(f"          /{w}: {slug} — chart says {c!r}, the page says {p!r}")
        print("          lib/corrections.js is what the person pages read; the chart must read it too.")
        return 1
    print(f"  ok    chartyears {compared} chart box(es) carry the same years as the page they link to")
    return 0


if __name__ == "__main__":
    sys.exit(main())

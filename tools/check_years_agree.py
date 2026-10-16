#!/usr/bin/env python3
"""Does every page that prints a person's years print the years THEIR page prints?

Written 16 October 2026, and rewritten the same day. It began as a check on one
chart (check_chart_years.py) after /tree drew William Hartley Sneyd as 1838–1902
for weeks while his own page said 1837–1902. Fixing the chart and looking again
found the SAME fault in six more places, which is the real finding: this archive
keeps a corrections map (lib/corrections.js) for where its research overturned
the family tree, and every page that prints a lifespan has to remember to read
it. Person pages did. Pedigree cards did. The chart, /people, /bloodline,
/register, /graves, /sneyd and /families did not. Patching renderers one at a
time is how it recurred; this refuses the whole class.

IT READS ONLY THE BUILT HTML, because the fault lives between two readers of one
fact and no gate that reads one source can see it. For every link to a person
page, anywhere on the site, followed by a lifespan — either just after the link
or inside it, which is how a card is built — the years must be the years that
person's own page prints. It never asks which is right. That is a research
question. It asks only whether the archive agrees with itself.

THREE THINGS IT DOES NOT DO, SAID PLAINLY. It cannot see /bloodline, which embeds its
data as JSON for the browser and prints no person links to compare; that page was fixed
and checked by hand, and a regression there would pass this gate. It compares only a full «YYYY–YYYY»;
a «b. 1814» or a lone death year is not checked. And it compares what is
printed beside a LINK, so a lifespan in running prose that happens to name
somebody is not seen — which is also why /changes and /corrections can quote the
tree's old year, on purpose, without tripping it.

A check that examined nothing must not pass. It prints how many links it
compared, refuses at zero, and separately refuses if it compared no chart box,
because the chart was the first place this was found and a markup change there
must not silently drop it out of the count.
"""
import os, re, sys, glob, html, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(os.path.dirname(HERE), "site", _o) if _o else os.path.join(os.path.dirname(HERE), "site", "dist")

Y = r"(\d{4}\s*[–-]\s*\d{4})"
H1 = re.compile(r"<h1[^>]*>")
LINK = re.compile(r'<a [^>]*href="/people/([a-z0-9-]+)/?"[^>]*>(.*?)</a>(.{0,170})', re.S)
CHART_BOX = re.compile(r'<span class="ac-d">')


def norm(x):
    return re.sub(r"\s", "", html.unescape(x)).replace("-", "–")


def read(f):
    return open(f, encoding="utf-8", errors="ignore").read()


def truth():
    """slug -> the years that person's own page prints, from its eyebrow."""
    t = {}
    for f in glob.glob(os.path.join(DIST, "people", "*", "index.html")):
        slug = f.split(os.sep)[-2]
        s = read(f)
        m = H1.search(s)
        if not m:
            continue
        head = re.sub(r"<[^>]+>", " ", s[max(0, m.start() - 400):m.start()])
        ys = re.findall(Y, head)
        if ys:
            t[slug] = norm(ys[-1])
    return t


def main():
    pages = glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)
    if not pages:
        print(f"  FAIL  years      no built pages under {DIST} — nothing was examined")
        return 1
    tr = truth()
    if not tr:
        print("  FAIL  years      no person page prints a lifespan in the eyebrow — the markup this "
              "reads has changed, so nothing can be compared")
        return 1
    compared = chart = 0
    bad = collections.defaultdict(set)
    for f in pages:
        page = os.path.relpath(f, DIST).replace(os.sep, "/").replace("/index.html", "") or "/"
        s = read(f)
        # the correction box prints the tree's year on purpose, beside the finding
        s = re.sub(r"Corrected against the family tree.*?Set out in full", "", s, flags=re.S)
        on_chart = bool(CHART_BOX.search(s))
        for m in LINK.finditer(s):
            slug = m.group(1)
            if slug not in tr:
                continue
            inner = re.sub(r"<[^>]+>", " ", m.group(2))
            after = re.sub(r"<[^>]+>", " ", m.group(3))
            mm = re.search(Y, inner) or re.match(r"\s*[·|(\[]?\s*" + Y, after)
            if not mm:
                continue
            compared += 1
            if on_chart:
                chart += 1
            if norm(mm.group(1)) != tr[slug]:
                grp = page if not page.startswith("people/") else "people/*"
                bad[(grp, slug, norm(mm.group(1)), tr[slug])].add(page)
    if compared == 0:
        print("  FAIL  years      no person link followed by a lifespan could be compared — the "
              "markup has changed, or nothing was built, and that is this gate failing and not the "
              "archive passing")
        return 1
    if chart == 0:
        print("  FAIL  years      links were compared but none on a chart — the chart's markup "
              "(ac-d) has changed, so the first place this fault was found is no longer being read")
        return 1
    if bad:
        print(f"  FAIL  years      {len(bad)} place(s) print a lifespan that the linked person's own page contradicts")
        for (grp, slug, shown, page_says), where in sorted(bad.items())[:8]:
            print(f"          /{grp}: {slug} — prints {shown!r}, the page says {page_says!r} ({len(where)} page(s))")
        print("          lib/corrections.js is what the person pages read; whatever prints a lifespan must too.")
        return 1
    print(f"  ok    years      {compared} person link(s) with a lifespan, {chart} of them on a chart, all "
          f"carry the years the linked page carries")
    return 0


if __name__ == "__main__":
    sys.exit(main())

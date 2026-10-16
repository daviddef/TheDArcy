#!/usr/bin/env python3
"""Does every confirmed cross-archive pair show its pointer on this archive's page, and nobody else?

Written 16 October 2026. The kit keeps the list of people documented in two archives
(kit/data/cross-archive.json) and draws «Also documented in the Falco archive» for a pair
marked CONFIRMED. The component is silent for everything else, which is exactly why this
reads the BUILT page: a template that forgets to pass `archive` or `path` renders nothing,
says nothing, and every gate that reads the source or the list sees a correct input.
Nothing else can tell «no pointer because there is no confirmed pair» from «no pointer
because the prop never arrived».

It checks both directions, because a rule checked one way drifts the other:
  - every CONFIRMED pair with a D'Arcy page: that page carries the pointer, and it links
    to the other archive's page at the address the ring gives
  - no OTHER page carries one, and above all no LIVING page does: a living page is a
    name, relationships and a place, and a pointer to another archive is none of those

Only the dead are compared by name; nothing here prints a living person.
"""
import os, re, sys, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(ROOT, "site", _o) if _o else os.path.join(ROOT, "site", "dist")

KIT = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "data")
ME = "darcy"
ALSO = re.compile(r'data-also-in="(\d+)"')
HREF = re.compile(r'data-also-in[^>]*>(.*?)</p>', re.S)


def read(f):
    return open(f, encoding="utf-8", errors="ignore").read()


def main():
    try:
        pairs = json.load(open(os.path.join(KIT, "cross-archive.json"), encoding="utf-8"))["pairs"]
        ring = {a["key"]: a for a in json.load(open(os.path.join(KIT, "archives.json"), encoding="utf-8"))["archives"]}
    except Exception as e:
        print(f"  FAIL  alsoin     cannot read the kit's cross-archive data: {e}")
        return 1
    pages = glob.glob(os.path.join(DIST, "people", "*", "index.html"))
    if not pages:
        print(f"  FAIL  alsoin     no built person pages under {DIST} — nothing was examined")
        return 1

    expect = {}                                  # my path -> [expected hrefs]
    for p in pairs:
        if p.get("status") != "confirmed":
            continue
        mine, other = (p["a"], p["b"]) if p["a"]["archive"] == ME else (p["b"], p["a"]) if p["b"]["archive"] == ME else (None, None)
        if not mine or other["archive"] not in ring:
            continue
        expect.setdefault(mine["path"], []).append(ring[other["archive"]]["url"].rstrip("/") + other["path"])

    fails, shown = [], 0
    for path, hrefs in expect.items():
        f = os.path.join(DIST, path.strip("/"), "index.html")
        if not os.path.exists(f):
            fails.append(f"{path} has a confirmed pair and no built page")
            continue
        html = read(f)
        if 'name="robots" content="noindex"' in html:
            # THE TEMPLATE IS RIGHT AND THE LIST IS WRONG. A living page never gets a pointer, so
            # if the kit confirms a pair that names one, the page correctly shows nothing and a bare
            # "no pointer" finding would blame the template for the kit's mistake. Say which it is.
            fails.append(f"{path} is a LIVING person's page and a confirmed pair names it; a pointer is never "
                         f"drawn for the living, so the kit's cross-archive list should not hold this pair")
            continue
        m = ALSO.search(html)
        if not m:
            fails.append(f"{path} has a confirmed pair and the page carries no pointer — the template is not passing its props")
            continue
        shown += 1
        body = HREF.search(html).group(1) if HREF.search(html) else ""
        for h in hrefs:
            if h not in body:
                fails.append(f"{path} points somewhere other than {h}")
        if int(m.group(1)) != len(hrefs):
            fails.append(f"{path} draws {m.group(1)} pointer(s) and {len(hrefs)} pair(s) are confirmed")

    stray = living_hits = 0
    for f in pages:
        slug = f.split(os.sep)[-2]
        path = f"/people/{slug}/"
        html = read(f)
        if ALSO.search(html) and path not in expect:
            stray += 1
            fails.append(f"{path} carries a pointer and no confirmed pair names it")
        if ALSO.search(html) and 'name="robots" content="noindex"' in html:
            living_hits += 1
            fails.append(f"{path} is a LIVING page and carries a pointer to another archive")

    if fails:
        print(f"  FAIL  alsoin     {len(fails)} finding(s) across {len(pages)} person page(s)")
        for m in fails[:6]:
            print(f"          {m}")
        return 1
    if not expect:
        print(f"  ok    alsoin     no confirmed pair involves this archive, so no page may carry a pointer, and none does "
              f"({len(pages)} checked)")
        return 0
    print(f"  ok    alsoin     {shown} of {len(expect)} confirmed pair(s) show their pointer on this archive's page, to the "
          f"address the ring gives; no other page and no living page carries one ({len(pages)} checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

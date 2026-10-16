#!/usr/bin/env python3
"""Do the declared duplicates behave as declared, and ONLY those?

Written 16 October 2026, with the mechanism it checks. site/src/data/same-person.json
declares pairs of tree people who are one person entered twice. A COPY keeps its
address (an address that has been published may have been written down), says it is
the same person, names the primary as its canonical, and is left out of the sitemap
and the search index. The PRIMARY is untouched.

A DECLARATION IS A CLAIM THAT NOTHING ELSE VERIFIES, so this reads it against the
built site, and every clause below can be made to fail:

  - the file declares something (a gate with nothing to check cannot fail)
  - every declared id is a person who has a built page
  - no id is declared twice, and nobody is their own copy: a chain of declarations
    would send a reader and a crawler round in a circle
  - a copy's page carries the notice and a canonical naming exactly its primary
  - a primary's page carries neither the notice nor a canonical naming another page
  - a copy is in NEITHER the sitemap nor the search index, and a primary is in BOTH,
    because declaring a duplicate must never delete the person from the index
  - NO OTHER PAGE names a canonical other than itself. The layout now lets a page
    pass one, so the same door that serves a declared copy would serve a mistake.

It reads ONLY the built HTML and the committed data, never the GEDCOM, so it runs
wherever the build does. It does not judge whether two people are the same person;
that is research, and the declaration's own `why` is where it is argued.
"""
import os, re, sys, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import slugrule
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(ROOT, "site", _o) if _o else os.path.join(ROOT, "site", "dist")

DECL = os.path.join(ROOT, "site", "src", "data", "same-person.json")
CANON = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
NOTICE = re.compile(r'data-same-person=["\']([^"\']+)["\']')


def read(f):
    return open(f, encoding="utf-8", errors="ignore").read()


def origin():
    m = re.search(r"\bsite:\s*['\"]([^'\"]+)['\"]", read(os.path.join(ROOT, "site", "astro.config.mjs")))
    return (m.group(1) if m else "").rstrip("/")


def main():
    try:
        pairs = json.load(open(DECL, encoding="utf-8")).get("pairs", [])
    except Exception as e:
        print(f"  FAIL  sameperson cannot read {DECL}: {e}")
        return 1
    if not pairs:
        print("  FAIL  sameperson the declaration file declares nothing — a gate with nothing to check "
              "cannot fail, so this is the file being emptied or unread and not the archive being clean")
        return 1
    pages = glob.glob(os.path.join(DIST, "people", "*", "index.html"))
    if not pages:
        print(f"  FAIL  sameperson no built person pages under {DIST} — nothing was examined")
        return 1

    fails = []
    sl = slugrule.slugs()                      # tree id -> page slug, from committed data
    site = origin()

    # ids: exist, once each, never their own copy
    seen = collections.Counter()
    for x in pairs:
        seen[x["copy"]] += 1
        seen[x["primary"]] += 1
        if x["copy"] == x["primary"]:
            fails.append(f"{x['copy']} is declared the copy of itself")
        for role in ("copy", "primary"):
            if x[role] not in sl:
                fails.append(f"the declared {role} {x[role]} is not a person with a page in this archive")
            elif not os.path.exists(os.path.join(DIST, "people", sl[x[role]], "index.html")):
                fails.append(f"the declared {role} {x[role]} should have /people/{sl[x[role]]}/ and it is not built")
    for i, n in seen.items():
        if n > 1:
            fails.append(f"{i} is declared {n} times; each id may appear once, or the declarations form a chain")

    sitemap = read(os.path.join(DIST, "sitemap.xml")) if os.path.exists(os.path.join(DIST, "sitemap.xml")) else ""
    locs = {l.rstrip("/") for l in re.findall(r"<loc>([^<]*)</loc>", sitemap)}
    try:
        search = json.load(open(os.path.join(DIST, "searchindex.json"), encoding="utf-8"))
        search = search if isinstance(search, list) else search.get("entries", [])
    except Exception:
        search = []
    in_search = {m.group(1) for r in search if isinstance(r, dict)
                 for m in [re.search(r"/people/([^/?#]+)", r.get("h") or "")] if m}

    copies, primaries = set(), set()
    for x in pairs:
        if x["copy"] not in sl or x["primary"] not in sl:
            continue
        cs, ps = sl[x["copy"]], sl[x["primary"]]
        copies.add(cs); primaries.add(ps)
        cf = os.path.join(DIST, "people", cs, "index.html")
        pf = os.path.join(DIST, "people", ps, "index.html")
        if not (os.path.exists(cf) and os.path.exists(pf)):
            continue
        c, p = read(cf), read(pf)
        want = f"{site}/people/{ps}/"
        # the copy
        n = NOTICE.search(c)
        if not n or n.group(1) != ps:
            fails.append(f"/people/{cs}/ is a declared copy and does not carry the notice naming {ps}")
        cc = CANON.search(c)
        if not cc or cc.group(1) != want:
            fails.append(f"/people/{cs}/ is a declared copy and its canonical is {cc.group(1) if cc else 'absent'}, not {want}")
        if f"{site}/people/{cs}".rstrip("/") in locs:
            fails.append(f"/people/{cs}/ is a declared copy and is in the sitemap")
        if cs in in_search:
            fails.append(f"/people/{cs}/ is a declared copy and is in the search index")
        # the primary
        if NOTICE.search(p):
            fails.append(f"/people/{ps}/ is a primary and carries the duplicate notice")
        pc = CANON.search(p)
        if pc and pc.group(1) != want:
            fails.append(f"/people/{ps}/ is a primary and its canonical names {pc.group(1)}")
        if f"{site}/people/{ps}".rstrip("/") not in locs:
            fails.append(f"/people/{ps}/ is a primary and is NOT in the sitemap: declaring a duplicate removed the person")
        if ps not in in_search:
            fails.append(f"/people/{ps}/ is a primary and is NOT in the search index: declaring a duplicate removed the person")

    # nobody else may name a foreign canonical
    stray = 0
    for f in pages:
        slug = f.split(os.sep)[-2]
        if slug in copies:
            continue
        cc = CANON.search(read(f))
        if cc and cc.group(1).rstrip("/") != f"{site}/people/{slug}":
            stray += 1
            fails.append(f"/people/{slug}/ is not a declared copy and its canonical names {cc.group(1)}")

    if fails:
        print(f"  FAIL  sameperson {len(fails)} finding(s) against {len(pairs)} declared pair(s)")
        for m in fails[:8]:
            print(f"          {m}")
        return 1
    print(f"  ok    sameperson {len(pairs)} pair(s): every id has a page and is declared once; {len(copies)} "
          f"cop{'y' if len(copies)==1 else 'ies'} carry the notice and a canonical to the primary and are in "
          f"neither sitemap nor search; {len(primaries)} primar{'y' if len(primaries)==1 else 'ies'} carry neither "
          f"and are in both; no other page names a foreign canonical ({len(pages)} checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

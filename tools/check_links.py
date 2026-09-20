#!/usr/bin/env python3
"""Every internal href in the built site, resolved. Exits non-zero on a break."""
import os, re, sys, html as _html, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "dist")
BASE = "/TheDArcy"

have = set()
for r, _, fs in os.walk(D):
    for f in fs:
        p = "/" + os.path.relpath(os.path.join(r, f), D).replace(os.sep, "/")
        have.add(p)
        if f == "index.html":
            have.add(p[:-len("index.html")].rstrip("/") or "/")

bad, pages = collections.Counter(), 0
where = collections.defaultdict(set)
for r, _, fs in os.walk(D):
    for f in fs:
        if not f.endswith(".html"):
            continue
        pages += 1
        src = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
        page = "/" + os.path.relpath(os.path.join(r, f), D).replace(os.sep, "/")
        for h in re.findall(r'href="([^"]+)"', src):
            if h.startswith(("http", "mailto:", "#", "data:")):
                continue
            h = h.split("#")[0].split("?")[0]
            if not h.startswith("/"):
                continue
            t = (h[len(BASE):] if h.startswith(BASE) else h).rstrip("/") or "/"
            if t not in have and t + "/index.html" not in have and t != "/":
                bad[h] += 1
                where[h].add(page)

print(f"{pages} pages · {sum(bad.values())} broken internal links")
for k, v in bad.most_common(20):
    print(f"   {v:3d}  {k}\n        from {sorted(where[k])[:3]}")

# ── evidence reaches the person it names ───────────────────────────────────
#
# The Mazza archive kept its evidence in two TSVs and the script that built
# per-person data read neither, so twelve people documented several times over
# had pages reading "No record has been read for this person." This archive had
# the same fault in a different shape: register.json's `record` rows are keyed
# by name, build_dossiers.py drops every one whose name the tree also carries
# ("the rest already have one"), and /people/[slug] never read them — 176 lines
# naming 55 people, of whom 30 had pages saying no record had been found for
# them. Six London Gazette commissions on one of them.
#
# THIS READS THE EVIDENCE FILE, NOT THE DERIVED ONE. The first version of this
# gate walked person-records.json and asked whether each person in it had a
# record on their page. Putting the bug back emptied person-records.json, and
# the gate reported "0 record lines reach 0 of 0 people — ok". A control that
# cannot fail is not a control, and this archive has a rule about that. So the
# expectation is computed here, from register.json, the way the person page
# ought to have computed it all along: every name that appears on a `record`
# row AND on a `tree` row must reach that tree page.
#
# Control-tested three ways on 17 September 2026, each exiting 1:
#   · build_person_records.py made to skip in-tree people (the original bug)
#   · person-records.json deleted outright
#   · the records section removed from /people/[slug].astro
import json, collections as _c

REG = os.path.join(ROOT, "site", "src", "data", "register.json")
MARK_RECORD = "<h2>What the records say</h2>"
MARK_CORRECTION = "Corrected against the family tree."

expect = _c.defaultdict(int)          # slug -> record lines owed to that page
if os.path.exists(REG):
    reg = json.load(open(REG, encoding="utf-8"))
    tree, recs = _c.defaultdict(list), _c.defaultdict(list)
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "tree" and r["link"].startswith("/people/"):
                tree[r["name"].lower()].append(r["link"].rsplit("/", 1)[-1])
            elif r["kind"] == "record":
                recs[r["name"].lower()].append(r)
    for nm, rows in recs.items():
        for sl in tree.get(nm, []):
            expect[sl] += len(rows)
else:
    print("  FAIL  evidence   register.json is missing")
    sys.exit(1)

silent = []
for slug, n in sorted(expect.items()):
    f = os.path.join(D, "people", slug, "index.html")
    if not os.path.exists(f):
        silent.append((slug, n, "no page built"))
        continue
    html = open(f, encoding="utf-8", errors="ignore").read()
    if MARK_RECORD not in html and MARK_CORRECTION not in html:
        silent.append((slug, n, "page carries neither a record nor a correction"))

print(f"  {'ok  ' if not silent else 'FAIL'}  evidence   "
      f"{sum(expect.values())} record line(s) owed by register.json reach "
      f"{len(expect) - len(silent)} of {len(expect)} people in the tree")
for slug, n, why in silent[:20]:
    print(f"   {n:3d} record line(s) dropped  /people/{slug}  — {why}")
if silent:
    print(f"  {len(silent)} person(s) are named in the register and their page does not say so.")

# ── the other joins that attach evidence to a person ───────────────────────
#
# The record-row gate above came out of the Mazza fault: evidence keyed to a
# person that no build script delivered. Auditing the rest of this archive's
# person-joins on 20 September found no second instance of THAT — graves.json
# and households.json do reach their people, though only indirectly, through
# mentions.json matching a name phrase in rendered HTML.
#
# It found a different silent loss instead. APPEARS_IN in /people/[slug].astro
# is a hand-kept map of slug -> pages, and hannah-saniger was in it twice: four
# links, then two. In a JavaScript object literal the second wins silently, so
# the direct line of this archive had quietly lost her voyage on the General
# Hewitt. No build could see it — an overwrite and an edit are the same thing to
# a parser.
#
# So three checks, none of which existed before:
#   1. no duplicate key in a hand-kept person map
#   2. no key in any person-join pointing at a page that is not built
#   3. everyone named in graves.json or households.json reaches their own page
#
# Control-tested on 20 September by re-adding the duplicate key, by pointing a
# key at a slug that does not exist, and by emptying mentions.json. Each exits 1.
PERSON_PAGE = os.path.join(D, "people")
built = set()
if os.path.isdir(PERSON_PAGE):
    built = {n for n in os.listdir(PERSON_PAGE)
             if os.path.exists(os.path.join(PERSON_PAGE, n, "index.html"))}

joins = []
astro = os.path.join(ROOT, "site", "src", "pages", "people", "[slug].astro")
if built and os.path.exists(astro):
    src = open(astro, encoding="utf-8").read()
    for name in ("APPEARS_IN", "VERIFIED", "PORTRAITS"):
        m = re.search(name + r"\s*=\s*\{(.*?)\n\};", src, re.S)
        if not m:
            joins.append((name, "-", "map not found in the page — has it been renamed?"))
            continue
        keys = re.findall(r'^\s*"([a-z0-9\-]+)"\s*:', m.group(1), re.M)
        for k in sorted({k for k in keys if keys.count(k) > 1}):
            joins.append((name, k, "DUPLICATE KEY — the later entry silently wins"))
        for k in sorted({k for k in keys if k not in built}):
            joins.append((name, k, "key names a person with no page"))

    for fn in ("graves.json", "households.json", "mentions.json"):
        fp = os.path.join(ROOT, "site", "src", "data", fn)
        if not os.path.exists(fn) and not os.path.exists(fp):
            continue
        blob = open(fp, encoding="utf-8").read()
        refs = set(re.findall(r'"slug"\s*:\s*"([a-z0-9\-]+)"', blob))
        if fn == "mentions.json":
            refs = set(json.load(open(fp, encoding="utf-8")).keys())
        for k in sorted(refs - built):
            joins.append((fn, k, "names a person with no page"))

    # Every person given a grave must have its PLACE on their own page.
    #
    # The first version of this check asked whether the page contained the
    # string "/graves". It passed 101 out of 101 and could never have done
    # anything else: /graves/ is in the site navigation, so it is on every page
    # of the site. It was caught only because the control test could not be
    # constructed — there was no page lacking the marker to inject. A control
    # that cannot fail is not a control, and this archive has now written that
    # sentence about its own work three times in four days.
    #
    # What is checked instead is the fact rather than the link: graves.json
    # names a burial place, and that place must appear somewhere on the page.
    # It does, for all 101, because the family tree carries a burial field —
    # which is also the answer to whether /graves and /households are a second
    # instance of the record-row fault. They are not. The data reaches the
    # person by another road.
    gp = os.path.join(ROOT, "site", "src", "data", "graves.json")
    if os.path.exists(gp):
        gj = json.load(open(gp, encoding="utf-8"))
        for row in gj.get("rows", []):
            key = (row.get("place") or "").split(",")[0].strip()
            if not key:
                continue
            for per in row.get("people", []):
                sl = per.get("slug")
                if not sl or sl not in built:
                    continue
                page = open(os.path.join(PERSON_PAGE, sl, "index.html"),
                            encoding="utf-8", errors="ignore").read()
                # unescape first: the page renders "&" as "&amp;", and the
                # first run of this check reported Emma Atwell as missing a
                # grave her page states in full, for want of six characters.
                flat = _html.unescape(re.sub(r"<[^>]+>", " ", page))
                if key.lower() not in flat.lower():
                    joins.append(("graves.json", sl,
                                  f"has a grave at {key} that their page never says"))

print(f"  {'ok  ' if not joins else 'FAIL'}  joins      "
      f"3 hand-kept maps and 3 data files checked against {len(built)} person pages")
for where, key, why in joins[:20]:
    print(f"   {where:16} {key:34} {why}")
if joins:
    print(f"  {len(joins)} person-join problem(s).")

sys.exit(1 if (bad or silent or joins) else 0)

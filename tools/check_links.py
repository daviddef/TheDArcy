#!/usr/bin/env python3
"""Every internal href in the built site, resolved. Exits non-zero on a break."""
import os, re, sys, collections

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

sys.exit(1 if (bad or silent) else 0)

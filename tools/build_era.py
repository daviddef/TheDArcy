#!/usr/bin/env python3
"""The place table behind the "at the time" notes: which Record Atlas region each place on a person's page belongs to.

THE DECISION IS data/era-ground.tsv, written by hand: one row per place string exactly as a person page prints it beside a date (the Born and
Died rows and a marriage, of every person who is not living), with the Atlas region it belongs to, or '-' for "looked at, and no region covers it",
the reason, and the town whose point (data/era-towns.tsv) lets the kit refuse a place that falls in a neighbouring region's ring or within 15 km
of its own region's ring edge. A region is given only where the region CLEARLY covers the place: the string itself names England, Wales,
Scotland, Ireland or Queensland (or a town the table can fix there), or one of the few continental regions the Atlas has. This tool turns those
rows into site/src/data/era-places.json and refuses to pass when the rows and the data disagree:

    python3 tools/build_era.py                       write site/src/data/era-places.json
    python3 tools/build_era.py --check               build gate: the file is what the rows build, every place a non-living person's page prints
                                                     beside a date has a row, and no row is stale
    python3 tools/build_era.py --snapshot <Record Atlas>/site/public/context.json [--report drops.json]
                                                     also rebuild site/src/data/era-snapshot.json (version 4) from the Atlas's versioned contract
                                                     (the deliberate refresh: nothing in a build ever reads the Atlas). The rings and bboxes come
                                                     from the contract (1.8.0 and later). --report writes, per region, how many eras were refused
                                                     and why (counts only).
    python3 tools/build_era.py --living-urls         write the page paths the notes must never appear on (the living people's pages), for check:era, to
                                                     ~/.local/state/darcy-archive/era-living.json (OUTSIDE the repository, as the autolink pass keeps
                                                     its living list: a living person's name is in their address); $ERA_LIVING overrides the path
    python3 tools/build_era.py --living-path         print where that file is

THE POLICY ON ERAS THE ATLAS HAS NOT ASSESSED. A region era's `contested` and `approx` are null where nobody has assessed it (Ireland, Scotland, the
Netherlands, Denmark, Norway and Bohemia are all null today). The kit refuses such an era by default, which would leave no note on it, so this archive
builds its snapshot with --unassessed allow, on purpose and on the record: the snapshot's policy says so, the gate prints how many notes rest on an
unassessed era, and dropping that flag below (then rebuilding) is the whole of going strict. The other policies are the kit's defaults: --approx margin,
--contested scope, --margin-years 5 (an assessed era flagged approximate or contested about its bounds is used only for a year more than
max(5, the Atlas's margin) from each bound; kit/docs/era-notes.md rule l).

WHAT THE PAGE PRINTS, re-derived here from the data (the same merge site/src/lib/people.js makes, and the place the archive's own corrections map
puts in place of the tree's): born place, died place, and the place of each marriage whose spouse is named. Only people who are NOT living are read:
a living person's page prints a town and a country and no event, and the notes are never drawn there. The built pages are the final word on this;
tools/check_era_expect.py reads them.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slugrule  # noqa: E402

ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
DATA = os.path.join(SITE, "src", "data")
GROUND = os.path.join(ROOT, "data", "era-ground.tsv")
TOWNS = os.path.join(ROOT, "data", "era-towns.tsv")
OUT = os.path.join(DATA, "era-places.json")
SNAP = os.path.join(DATA, "era-snapshot.json")
CORRECTIONS = os.path.join(SITE, "src", "lib", "corrections.js")


def rows_of(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        yield line.rstrip("\n").split("\t")


def ground():
    rows = {}
    for cols in rows_of(GROUND):
        if cols[0] == "place":
            continue
        place, region, why, town = (cols + ["", "", "", ""])[:4]
        if not place or not region or not why:
            raise SystemExit("era-ground.tsv: a row needs a place, a region (or '-') and a reason: %r" % cols[0][:60])
        if place in rows:
            raise SystemExit("era-ground.tsv: a place appears twice (a row must say one thing): %r" % place[:60])
        rows[place] = (region, why, town)
    return rows


def towns():
    out = {}
    for cols in rows_of(TOWNS):
        if cols[0] == "town":
            continue
        out[cols[0]] = (float(cols[1]), float(cols[2]))
    return out


ENT = {"&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&amp;": "&"}


def clean_place(s):
    """site/src/lib/people.js cleanPlace(): the born and died places are unescaped, stripped of angle brackets and of runs of white space."""
    if not isinstance(s, str):
        return s
    s = re.sub(r"&(?:lt|gt|quot|#39|amp);", lambda m: ENT[m.group(0)], s)
    s = re.sub(r"[<>]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def merged_people():
    """{id: record}, merged the way people.js build() merges (ancestors, then the families' members, then the relatives; a later record's fields win)."""
    by_id = {}

    def add(rec):
        if not isinstance(rec, dict) or not rec.get("id"):
            return
        prev = by_id.get(rec["id"], {})
        merged = {**prev, **rec}
        for k in ("bornPlace", "diedPlace"):
            if rec.get(k):
                merged[k] = clean_place(rec[k])
        by_id[rec["id"]] = merged

    def load(name):
        p = os.path.join(DATA, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []

    for a in load("ancestors.json"):
        add(a)
    for f in load("families.json"):
        for m in f["members"]:
            add(m)
    for r in load("relatives.json"):
        add(r)
    return by_id


def place_corrections():
    """{slug: {bornPlace|diedPlace: string}}: where lib/corrections.js puts the archive's finding in place of the tree's place."""
    src = open(CORRECTIONS, encoding="utf-8").read()
    body = src[src.index("export const CORRECTIONS"):src.index("export const yearOf")]
    out = {}
    for m in re.finditer(r'^  "([a-z0-9-]+)": \{', body, re.M):
        blk = body[m.end():]
        blk = blk[:blk.index("\n  },")]
        for k in ("bornPlace", "diedPlace"):
            mm = re.search(r"^\s+%s: \[(\"(?:[^\"\\]|\\.)*\")" % k, blk, re.M)
            if mm:
                out.setdefault(m.group(1), {})[k] = json.loads(mm.group(1))
    return out


def has_name(s):
    """«—» is what a page prints for no place; it folds to nothing, and the kit refuses a table that holds one."""
    return any(c.isalnum() for c in str(s))


def event_places():
    """Every place string a non-living person's page prints beside a date: born, died and the marriages whose spouse is named."""
    people = merged_people()
    slugs = slugrule.assign(*slugrule.records())
    corr = place_corrections()
    out = {}

    def count(place):
        if place and has_name(place):
            out[place] = out.get(place, 0) + 1

    for pid, p in people.items():
        if p.get("living"):
            continue
        c = corr.get(slugs.get(pid), {})
        count(c.get("bornPlace", p.get("bornPlace")))
        count(c.get("diedPlace", p.get("diedPlace")))
        for s in p.get("spouses") or []:
            if s.get("name") and s["name"] != "—" and not s.get("living"):
                count(s.get("marriedPlace"))
    return out


def build():
    rows = ground()
    used = event_places()
    pts = towns()
    table = {}
    for place in sorted(rows):
        region, _, town = rows[place]
        if region == "-":
            table[place] = None
            continue
        table[place] = {"region": region}
        if town:
            if town not in pts:
                raise SystemExit("era-ground.tsv: town %r has no row in era-towns.tsv" % town)
            table[place].update(lat=pts[town][0], lon=pts[town][1])
    return rows, used, table


def living_path():
    if os.environ.get("ERA_LIVING"):
        return os.environ["ERA_LIVING"]
    return os.path.join(os.path.expanduser("~"), ".local", "state", "darcy-archive", "era-living.json")


def living_urls():
    people = merged_people()
    slugs = slugrule.assign(*slugrule.records())
    return sorted("/people/%s/" % slugs[pid] for pid, p in people.items() if p.get("living") and pid in slugs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--snapshot", default=None, help="a local copy of the Record Atlas's context.json (the versioned contract): also rebuild era-snapshot.json")
    ap.add_argument("--report", default=None, help="write the per-region count of refused eras (and why) here (JSON)")
    ap.add_argument("--living-urls", action="store_true", help="write the living page paths (JSON list) outside the repository and stop")
    ap.add_argument("--living-path", action="store_true", help="print where --living-urls writes, and stop")
    a = ap.parse_args()
    if a.living_path:
        print(living_path())
        return 0
    if a.living_urls:
        urls = living_urls()
        if not urls:
            raise SystemExit("build_era: no living page found; a list of none would make the living gate a verdict on nothing")
        fp = living_path()
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w", encoding="utf-8").write(json.dumps(urls, indent=0) + "\n")
        try:
            os.chmod(fp, 0o600)
        except OSError:
            pass
        print("  era living list: %d page path(s), kept outside the repository" % len(urls))
        return 0
    rows, used, table = build()
    missing = sorted(set(used) - set(rows))
    stale = sorted(set(rows) - set(used))
    out = {"_about": "Built by tools/build_era.py from data/era-ground.tsv and data/era-towns.tsv. Place as printed -> {region, lat, lon}, or null where no Atlas "
                     "region covers it. Read by kit erasnap.py.", "places": table}
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if a.check:
        bad = False
        if missing:
            print("  FAIL  era-ground  %d place string(s) a non-living person's page prints beside a date have no row in data/era-ground.tsv "
                  "(decide a region, or '-', for each)" % len(missing))
            bad = True
        if stale:
            print("  FAIL  era-ground  %d row(s) in data/era-ground.tsv match no place (stale)" % len(stale))
            bad = True
        try:
            have = open(OUT, encoding="utf-8").read()
        except OSError:
            have = None
        if have != text:
            print("  FAIL  era-ground  site/src/data/era-places.json is not what the rows build (run tools/build_era.py)")
            bad = True
        if not bad:
            mapped = sum(1 for v in table.values() if v)
            print("  ok    era-ground  %d place strings decided (%d mapped to a region, %d to none); the table matches" % (len(table), mapped, len(table) - mapped))
        return 1 if bad else 0
    open(OUT, "w", encoding="utf-8").write(text)
    print("era-places.json: %d place strings (%d mapped)" % (len(table), sum(1 for v in table.values() if v)))
    if missing:
        print("  WARNING %d place string(s) have no row in data/era-ground.tsv" % len(missing))
        return 1
    if a.snapshot:
        cmd = [sys.executable, os.path.join(KIT_TOOLS, "erasnap.py"), "--contract", a.snapshot,
               "--places", OUT, "--out", SNAP, "--unassessed", "allow"]
        if a.report:
            cmd += ["--report", a.report]
        r = subprocess.run(cmd)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())

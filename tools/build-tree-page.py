#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roots & Routes: the tree page for this archive, built from this archive's own committed data.

    python3 tools/build-tree-page.py            # rebuild data/tree-page/ (tree.json, atlas-data.json, roots.html) and site/public/roots-links.json

(23 November 2026: the /roots/ PAGE was retired, so the fragment for it, roots.embed.html, is no longer built. roots.html stays: it is served bare at
/roots/view.html for the kit's per-person "Where they lived" frames on the person pages.)
    python3 tools/build-tree-page.py --check    # exit 1 if the page is older than the data it was built from

WHERE THE PEOPLE COME FROM. There is no committed GEDCOM (the tree export carries living people in full and stays outside the repo). The people are the ones the
person pages draw: tools/export_tree_people.mjs reads site/src/lib/people.js (the same slugs, names and years the pages print, with lib/corrections.js applied)
and exports every person who is NOT living. That file is turned into a small GEDCOM (data/tree-page/people.ged, not committed) and handed to the
family-tree-page skill's converter, vendored in tools/tree-page/ so CI and other sessions do not depend on ~/.claude. The converter then adds its own floor:
nobody with no death recorded and a birth year in the last 110 years is drawn. A person this archive declares to be a copy of another (site/src/data/same-person.json)
is not drawn twice: the primary is drawn and every relation to the copy goes to it.

COLOUR is the archive's own family (the `family` of a person in people.js, the surnames of its thirteen clusters in families.json), not a surname spelling: which
spellings are one name is the Record Atlas catalogue's to say (surname-variants skill), and this archive keeps no list of them.

PLACES are resolved through data/tree-page/place_map.json, never guessed. data/era-ground.tsv decided, for every place string AS PRINTED on a page, the town it
belongs to (and refused a string that is several places or a country only); data/era-towns.tsv gives that town's point; the country is the Atlas's own
`geo.country_of` on the point. A string the era table leaves without a town is resolved only if the Record Atlas names it uniquely in the country the string
names (--accept-unique), or by hand in place-additions.json with a reason. Anything else is listed in tree.report.json (unresolved_places), and the person is
drawn at a relative's birth place (and the page says so) or, with no relative placed, not drawn.
"""
import argparse, collections, hashlib, io, json, os, subprocess, sys, unicodedata, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
OUT = os.path.join(ROOT, "data", "tree-page")
TP = os.path.join(ROOT, "tools", "tree-page")
EXT = os.path.join(TP, "painted-lines.ext.html")
HOST = "darcy.defranceski.com"
FULLDATE = re.compile(r"^\d{1,2} (?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) \d{4}$")   # 4 APR 1460 | 17 AUG 1927 : this archive's GEDCOM form, a day present, no ABT/BET/BEF/AFT/EST/TO
REDIRECTED = set((json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site", "src", "data", "who-fold.json"), encoding="utf-8")).get("redirects") or {}))   # the /who/ names that are redirects (tools/who-fold-rulings.json)
FOCUS_SLUG = "kenneth-lindsay-d-arcy"    # where the page opens: the man the archive's eulogy is for. Left to itself the converter opens on the best-connected person, who is a man of the Hornby descent this archive does not accept
ATLAS_CANDIDATES = [os.environ.get("RECORD_ATLAS", ""), os.path.expanduser("~/Projects/Family Projects/Record Atlas"),
                    os.path.join(os.path.dirname(ROOT), "Record Atlas")]
INPUTS = [os.path.join(DATA, n) for n in ("ancestors.json", "families.json", "relatives.json", "same-person.json", "living.json", "dossiers.json")] + \
         [os.path.join(SITE, "src", "lib", "corrections.js"), os.path.join(SITE, "src", "lib", "people.js"),
          os.path.join(ROOT, "data", "era-ground.tsv"), os.path.join(ROOT, "data", "era-towns.tsv"), os.path.join(ROOT, "tools", "export_tree_people.mjs")]

def jl(path): return json.load(io.open(path, encoding="utf-8"))
def run(args, cwd=None):
    print("$", " ".join(os.path.relpath(a, ROOT) if os.path.isabs(a) and a.startswith(ROOT) else a for a in args)); r = subprocess.run(args, cwd=cwd)
    if r.returncode: sys.exit(r.returncode)
def inputs_hash():
    h = hashlib.sha1()
    for n in INPUTS: h.update(io.open(n, "rb").read())
    for n in ("tree-views.template.html", "painted-lines.ext.html", "gedcom_to_tree.py"): h.update(io.open(os.path.join(TP, n), "rb").read())
    h.update(io.open(os.path.abspath(__file__), "rb").read())
    pm = os.path.join(OUT, "place_map.json")
    if os.path.exists(pm): h.update(io.open(pm, "rb").read())
    return h.hexdigest()[:16]
def atlas_path():
    for c in ATLAS_CANDIDATES:
        if c and os.path.exists(os.path.join(c, "data", "places.json")): return c
    sys.exit("Record Atlas checkout not found (set RECORD_ATLAS)")

# ---------------------------------------------------------------- the people the pages draw -> a small GEDCOM
def export_people():
    path = os.path.join(OUT, "people.export.json")
    run(["node", "--import", "./tools/jsonhooks.mjs", "tools/export_tree_people.mjs", path], cwd=ROOT)
    return jl(path)

def write_ged(people, path):
    """people: the dead the pages draw, copies already folded into their primaries. Relations are the tree's: a child's parents, and a spouse's children."""
    byid = {p["id"]: p for p in people}
    out = ["0 HEAD", "1 CHAR UTF-8"]
    fams, fam_of_child, fam_of_spouse = {}, {}, collections.defaultdict(list)
    def fam(h, w):
        k = (h or "", w or "")
        if k not in fams: fams[k] = "@F%d@" % (len(fams) + 1)
        return fams[k]
    def pair(ids):
        """two parents -> (father, mother): the M one is the father; a parent of unrecorded sex is read in the order the tree lists them"""
        ids = [i for i in ids if i in byid]
        f = next((i for i in ids if byid[i]["sex"] == "M"), None); m = next((i for i in ids if byid[i]["sex"] == "F" and i != f), None)
        rest = [i for i in ids if i not in (f, m)]
        if not f and rest: f = rest.pop(0)
        if not m and rest: m = rest.pop(0)
        return f, m
    # a child's own parent list first, then the children a spouse record names
    for p in people:
        f, m = pair(p["parents"])
        if f or m: fam_of_child[p["id"]] = fam(f, m)
    for p in people:
        for s in p["spouses"]:
            sid = s["id"]
            if sid not in byid or sid == p["id"]: continue
            x, y = p["id"], sid
            if byid[x]["sex"] == byid[y]["sex"]: a, b = sorted((x, y))        # same sex recorded twice (or unrecorded): a stable order, so the couple is one family
            else: a, b = (x, y) if byid[x]["sex"] != "F" else (y, x)
            k = fam(a, b)
            for pid_, fx in ((p["id"], k), (sid, k)):
                if fx not in fam_of_spouse[pid_]: fam_of_spouse[pid_].append(fx)
            for c in s["children"]:
                if c in byid and c not in fam_of_child: fam_of_child[c] = k
    for p in people:
        given, sur = p["name"], p["surname"]
        if sur and given.endswith(sur): given = given[:-len(sur)].strip()
        elif sur: given, sur = p["name"], ""     # the surname is not in the name as printed: the whole name is the given name
        out += ["0 %s INDI" % p["id"], "1 NAME %s /%s/" % (given, sur)]
        if p["sex"] in ("M", "F"): out.append("1 SEX %s" % p["sex"])      # a sex the tree does not record is written as none: the converter reads it as 'u' and the page says parent, child, spouse
        elif p["sex"]: out.append("1 SEX U")                                # the tree's own «U». A sex is never inferred from a name
        dead = bool(p["died"] or p["diedPlace"] or p["burial"] or p["cause"])
        if p["born"] or p["bornPlace"]:
            out.append("1 BIRT")
            if p["born"]: out.append("2 DATE %s" % p["born"])
            if p["bornPlace"]: out.append("2 PLAC %s" % p["bornPlace"])
        if dead:
            out.append("1 DEAT")
            if p["died"]: out.append("2 DATE %s" % p["died"])
            if p["diedPlace"]: out.append("2 PLAC %s" % p["diedPlace"])
        if p["occupation"]: out.append("1 OCCU %s" % p["occupation"])
        if p["id"] in fam_of_child: out.append("1 FAMC %s" % fam_of_child[p["id"]])
        for fx in fam_of_spouse.get(p["id"], []): out.append("1 FAMS %s" % fx)
    for (h, w), fx in fams.items():
        out.append("0 %s FAM" % fx)
        if h: out.append("1 HUSB %s" % h)
        if w: out.append("1 WIFE %s" % w)
        for cid, f in fam_of_child.items():
            if f == fx: out.append("1 CHIL %s" % cid)
    out.append("0 TRLR")
    io.open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")

# ---------------------------------------------------------------- places the archive has already placed
def fold(s): return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()).strip()
def km(a, b, c, d):
    import math
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def seed_place_map(atlas):
    """Place strings this archive has already put on the ground. data/era-ground.tsv decided, for every place string AS PRINTED, the town it belongs to
    (column 4) and REFUSED a string whose names disagree, a bare name that is several places, or a country-only string: those rows have no town and stay
    unresolved here. data/era-towns.tsv gives the town's point (the kit's gazetteer, or the centre of the town by hand). The country is the Atlas's own
    `geo.country_of` on the point, never a guess from the string; a Record Atlas place is linked only where it has the same name within 15 km."""
    sys.path.insert(0, os.path.join(atlas, "scripts")); import geo
    cj = jl(os.path.join(atlas, "data", "countries.json"))["countries"]
    pj = jl(os.path.join(atlas, "data", "places.json"))["places"]
    byname = collections.defaultdict(list)
    for x in pj:
        for nm in [x["name"]] + [n["n"].split(",")[0] for n in x.get("names", [])]: byname[fold(nm)].append(x)
    towns = {}
    for line in io.open(os.path.join(ROOT, "data", "era-towns.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        c = line.rstrip("\n").split("\t")
        if c[0] == "town" or len(c) < 3: continue
        towns[c[0]] = (float(c[1]), float(c[2]))
    pm_path = os.path.join(OUT, "place_map.json")
    pm = jl(pm_path) if os.path.exists(pm_path) else {}
    seeded = 0
    for line in io.open(os.path.join(ROOT, "data", "era-ground.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        c = line.rstrip("\n").split("\t")
        if len(c) < 4 or c[0] == "place": continue
        raw, town = c[0], c[3].strip()
        if not town or town not in towns or (pm.get(raw) or {}).get("lat") is not None: continue
        lat, lon = towns[town]
        name = re.sub(r" \(county\)$", "", town)
        iso = geo.country_of(lat, lon)
        if not iso: continue
        hit = next((x for x in byname.get(fold(name), []) if x.get("country") == iso and km(lat, lon, x["lat"], x["lon"]) <= 15), None)
        pm[raw] = {"name": name, "lat": lat, "lon": lon, "country": cj.get(iso, {}).get("name", iso), "iso": iso, "atlas_id": hit["id"] if hit else None,
                   "how": "data/era-ground.tsv town and data/era-towns.tsv point; country by the Atlas's geo.country_of"}
        seeded += 1
    ap_ = os.path.join(OUT, "place-additions.json")
    if os.path.exists(ap_):
        for k, v in jl(ap_)["places"].items():
            if (pm.get(k) or {}).get("lat") is None: pm[k] = v; seeded += 1
    io.open(pm_path, "w", encoding="utf-8").write(json.dumps(pm, indent=1, ensure_ascii=False))
    print("place_map: %d place strings seeded (era-ground.tsv and place-additions.json)" % seeded)

def describe_atlas_accepted(atlas):
    """The converter's --accept-unique writes a place it took from the Record Atlas without saying how. Say it, and say where the point is only the Atlas's marker for
    a region or a country (level == 'region', or a country itself), which the page must not read as a town."""
    pm_path = os.path.join(OUT, "place_map.json"); pm = jl(pm_path)
    pj = {x["id"]: x for x in jl(os.path.join(atlas, "data", "places.json"))["places"]}
    cj = jl(os.path.join(atlas, "data", "countries.json"))["countries"]
    n = 0
    for k, v in pm.items():
        if v.get("lat") is None or v.get("how"): continue
        x = pj.get(v.get("atlas_id")) or {}
        coarse = x.get("level") == "region" or fold(v["name"]) == fold(cj.get(v.get("iso"), {}).get("name", "")) or fold(v["name"]) == fold(v.get("country"))
        v["how"] = "the Record Atlas names this uniquely in the country the string names (--accept-unique)" + ("; region- or country-level: the point is the Atlas's own marker for it, not a town" if coarse else "")
        if coarse: v["level"] = "region"
        n += 1
    io.open(pm_path, "w", encoding="utf-8").write(json.dumps(pm, indent=1, ensure_ascii=False))
    print("place_map: %d places taken from the Atlas by unique name are now described" % n)

def build(a):
    os.makedirs(OUT, exist_ok=True)
    exp = export_people(); rows = exp["people"]
    copies = {p["id"]: p["copyOf"] for p in rows if p["copyOf"]}
    prim = lambda i: copies.get(i, i)
    people = [p for p in rows if not p["copyOf"]]
    ids = {p["id"] for p in people}
    for p in people:     # every relation to a declared copy goes to its primary; a relation to anyone not drawn is dropped
        p["parents"] = list(dict.fromkeys(prim(x) for x in p["parents"] if prim(x) in ids and prim(x) != p["id"]))
        for s in p["spouses"]:
            s["id"] = prim(s["id"]); s["children"] = list(dict.fromkeys(prim(c) for c in s["children"] if prim(c) in ids))
        p["spouses"] = [s for s in p["spouses"] if s["id"] in ids]
    write_ged(people, os.path.join(OUT, "people.ged"))
    slugs = {p["id"].strip("@"): p["slug"] for p in people}
    io.open(os.path.join(OUT, "slugs.json"), "w", encoding="utf-8").write(json.dumps(slugs, ensure_ascii=False))
    fams = jl(os.path.join(DATA, "families.json"))
    top = sorted(fams, key=lambda f: -f["published"])[:7]
    atlas = atlas_path(); seed_place_map(atlas)
    tree, pm = os.path.join(OUT, "tree.json"), os.path.join(OUT, "place_map.json")
    cmd = [sys.executable, os.path.join(TP, "gedcom_to_tree.py"), os.path.join(OUT, "people.ged"), "--out", tree, "--place-map", pm, "--atlas", atlas, "--living", "omit",
           "--lines", "8", "--slugs", os.path.join(OUT, "slugs.json"), "--title", "Roots & Routes",
           "--subtitle", "Explore the family tree ten ways: by generation, place, era and relationship. Click anyone and every view follows."]
    if a.accept_unique: cmd.append("--accept-unique")
    focus = next((p["id"].strip("@") for p in people if p["slug"] == FOCUS_SLUG), None)
    if focus: cmd += ["--focus", focus]
    run(cmd)
    describe_atlas_accepted(atlas)
    t = jl(tree)
    fam_of = {p["id"].strip("@"): p.get("family") for p in people}
    src_of = {p["id"].strip("@"): p for p in people}
    key_i = {f["surname"]: i for i, f in enumerate(top)}
    for p in t["people"]:
        p["line"] = key_i.get(fam_of.get(p["id"]), 7)
        p["page"] = "/people/%s/" % slugs[p["id"]] if p["id"] in slugs else None
        if p["page"] is None: p.pop("page")
        # FULL DATES (bd, dd), for DEAD people only: `people` holds only the dead the pages draw (export_tree_people.mjs leaves out everyone people.js marks living, and the
        # converter's floor and drop_possibly_living() leave out the rest), so a living person never gets one. The string is people.js's own `born` / `died`, byte for byte,
        # which the person page prints as "4 April 1460" (people.js keeps the GEDCOM form "4 APR 1460"; kept as stored, not reformatted). A year alone, a year-month, an approximate date ("1875c", "c.1812") or a year the archive's corrections.js has overturned
        # (exported as a bare year) is NOT a full date and gets no field: `by` / `dy` and the `bye` / `dye` flags already carry those. Added 16 Nov 2026 for the Atlas Tree Canvas.
        src = src_of.get(p["id"], {})
        if FULLDATE.match(str(src.get("born") or "")): p["bd"] = src["born"]
        if FULLDATE.match(str(src.get("died") or "")): p["dd"] = src["died"]
        # CORRECTIONS COUNT (cx, optional): how many corrections this archive records about the person, the number the person page lists under "Corrected against the family
        # tree" (one per entry of lib/corrections.js for the slug; the export counts them, a living person is never exported). A count only; omitted when 0. Added 16 Nov 2026
        # for the Atlas Tree Canvas, which shows a pencil and the count and links to /corrections/.
        if int(src.get("cx") or 0) >= 1: p["cx"] = int(src["cx"])
        if is_placeholder(src.get("name")): p["placeholder"] = True
    t["lines"] = [{"sur": f["surname"], "host": HOST} for f in top] + [{"sur": "Other", "host": HOST}]
    t["meta"].update({"rowLabel": "Family line", "lineLabel": "Family line"})
    mark_relative_places(t, people)
    drop_conflicts(t, tree)
    drop_possibly_living(t, tree)
    t["undrawn"], und = undrawn_cards(rows, exp.get("living") or [], t, key_i, fam_of, prim)
    rep_path = os.path.splitext(tree)[0] + ".report.json"; rep = jl(rep_path)
    rep["undrawn"] = und
    rep["declared_copies_folded_into_primary"] = len(copies)
    rep["export"] = {k: v for k, v in exp.items() if k not in ("people", "living")}; rep["not_living_exported"] = len(rows)
    io.open(rep_path, "w", encoding="utf-8").write(json.dumps(rep, indent=1, ensure_ascii=False))
    io.open(tree, "w", encoding="utf-8").write(json.dumps(t, ensure_ascii=False, separators=(",", ":")))

def is_placeholder(name):
    """A record that STANDS FOR somebody rather than naming them ("Unknown", "UNKNOWN Falco", an unnamed infant, a person known only by a household). David (17 November 2026): they
    are research hotspots, so they are drawn and FLAGGED (`placeholder: true`), never hidden. Only the NAME decides: a word in a bracketed note does not make a named person a stand-in."""
    n = name or ""
    base = re.sub(r"\([^)]*\)", " ", n)
    return bool(re.match(r"\s*\[", n) or re.search(r"\bunnamed\b|\bunknown\b|\bhousehold\b|\bplaceholder\b", base, re.I))

def undrawn_cards(rows, living, t, key_i, fam_of, prim):
    """EVERYONE THE ARCHIVE PUBLISHES IS ON THE CANVAS (David, 17 November 2026, "if it's in the archive it must be shown"). The ten views draw only the dead people who can be
    placed and dated; everyone else who has a page of their own goes into tree.json's `undrawn`, which the page's views ignore and the Record Atlas Tree Canvas draws as an unplaced card.
      - a DEAD person the maps skip (undated, unplaced, a declared copy, one of the conflicts): an unplaced card with what their page prints: given, sur, `by`/`dy` where a year is
        recorded, parent / spouse / child links, the page, cx. A declared copy has NO links (its relations go to its primary, who is drawn once).
      - a person with NO DEATH recorded whose birth, recorded OR estimated from kin, is 1900 or later (this archive's floor, the same as drop_possibly_living), and every LIVING
        person the page names: a living-style card, `living: true`, NAME AND FAMILY LINKS ONLY (no sex, no date, no place, no page link, no cx). Their names are already public on their
        pages; this adds nothing about them. A living person the pages do not name (no name, or the dash) stays unnamed here too.
    Each card also carries `name` and `why` ('year', 'place' or 'other'), which the page's own "Not drawn yet" list reads.
    Links follow the register's own, only to people who are themselves in tree.json, and drawn people's own lists are left exactly as they were."""
    sid = lambda i: i.strip("@")
    drawn = {p["id"] for p in t["people"]}
    byrow = {r["id"]: r for r in rows}
    yr = lambda v: (lambda m: int(m.group(0)) if m else None)(re.search(r"\d{4}", str(v or "")))
    circa = lambda v: bool(re.search(r"\b(ABT|EST|CAL|BET|BEF|AFT|FROM|TO)\b|\bc\.?\s*\d|\d\s*c\b|about", str(v or ""), re.I))
    def est_birth(r):
        b = yr(r["born"])
        if b: return b
        ys = []
        for pid in r["parents"]:
            q = byrow.get(pid)
            if q and yr(q["born"]): ys.append(yr(q["born"]) + 28)
        for sp in r["spouses"]:
            q = byrow.get(sp["id"])
            if q and yr(q["born"]): ys.append(yr(q["born"]))
            for c in sp["children"]:
                q = byrow.get(c)
                if q and yr(q["born"]): ys.append(yr(q["born"]) - 28)
        return round(sum(ys) / len(ys)) if ys else None
    cand = [r for r in rows if sid(r["id"]) not in drawn]
    liv = [l for l in living if l.get("name")]
    ids = drawn | {sid(r["id"]) for r in cand} | {sid(l["id"]) for l in liv}
    copyof = {sid(r["id"]) for r in rows if r["copyOf"]}
    par, kids, sp = collections.defaultdict(list), collections.defaultdict(set), collections.defaultdict(set)
    def link(parent, child):
        parent, child = sid(prim(parent)), sid(prim(child))
        if parent == child or parent not in ids or child not in ids: return
        kids[parent].add(child)
        if parent not in par[child]: par[child].append(parent)
    for r in list(rows) + list(liv):
        me = sid(r["id"])
        if me in copyof: continue                         # a declared copy's relations belong to its primary
        for pid in r["parents"]: link(pid, r["id"])
        for x in r["spouses"]:
            o = sid(prim(x["id"]))
            if o != me and o in ids: sp[me].add(o); sp[o].add(me)
            for c in x["children"]: link(r["id"], c)
    sexof = {sid(r["id"]): r["sex"] for r in rows}
    out, kinds = [], collections.Counter()
    def card(me, name, surname, line):
        given, sur = name, surname
        if sur and given.endswith(sur): given = given[:-len(sur)].strip()
        elif sur: given, sur = name, ""
        f = m = None
        free = []
        for x in par.get(me, []):
            sx = (sexof.get(x) or "").upper()
            if sx == "M" and not f: f = x
            elif sx == "F" and not m: m = x
            else: free.append(x)
        for x in free:
            if not f and x != m: f = x
            elif not m and x != f: m = x
        return {"id": me, "name": name, "why": "other", "sex": "u", "given": given, "sur": sur, "line": line, "father": f, "mother": m, "spouse": sorted(sp.get(me, ())), "kids": sorted(kids.get(me, ()))}
    for r in sorted(cand, key=lambda q: q["id"]):
        me = sid(r["id"])
        nodeath = not (r["died"] or r["diedPlace"] or r["burial"] or r["cause"])
        b = est_birth(r)
        line = key_i.get(fam_of.get(me), 7)
        c = card(me, r["name"], r["surname"], line)
        if nodeath and b is not None and b >= 1900:
            c["living"] = True; kinds["living-style (no death recorded, born 1900 or later)"] += 1
        else:
            sx = (r["sex"] or "").upper()
            c["sex"] = "m" if sx == "M" else "f" if sx == "F" else "u"
            c["unplaced"] = True
            if yr(r["born"]): c["by"] = yr(r["born"]); c["bye"] = circa(r["born"])
            if yr(r["died"]): c["dy"] = yr(r["died"]); c["dye"] = circa(r["died"])
            c["why"] = "place" if (yr(r["born"]) or yr(r["died"])) else "year"      # the page's own "Not drawn yet" list says which: no year, or a year but no place
            c["slug"] = r["slug"]; c["page"] = "/people/%s/" % r["slug"]
            if int(r.get("cx") or 0) >= 1: c["cx"] = int(r["cx"])
            kinds["dead, unplaced" + (" (a declared copy)" if me in copyof else "")] += 1
        out.append(c)
    for l in sorted(liv, key=lambda q: q["id"]):
        c = card(sid(l["id"]), l["name"], l["surname"], 7)
        c["living"] = True; out.append(c); kinds["living (named on their bare page)"] += 1
    # The people who have only a /who/ record page (site/src/data/dossiers.json: a name read from a document, no place in the tree): an unplaced, name-only card linking to the page.
    # No family links (a record names no tree relative), no date (the page prints what the record says; nothing is added here).
    for w in sorted(jl(os.path.join(DATA, "dossiers.json"))["people"].values(), key=lambda q: q["slug"]):
        if w.get("inTree"): continue
        if w["slug"] in REDIRECTED: continue            # /who/<slug>/ is a redirect to the person page (23 November 2026), and that person already has a card: a second card for one person is no page
        c = card("who-" + w["slug"], w["name"], "", 7)
        parts = w["name"].split()                               # the dossier's surname is upper-case ("D'ARCY"): the printed name's last word is the surname the page shows
        c["given"], c["sur"] = " ".join(parts[:-1]), (parts[-1] if len(parts) > 1 else "")
        if len(parts) == 1: c["given"] = w["name"]
        c["unplaced"] = True; c["slug"] = w["slug"]; c["page"] = "/who/%s/" % w["slug"]; c["why"] = "year"
        if is_placeholder(w["name"]): c["placeholder"] = True
        out.append(c); kinds["record only (a /who/ page, not in the tree)"] += 1
    for c in out:
        if is_placeholder(c.get("name")): c["placeholder"] = True
    return out, dict(kinds, total=len(out))

def mark_relative_places(t, people):
    """The converter puts a person whose own birth place it cannot resolve (none recorded, or a string the place map does not place) at a relative's birth place, and
    says so only in its report. The page can say it on the card (`bpe`: «place taken from a relative, not recorded», and an asterisk), so it does: every person whose
    drawn birth place is not the place their own record names gets it."""
    pm = jl(os.path.join(OUT, "place_map.json"))
    own = {p["id"].strip("@"): (pm.get(p["bornPlace"]) or {}).get("name") if p["bornPlace"] else None for p in people}
    n = 0
    for p in t["people"]:
        if own.get(p["id"]) != p["bp"]: p["bpe"] = True; n += 1
    print("relative's place: %d people are drawn at a relative's birth place and marked so on the page" % n)

def drop_people(t, tree, bad, key, why):
    """Take `bad` (a set of ids) off the page: they are not drawn, they are counted (and, for a conflict, named) in tree.report.json under `key`, and every relation to them is
    removed so the page stays symmetric."""
    if not bad: return
    rep_path = os.path.splitext(tree)[0] + ".report.json"; rep = jl(rep_path)
    rows = [{"id": p["id"], "slug": p.get("slug"), "born": p["by"], "died": p["dy"]} for p in t["people"] if p["id"] in bad]
    rep[key] = rows if key == "conflicts" else {"count": len(rows)}   # a possibly-living person is counted, never listed
    t["people"] = [p for p in t["people"] if p["id"] not in bad]
    for p in t["people"]:
        for k in ("father", "mother"):
            if p.get(k) in bad: p[k] = None
        p["spouse"] = [x for x in p["spouse"] if x not in bad]; p["kids"] = [x for x in p["kids"] if x not in bad]
    if t.get("focus") in bad: t["focus"] = t["people"][0]["id"]
    io.open(rep_path, "w", encoding="utf-8").write(json.dumps(rep, indent=1, ensure_ascii=False))
    print("%s: %d people %s" % (key, len(bad), why))

def drop_conflicts(t, tree):
    """A person whose recorded death comes before their birth, or more than 110 years after it, is not one life. They are not drawn and are named in tree.report.json
    (conflicts) for the research to settle."""
    bad = {p["id"] for p in t["people"] if not p.get("dye") and p.get("dy") is not None and not 0 <= p["dy"] - p["by"] <= 110}
    drop_people(t, tree, bad, "conflicts", "whose death is before their birth, or over 110 years after it, are not one life and are not drawn")

def drop_possibly_living(t, tree):
    """THIS ARCHIVE'S FLOOR, STRICTER THAN THE CONVERTER'S: a person with no death recorded (the page would print «1915–?») whose birth, recorded OR estimated from a relative,
    falls after 1900 is not drawn. The converter drops no-death people born within 110 years (after 1916); an estimated birth can be decades out, so the line is 1900."""
    bad = {p["id"] for p in t["people"] if p.get("dye") and p["by"] > 1900}
    drop_people(t, tree, bad, "possibly_living_omitted", "have no death recorded and a birth (recorded or estimated) after 1900: possibly living, not drawn")

def write_roots_links(tree):
    """site/public/roots-links.json: the people Roots & Routes DRAWS (one id each). The person page offers 'Where they lived' only for those."""
    ids = sorted(p["id"] for p in jl(tree)["people"])
    out = {"note": "The people Roots & Routes draws, by person id. Made by tools/build-tree-page.py; do not edit by hand.", "people": ids}
    io.open(os.path.join(ROOT, "site", "public", "roots-links.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("roots-links: %d people" % len(ids))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true"); ap.add_argument("--accept-unique", action="store_true")
    a = ap.parse_args()
    if a.check:
        try: have = jl(os.path.join(OUT, "tree.json"))["meta"]["inputs"]
        except Exception: print("tree page: not built yet. python3 tools/build-tree-page.py"); sys.exit(1)
        if have != inputs_hash(): print("tree page is STALE: the people, corrections, era tables, place map or builder changed since it was built.\n  python3 tools/build-tree-page.py --accept-unique"); sys.exit(1)
        print("tree page is current"); return
    build(a)
    tree = os.path.join(OUT, "tree.json"); pm = os.path.join(OUT, "place_map.json"); ad = os.path.join(OUT, "atlas-data.json"); page = os.path.join(OUT, "roots.html")
    run([sys.executable, os.path.join(TP, "build_atlas_data.py"), "--atlas", atlas_path(), "--tree", tree, "--place-map", pm, "--out", ad])
    t = jl(tree); t["meta"]["inputs"] = inputs_hash()
    io.open(tree, "w", encoding="utf-8").write(json.dumps(t, ensure_ascii=False, separators=(",", ":")))
    write_roots_links(tree)
    tpl = os.path.join(TP, "tree-views.template.html")
    run([sys.executable, os.path.join(TP, "build_page.py"), "--template", tpl, "--tree", tree, "--atlas-data", ad, "--out", page, "--ext", EXT])
    run([sys.executable, os.path.join(TP, "check_tree_page.py"), "--tree", tree, "--atlas-data", ad, "--page", page])

if __name__ == "__main__": main()

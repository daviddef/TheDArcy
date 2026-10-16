#!/usr/bin/env python3
"""A living person is a name, a relationship, a town and a country. Prove it held.

THE RULE (David, 16 October 2026, version 2, replacing the 100-year bound): a
living person is 80 or younger by year with no death or burial recorded and no
public source; a person with no birth year is not living. A living person is
shown by NAME, RELATIONSHIP, TOWN and COUNTRY, and nothing else: no date, no
record, no source, no note, no occupation, no photograph, no structured data.
Their page is noindex, which takes it out of the sitemap and the search index.
EVERY PERSON THE ARCHIVE NAMES HAS A PAGE. A child with a known birth year follows
the same standard as anyone living. Two kinds of person are held out and
published nowhere: an undated person with a living parent, who might be a child,
and the person promised privacy, by id.

This gate needs only what is COMMITTED and what is BUILT, so it can run in the
deploy, where the GEDCOM is not and must never be. It is in check_archive.py's
list for that reason. check_living.py adds what only the tree can say: who is
living (computed there with the kit's living_rule.py, apart from the generator),
who is held out, and the living person's own dates and notes, searched for in
everything the site serves and everything the repository tracks.

WHAT IS CHECKED (each rule below has a planted fault in `controls()` that must
make it fail; a rule that has never been seen to fail has not been shown to be
able to):

  data-keys     every record flagged living holds only the keys a living record
                may hold, and every one of those but name/relatives/place is empty
  data-marriage a living person's marriage carries no date, no place, no divorce
  data-place    the place is a town and a country: no digit, no street, no
                institution (a hospital, a care home), at most one comma
  data-refs     a relative is a name AND the id of a page: every parent, brother,
                sister, spouse and child in the data names a person who has a record
  unnamed       nobody is published who the archive does not name: every record
                in relatives.json is named by someone, as a parent, brother,
                sister or spouse
  page-exists   every person who has a record has a page, and every page built
                has a record (the slug rule is people.js's, reproduced)
  named-page    on every person's page, every relative in the record is a link
                to that relative's page; on /direct-line/ so is every sibling;
                in households.json every person named has a page address
  noindex       a living person's page says <meta name="robots" content="noindex">
  no-ld         that page carries no structured data at all
  headings      that page has only the headings a living page has, and no table
  no-photo      that page has no <img>
  no-year       that page shows no year anywhere: title, description, heading,
                eyebrow, the "Where" block, and beside every relative
  sitemap       no living page is in sitemap-*.xml
  search        no living page is in searchindex.json, and none is in whoindex.json
  control       the same checks on a DEAD person's page give the opposite answer
                (indexable, structured data, in the sitemap), so a detector that
                has stopped detecting is caught rather than read as a clean build
  held-out      the people held out (decisions.json: the person promised privacy
                by id, and, by rule, every undated person with a living parent) are in no committed
                data file, no tsv, no built page and no served index: their ids
                appear nowhere, there is no record for them, and the count of
                those left out was measured and written
  not-empty     a build with no living pages, or none of the dead, does not pass

    python3 tools/check_living_standard.py              # gate the build
    python3 tools/check_living_standard.py --controls   # also plant every fault
"""
import copy, glob, html, json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outdir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")

# Mirrored from tools/build_site_data.py on purpose and not imported from it: a
# gate that reads its allowance from the thing it gates widens when that does.
LIVING_KEYS = {
    "id", "mh", "name", "surname", "sex", "ahn", "gen", "born", "bornPlace", "died",
    "diedPlace", "cause", "burial", "occupation", "life", "place", "spouses",
    "parents", "siblings", "sources", "notes", "living",
}
EMPTY_STRINGS = ("mh", "born", "bornPlace", "died", "diedPlace", "cause", "burial",
                 "occupation", "life")
EMPTY_LISTS = ("sources", "notes")
SPOUSE_KEYS = {"name", "id", "living", "married", "marriedPlace", "divorced",
               "children", "place"}
REL_KEYS = {"name", "id"}          # a parent or a brother or sister: a name and the id of a page
# A place that is a building, a road or an institution is not a town. Mirrored
# from tools/build_site_data.py on purpose, like LIVING_KEYS.
NOT_A_TOWN = re.compile(
    r"\b(hospital|clinic|nursing|maternity|medical|infirmary|farm|ranch|station|"
    r"street|st\.|road|rd\.?|avenue|ave|drive|lane|court|crescent|place|house|"
    r"school|university|college|church|chapel|prison|barracks|lodge|home|estate|"
    r"po box|private bag)\b", re.I)
SPOUSE_EMPTY = ("married", "marriedPlace", "divorced")
# What a living person's page may have a heading for. (PersonTree draws its own
# h3s; these are the ones this archive's template and the kit's produce.)
HEADINGS = {"Where", "Family", "Parents", "Married", "Brothers and sisters",
            "Children", "Where this comes from", "Brother or sister",
            "Parents and siblings", "Spouse", "Spouses"}
YEAR = re.compile(r"\b(?:1[0-9]|20)\d\d\b")
NOINDEX = re.compile(r'<meta[^>]*name=["\']robots["\'][^>]*noindex', re.I)


def kebab(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _j(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---- the world: committed data, built pages ---------------------------------

def _text(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def load_data(data_dir=DATA):
    anc = _j(os.path.join(data_dir, "ancestors.json"))
    fams = _j(os.path.join(data_dir, "families.json"))
    line = _j(os.path.join(data_dir, "line.json"))
    relatives = _j(os.path.join(data_dir, "relatives.json"))
    # Every other committed file that could carry an id: the rest of the site's
    # data, and the tsv files ancestry.py writes. decisions.json is the one file
    # that says WHICH ids are held out, so it is read, not searched.
    files = {}
    for f in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        b = os.path.basename(f)
        if b in ("ancestors.json", "families.json", "line.json", "relatives.json", "decisions.json"):
            continue
        files["site/src/data/" + b] = _text(f)
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "*.tsv"))):
        files["data/" + os.path.basename(f)] = _text(f)
    dec = {}
    try:
        dec = _j(os.path.join(data_dir, "decisions.json")).get("decisions", {})
    except Exception:
        pass
    held = list((dec.get("heldOutIds") or {}).get("value") or [])
    return {"ancestors": anc, "families": fams, "line": line, "relatives": relatives,
            "files": files, "held": held, "decisions": dec}


def page_records(data):
    """Everybody who has a page, in the order lib/people.js inserts them: the
    direct line, the family clusters, then the relatives (marked `_rel`)."""
    order = {}
    for a in data["ancestors"]:
        order.setdefault(a["id"], {}).update(a)
    for f in data["families"]:
        for m in f["members"]:
            order.setdefault(m["id"], {}).update(m)
    out = list(order.values())
    for r in data.get("relatives") or []:
        if r["id"] not in order:
            out.append({**r, "_rel": True})
    return out


def _yr(r):
    m = re.search(r"\d{4}", (r.get("born") or r.get("died") or ""))
    return m.group(0) if m else ""


def slugs(recs):
    """lib/people.js's slug rule, reproduced in three phases so that adding
    people moved no address already published:
      1. the dead of the direct line and the clusters, among themselves;
      2. the dead who are only relatives: the bare name, then name and year;
      3. the living, from what is left."""
    base = [r for r in recs if not r.get("_rel")]
    rel = [r for r in recs if r.get("_rel")]
    dead = [r for r in base if not r.get("living")]
    counts = {}
    for r in dead:
        counts[kebab(r["name"])] = counts.get(kebab(r["name"]), 0) + 1
    used, out = set(), {}
    for r in dead:
        b = kebab(r["name"]) or "unnamed"
        s = b
        if counts[b] > 1:
            y = _yr(r)
            s = f"{b}-{y}" if y else b
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    for r in (x for x in rel if not x.get("living")):
        b = kebab(r["name"]) or "unnamed"
        s = b
        if s in used and _yr(r):
            s = f"{b}-{_yr(r)}"
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    for r in (x for x in recs if x.get("living")):
        b = kebab(r["name"]) or "unnamed"
        s = b
        if s in used:
            s = f"{b}-living"
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    return out


def load_pages(dist):
    """Every people/<slug>/index.html, keyed by slug. Plus the served indexes."""
    pages = {}
    for p in glob.glob(os.path.join(dist, "people", "*", "index.html")):
        slug = os.path.basename(os.path.dirname(p))
        pages[slug] = open(p, encoding="utf-8", errors="replace").read()
    sitemap = ""
    for p in glob.glob(os.path.join(dist, "sitemap*.xml")):
        sitemap += open(p, encoding="utf-8", errors="replace").read()
    def jl(name):
        p = os.path.join(dist, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    served = {}
    for dp, _, fs in os.walk(dist):
        for f in fs:
            if f.lower().endswith((".json", ".xml", ".txt")):
                q = os.path.join(dp, f)
                served[os.path.relpath(q, dist).replace(os.sep, "/")] = \
                    open(q, encoding="utf-8", errors="replace").read()
    served_pages = {}
    for name in ("direct-line",):
        p = os.path.join(dist, name, "index.html")
        if os.path.exists(p):
            served_pages[name] = open(p, encoding="utf-8", errors="replace").read()
    hh = None
    hp = os.path.join(DATA, "households.json")
    if os.path.exists(hp):
        hh = _j(hp)
    return {"pages": pages, "sitemap": sitemap, "served": served,
            "served_pages": served_pages, "households": hh,
            "search": jl("searchindex.json"), "who": jl("whoindex.json")}


# ---- the rules --------------------------------------------------------------

def walk_living(o, path, out):
    """Every dict flagged living anywhere in a JSON value."""
    if isinstance(o, dict):
        if o.get("living") is True:
            out.append((path, o))
        for k, v in o.items():
            walk_living(v, f"{path}.{k}", out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_living(v, f"{path}[{i}]", out)


def _bad_place(pl):
    """A town and a country, or one of them: no digit, no question mark, no more
    than one comma, and no part of it that is a building, a road or an institution."""
    return bool(pl) and (bool(re.search(r"[\d?]", pl)) or pl.count(",") > 1
                         or any(NOT_A_TOWN.search(x) for x in pl.split(",")))


def rule_data(data, extra_files=()):
    fails = []
    n = 0
    found = []
    for name in ("ancestors", "families", "line", "relatives"):
        walk_living(data[name], name, found)
    for path, d in found:
        n += 1
        is_record = "surname" in d and "born" in d
        if is_record:
            extra = set(d) - LIVING_KEYS
            if extra:
                fails.append(("data-keys", f"{path}: key(s) {sorted(extra)} on a living record"))
            for k in EMPTY_STRINGS:
                if d.get(k):
                    fails.append(("data-keys", f"{path}: {k} is not empty on a living record"))
            for k in EMPTY_LISTS:
                if d.get(k):
                    fails.append(("data-keys", f"{path}: {k} is not empty on a living record"))
            for k in ("parents", "siblings"):
                for i, e in enumerate(d.get(k) or []):
                    if not isinstance(e, dict) or set(e) - REL_KEYS:
                        fails.append(("data-keys", f"{path}.{k}[{i}]: a relative is a name and an id and nothing more"))
            if _bad_place(d.get("place") or ""):
                fails.append(("data-place", f"{path}: place is not a town and a country"))
            for i, s in enumerate(d.get("spouses") or []):
                for k in SPOUSE_EMPTY:
                    if s.get(k):
                        fails.append(("data-marriage", f"{path}.spouses[{i}]: {k} on a living person's marriage"))
        else:                                   # a spouse entry
            extra = set(d) - SPOUSE_KEYS
            if extra:
                fails.append(("data-keys", f"{path}: key(s) {sorted(extra)} on a living spouse"))
            for k in SPOUSE_EMPTY:
                if d.get(k):
                    fails.append(("data-marriage", f"{path}: {k} on a living spouse"))
            if _bad_place(d.get("place") or ""):
                fails.append(("data-place", f"{path}: place is not a town and a country"))
    # any other data file that flags somebody living
    for fpath in extra_files:
        try:
            v = _j(fpath)
        except Exception:
            continue
        hits = []
        walk_living(v, os.path.basename(fpath), hits)
        for path, d in hits:
            extra = set(d) - LIVING_KEYS - SPOUSE_KEYS
            if extra:
                fails.append(("data-keys", f"{path}: key(s) {sorted(extra)} on a living record"))
    return fails, n


def iter_rows(data):
    """Every record in every data file, ONE ROW AT A TIME: the same person is a row
    in ancestors.json and again in families.json, and a check made on the merged
    record would see only whichever copy was merged last."""
    for src in ("ancestors", "line", "relatives"):
        for r in data.get(src) or []:
            yield src, r
    for f in data["families"]:
        for m in f["members"]:
            yield "families", m


def rule_refs(data, recs):
    """A relative is a name AND the id of a page. Everyone the data names as a
    parent, a brother or sister, a spouse or a child must be a person with a
    record; and nobody is published whom nobody names."""
    fails = []
    ids = {r["id"] for r in recs}
    named_by = set()
    base_ids = {r["id"] for src, r in iter_rows(data) if src != "relatives"}
    for src, r in iter_rows(data):
        for k in ("parents", "siblings"):
            for e in r.get(k) or []:
                if not isinstance(e, dict) or not e.get("id"):
                    fails.append(("data-refs", f"a {k[:-1] if k == 'parents' else 'sibling'} is named without the id of a page ({r['id']})"))
                    continue
                if e["id"] not in ids:
                    fails.append(("data-refs", f"a {k} entry names a person who has no record ({e['id']})"))
                if r["id"] in base_ids:
                    named_by.add(e["id"])
        for s in r.get("spouses") or []:
            if s.get("name") and not s.get("id"):
                fails.append(("data-refs", f"a spouse is named without the id of a page ({r['id']})"))
            if s.get("id"):
                if s["id"] not in ids:
                    fails.append(("data-refs", f"a spouse entry names a person who has no record ({s['id']})"))
                if r["id"] in base_ids:
                    named_by.add(s["id"])
            for c in s.get("children") or []:
                if c not in ids:
                    fails.append(("data-refs", f"a child is listed who has no record ({c})"))
    for src, r in iter_rows(data):
        if src == "relatives" and r["id"] not in named_by:
            fails.append(("unnamed", f"{r['id']} has a record and no person with a page names them"))
    return fails


def _between(src, a, b):
    i = src.find(a)
    if i < 0:
        return ""
    j = src.find(b, i + len(a))
    return src[i + len(a): j if j > 0 else None]


def page_fails(slug, src):
    """What is wrong with ONE living person's page."""
    fails = []
    if not NOINDEX.search(src):
        fails.append(("noindex", f"/people/{slug}/ is not noindex"))
    if "ld+json" in src:
        fails.append(("no-ld", f"/people/{slug}/ carries structured data"))
    main = _between(src, "<main", "</main>")
    for m in re.finditer(r"<(h[1-6])[^>]*>(.*?)</\1>", main, re.S):
        tag, txt = m.group(1), html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        if tag == "h1":
            continue
        if txt not in HEADINGS:
            fails.append(("headings", f"/people/{slug}/ has a heading «{txt[:30]}»"))
    if "<table" in main:
        fails.append(("headings", f"/people/{slug}/ has a table"))
    if "<img" in main:
        fails.append(("no-photo", f"/people/{slug}/ has an image"))
    # No year ANYWHERE on a living person's page: not in the title or the
    # description, not in the heading or the eyebrow, and not beside a relative —
    # the template shows no relative's lifespan on a living page, so the rule can
    # be tested as a rule and not judged. (A dead person's page is full of them.)
    body = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", main)
    chunks = [
        _between(src, "<title>", "</title>"),
        " ".join(re.findall(r'<meta[^>]*content=["\']([^"\']*)["\']', src[: src.find("</head>")])),
        body,
    ]
    for chunk in chunks:
        if YEAR.search(html.unescape(re.sub(r"<[^>]+>", " ", chunk))):
            fails.append(("no-year", f"/people/{slug}/ shows a year"))
            break
    return fails


def _linked(src, slug):
    """Does this page link to /people/<slug>/ ?"""
    return re.search(r'href=["\'][^"\']*/people/' + re.escape(slug) + r'/?(?:["\'#?])', src) is not None


def rule_named(recs, sl, world, data):
    """EVERY NAME HAS A PAGE, AND THE PAGE IS LINKED. On a person's page every
    relative in the record is a link to that relative's page; on /direct-line/ so
    is every sibling; in households.json every person named has an address."""
    fails = []
    by_id = {r["id"]: r for r in recs}
    pages = world["pages"]
    checked = 0
    for r in recs:
        s = sl[r["id"]]
        if s not in pages:
            continue                              # page-exists says so
        want = [e["id"] for k in ("parents", "siblings") for e in (r.get(k) or [])]
        for sp in r.get("spouses") or []:
            if sp.get("id"):
                want.append(sp["id"])
            want += [c for c in sp.get("children") or []]
        for rid in want:
            if rid in sl:
                checked += 1
                if not _linked(pages[s], sl[rid]):
                    fails.append(("named-page", f"/people/{s}/ names a relative without linking their page (/people/{sl[rid]}/)"))
    dl = world["served_pages"].get("direct-line")
    if dl is not None:
        for g in data["line"]:
            if g.get("living"):
                continue
            for e in g.get("siblings") or []:
                if e.get("id") in sl:
                    checked += 1
                    if not _linked(dl, sl[e["id"]]):
                        fails.append(("named-page", f"/direct-line/ names a sibling without linking their page (/people/{sl[e['id']]}/)"))
    hh = world["households"]
    if hh is not None:
        for row in hh.get("rows", []):
            who = [(row.get("a"), row.get("aSlug"))]
            if row.get("b"):
                who.append((row.get("b"), row.get("bSlug")))
            who += [(k.get("name"), k.get("slug")) for k in row.get("kids", [])]
            for name, slug in who:
                if name and not slug:
                    fails.append(("named-page", "a household names a person and gives them no page"))
                elif slug and slug not in set(sl.values()):
                    fails.append(("named-page", f"a household links /people/{slug}/ and no such person has a page"))
    return fails, checked


def rule_pages(recs, sl, world):
    fails = []
    pages = world["pages"]
    living = [r for r in recs if r.get("living")]
    dead = [r for r in recs if not r.get("living")]
    for r in recs:
        s = sl[r["id"]]
        if s not in pages:
            fails.append(("page-exists", f"the person {r['id']} should have /people/{s}/ and it is not built"))
            continue
        if r.get("living"):
            fails += page_fails(s, pages[s])
    # the other direction: a built people page the data does not account for
    known = set(sl.values())
    for s in pages:
        if s not in known:
            fails.append(("page-exists", f"/people/{s}/ is built and no record accounts for it"))
    return fails, len(living), len(dead)


def rule_served(recs, sl, world):
    fails = []
    live_slugs = {sl[r["id"]] for r in recs if r.get("living")}
    sm = world["sitemap"]
    locs = re.findall(r"<loc>([^<]*)</loc>", sm)
    for s in live_slugs:
        if any(l.rstrip("/").endswith(f"/people/{s}") for l in locs):
            fails.append(("sitemap", f"/people/{s}/ is in the sitemap"))
    srch = world["search"]
    if srch is not None:
        for row in srch:
            h = (row.get("h") or row.get("href") or "") if isinstance(row, dict) else ""
            m = re.search(r"/people/([^/?#]+)", h)
            if m and m.group(1) in live_slugs:
                fails.append(("search", f"/people/{m.group(1)}/ is in the search index"))
    who = world["who"]
    if who is not None:
        for row in who:
            if isinstance(row, list) and len(row) > 1 and row[1] in live_slugs:
                fails.append(("search", f"/people/{row[1]}/ is in whoindex.json"))
    return fails


def rule_control(recs, sl, world):
    """The same detectors, pointed at a person who is dead, must say the opposite.
    If they do not, the build is not clean: the detectors are blind."""
    fails = []
    dead = [r for r in recs if not r.get("living")]
    pages = world["pages"]
    probe = None
    for r in dead:
        s = sl[r["id"]]
        if s in pages:
            probe = (s, pages[s])
            break
    if probe is None:
        return [("control", "no dead person's page to test the detectors against")]
    s, src = probe
    if NOINDEX.search(src):
        fails.append(("control", f"a DEAD person's page (/people/{s}/) is noindex — the noindex detector (or the build) is wrong"))
    if "ld+json" not in src:
        fails.append(("control", f"a DEAD person's page (/people/{s}/) carries no structured data — the structured-data detector reads nothing"))
    main = _between(src, "<main", "</main>")
    if "<table" not in main:
        fails.append(("control", f"a DEAD person's page (/people/{s}/) has no table — the table detector reads nothing"))
    if not YEAR.search(html.unescape(re.sub(r"<[^>]+>", " ", main))):
        fails.append(("control", f"a DEAD person's page (/people/{s}/) shows no year — the year detector reads nothing"))
    locs = re.findall(r"<loc>([^<]*)</loc>", world["sitemap"])
    if locs and not any(l.rstrip("/").endswith(f"/people/{s}") for l in locs):
        fails.append(("control", f"a DEAD person's page (/people/{s}/) is not in the sitemap — the sitemap check reads nothing"))
    if not locs:
        fails.append(("control", "the sitemap is empty or unread"))
    return fails


def _quoted(i):
    return re.compile(r'(?<![A-Za-z0-9@])' + re.escape(i) + r'(?![A-Za-z0-9@])')


def rule_held(data, world):
    """The held-out people are not here. Ids only: this gate has no tree, and
    must not have a name, so it looks for what the data CAN carry: an id."""
    fails = []
    held = data.get("held") or []
    if not held:
        fails.append(("held-out", "decisions.json declares no held-out id (heldOutIds), so there is nothing to prove absent"))
    rules = (data.get("decisions") or {}).get("heldOutRules", {}).get("value") or {}
    if "possible-minor" not in rules or "dna-tester" not in rules:
        fails.append(("held-out", "decisions.json does not declare both held-out rules (heldOutRules)"))
    blobs = {
        "ancestors.json": json.dumps(data["ancestors"], ensure_ascii=False),
        "families.json": json.dumps(data["families"], ensure_ascii=False),
        "line.json": json.dumps(data["line"], ensure_ascii=False),
        "relatives.json": json.dumps(data.get("relatives") or [], ensure_ascii=False),
    }
    blobs.update(data.get("files") or {})
    for name, text in (world.get("served") or {}).items():
        blobs["dist/" + name] = text
    for hid in held:
        rx = _quoted(hid)
        for name, text in blobs.items():
            if rx.search(text):
                fails.append(("held-out", f"a held-out id is in {name}"))
    # the build says how many it left out; a count that is not there means the
    # generator never looked
    pub = {}
    try:
        pub = (_j(os.path.join(DATA, "living.json")).get("published") or {})
    except Exception:
        pass
    ho = pub.get("heldOut")
    if not isinstance(ho, dict) or not all(isinstance(ho.get(k), int) for k in
                                           ("dnaTester", "possibleMinors", "total")):
        fails.append(("held-out", "living.json carries no measured count of the people left out"))
    elif ho["total"] != ho["dnaTester"] + ho["possibleMinors"]:
        fails.append(("held-out", "the counts of people left out do not add up"))
    return fails


def run(data, world, extra_files=()):
    recs = page_records(data)
    sl = slugs(recs)
    fails, nrec = rule_data(data, extra_files)
    fails += rule_refs(data, recs)
    f2, nl, nd = rule_pages(recs, sl, world)
    fails += f2
    f3, nchecked = rule_named(recs, sl, world, data)
    fails += f3
    fails += rule_served(recs, sl, world)
    fails += rule_control(recs, sl, world)
    fails += rule_held(data, world)
    if nl == 0:
        fails.append(("not-empty", "no living person has a page in this data — a build with nobody to check proves nothing"))
    if nd == 0 or len(world["pages"]) == 0:
        fails.append(("not-empty", "no page was built under /people/ — an empty build is not a clean build"))
    return fails, {"living": nl, "dead": nd, "records": nrec, "pages": len(world["pages"]),
                   "slugs": sl, "links": nchecked}


# ---- the planted faults -------------------------------------------------------

def controls(data, world):
    """Plant each fault in a COPY and demand the gate say so. Returns (ok, lines)."""
    lines, ok = [], True
    recs = page_records(data)
    sl = slugs(recs)
    live = next(r for r in recs if r.get("living"))
    ls = sl[live["id"]]

    def expect(rule, label, d, w):
        nonlocal ok
        fails, _ = run(d, w)
        hit = [f for f in fails if f[0] == rule]
        good = bool(hit)
        ok &= good
        lines.append(f"  {'caught ' if good else 'MISSED '} {rule:13s} {label}")

    def clone():
        return copy.deepcopy(data), {**world, "pages": dict(world["pages"]),
                                     "search": copy.deepcopy(world["search"]),
                                     "who": copy.deepcopy(world["who"]),
                                     "served": dict(world.get("served") or {}),
                                     "served_pages": dict(world.get("served_pages") or {}),
                                     "households": copy.deepcopy(world.get("households"))}

    def src_row(d):
        for a in d["ancestors"]:
            if a.get("living"):
                return a
        for f in d["families"]:
            for m in f["members"]:
                if m.get("living"):
                    return m

    def any_row_with(d, key):
        """Any record, living or dead, that has something under `key`."""
        for a in d["ancestors"]:
            if a.get(key):
                return a
        for f in d["families"]:
            for m in f["members"]:
                if m.get(key):
                    return m

    # the data
    d, w = clone(); src_row(d)["born"] = "1 JAN 1799"
    expect("data-keys", "a birth date on a living record", d, w)
    d, w = clone(); src_row(d)["occupation"] = "plumber"
    expect("data-keys", "an occupation on a living record", d, w)
    d, w = clone(); src_row(d)["notes"] = ["a family note"]
    expect("data-keys", "a note on a living record", d, w)
    d, w = clone(); src_row(d)["sources"] = ["a census"]
    expect("data-keys", "a source on a living record", d, w)
    d, w = clone(); src_row(d)["cause"] = "an illness"
    expect("data-keys", "a cause on a living record", d, w)
    d, w = clone(); src_row(d)["photo"] = "x.jpg"
    expect("data-keys", "an unknown field (photo) on a living record", d, w)
    d, w = clone(); src_row(d)["place"] = "12 High Street, Leeds, England"
    expect("data-place", "a street address as the place", d, w)
    d, w = clone(); src_row(d)["place"] = "Mercy Hospital, Leeds, England"
    expect("data-place", "an institution as the place", d, w)
    d, w = clone(); src_row(d)["place"] = "Leeds, West Yorkshire, England"
    expect("data-place", "a county as well as a town and a country", d, w)
    d, w = clone(); src_row(d)["parents"] = [{"name": "A. N. Other", "id": "@I0@", "born": "1799"}]
    expect("data-keys", "a date inside a living person's parent entry", d, w)
    d, w = clone()
    r = src_row(d); r["spouses"] = (r.get("spouses") or [{"name": "X", "id": "", "living": True,
                                      "married": "", "marriedPlace": "", "divorced": "", "children": []}])
    r["spouses"][0]["married"] = "1 JUN 1799"
    expect("data-marriage", "a marriage date on a living person", d, w)
    # the page
    d, w = clone(); w["pages"][ls] = NOINDEX.sub("<meta name=\"robots\" content=\"index\"", w["pages"][ls])
    expect("noindex", "a living page that is not noindex", d, w)
    d, w = clone(); w["pages"][ls] = w["pages"][ls].replace("</head>", '<script type="application/ld+json">{"@type":"Person"}</script></head>', 1)
    expect("no-ld", "JSON-LD Person on a living page", d, w)
    d, w = clone(); w["pages"][ls] = w["pages"][ls].replace("</main>", "<h2>The record</h2><table><tr><td>Born</td></tr></table></main>", 1)
    expect("headings", "a «The record» table on a living page", d, w)
    d, w = clone(); w["pages"][ls] = w["pages"][ls].replace("</main>", '<h2>Sources attached in the tree</h2></main>', 1)
    expect("headings", "a sources heading on a living page", d, w)
    d, w = clone(); w["pages"][ls] = w["pages"][ls].replace("</main>", '<img src="/img/x.jpg" alt=""></main>', 1)
    expect("no-photo", "a photograph on a living page", d, w)
    d, w = clone(); w["pages"][ls] = re.sub(r"(<h1[^>]*>)", r"\g<1>1799 ", w["pages"][ls], count=1)
    expect("no-year", "a year in a living page's heading", d, w)
    d, w = clone(); w["pages"][ls] = re.sub(r"<title>", "<title>b. 1799 ", w["pages"][ls], count=1)
    expect("no-year", "a year in a living page's title", d, w)
    d, w = clone(); w["pages"][ls] = w["pages"][ls].replace("</main>", "<p>Parents: A. N. Other (1799\u20131801)</p></main>", 1)
    expect("no-year", "a relative's lifespan beside a living person", d, w)
    d, w = clone(); del w["pages"][ls]
    expect("page-exists", "a living person with no page built", d, w)
    # a name is a name AND the id of a page
    d, w = clone(); r = any_row_with(d, "siblings"); r["siblings"][0] = {"name": r["siblings"][0]["name"], "id": ""}
    expect("data-refs", "a brother or sister named without the id of a page", d, w)
    d, w = clone(); r = any_row_with(d, "siblings"); r["siblings"][0] = {"name": "Nobody", "id": "@I999999999@"}
    expect("data-refs", "a brother or sister whose id has no record", d, w)
    d, w = clone(); r = any_row_with(d, "parents"); r["parents"][0] = {"name": r["parents"][0]["name"], "id": ""}
    expect("data-refs", "a parent named without the id of a page", d, w)
    d, w = clone(); r = any_row_with(d, "spouses"); r["spouses"][0] = {**r["spouses"][0], "id": "", "name": "A Name"}
    expect("data-refs", "a spouse named without the id of a page", d, w)
    d, w = clone(); r = any_row_with(d, "spouses"); r["spouses"][0] = {**r["spouses"][0], "children": ["@I999999999@"]}
    expect("data-refs", "a child listed who has no record", d, w)
    d, w = clone(); d["relatives"].append({**copy.deepcopy(d["relatives"][0]), "id": "@I888888888@", "name": "Planted Person"})
    expect("unnamed", "a person published whom nobody names", d, w)
    # every name is linked to its page
    d, w = clone()
    r = next(x for x in page_records(d) if x.get("siblings") and sl.get(x["id"]) in w["pages"])
    tgt = sl[r["siblings"][0]["id"]]
    w["pages"][sl[r["id"]]] = re.sub(r'href=["\'][^"\']*/people/' + re.escape(tgt) + r'/?["\']', 'href="#"', w["pages"][sl[r["id"]]])
    expect("named-page", "a brother or sister named on a person's page without a link to theirs", d, w)
    d, w = clone()
    g = next(x for x in d["line"] if not x.get("living") and x.get("siblings"))
    tgt = sl[g["siblings"][0]["id"]]
    w["served_pages"]["direct-line"] = re.sub(r'href=["\'][^"\']*/people/' + re.escape(tgt) + r'/?["\']', 'href="#"', w["served_pages"]["direct-line"])
    expect("named-page", "a sibling on /direct-line/ with no link to their page", d, w)
    if w["households"] and w["households"].get("rows"):
        d, w = clone(); w["households"]["rows"][0]["aSlug"] = ""
        expect("named-page", "a household naming a person who has no page", d, w)
    # served
    d, w = clone(); w["sitemap"] += f"<url><loc>https://x.example/people/{ls}/</loc></url>"
    expect("sitemap", "a living page in the sitemap", d, w)
    if w["search"] is not None:
        d, w = clone(); w["search"].append({"k": "Person", "t": "x", "h": f"/people/{ls}/"})
        expect("search", "a living page in the search index", d, w)
    if w["who"] is not None:
        d, w = clone(); w["who"].append(["Some Name", ls, 1])
        expect("search", "a living person in whoindex.json", d, w)
    # the held out
    hid = (data.get("held") or ["@I0@"])[0]
    d, w = clone()
    d["ancestors"][0]["spouses"] = list(d["ancestors"][0].get("spouses") or []) + [
        {"name": "Planted", "id": hid, "living": True, "married": "", "marriedPlace": "",
         "divorced": "", "children": []}]
    expect("held-out", "a held-out id as somebody's spouse", d, w)
    d, w = clone()
    d["families"][0]["members"].append({**copy.deepcopy(src_row(d)), "id": hid})
    expect("held-out", "a held-out id as a record in a family", d, w)
    d, w = clone()
    d["families"][0]["members"][0]["spouses"] = [
        {"name": "Planted", "id": "", "living": False, "married": "", "marriedPlace": "",
         "divorced": "", "children": [hid]}]
    expect("held-out", "a held-out id in somebody's list of children", d, w)
    d, w = clone()
    d["relatives"].append({**copy.deepcopy(d["relatives"][0]), "id": hid})
    expect("held-out", "a held-out id as a record among the relatives", d, w)
    d, w = clone(); r = any_row_with(d, "siblings"); r["siblings"].append({"name": "Planted", "id": hid})
    expect("held-out", "a held-out id as somebody's brother or sister", d, w)
    d, w = clone(); r = any_row_with(d, "parents"); r["parents"].append({"name": "Planted", "id": hid})
    expect("held-out", "a held-out id as somebody's parent", d, w)
    d, w = clone(); d["files"] = {**d["files"], "data/planted.tsv": f"1\t2\t{hid}\tx\n"}
    expect("held-out", "a held-out id in a committed tsv", d, w)
    d, w = clone(); d["files"] = {**d["files"], "site/src/data/planted.json": json.dumps({"who": hid})}
    expect("held-out", "a held-out id in another committed data file", d, w)
    d, w = clone(); w["served"] = {**w["served"], "planted.json": json.dumps([hid])}
    expect("held-out", "a held-out id in a file the site serves", d, w)
    d, w = clone(); d["held"] = []
    expect("held-out", "no held-out id declared at all", d, w)
    d, w = clone(); d["decisions"] = {k: v for k, v in d["decisions"].items() if k != "heldOutRules"}
    expect("held-out", "the held-out rules not declared", d, w)
    # the positive control and the empty build
    dead_slug = next(sl[r["id"]] for r in recs if not r.get("living") and sl[r["id"]] in world["pages"])
    d, w = clone(); w["pages"][dead_slug] = NOINDEX.sub("", w["pages"][dead_slug]).replace("</head>", '<meta name="robots" content="noindex"></head>', 1)
    expect("control", "a dead page that is noindex (detector reads everything as noindex)", d, w)
    d, w = clone(); w["pages"] = {}
    expect("not-empty", "an empty build", d, w)
    d, w = clone(); w["sitemap"] = ""
    expect("control", "an empty sitemap", d, w)
    return ok, lines


def main(argv):
    dist = outdir.out()
    world = load_pages(dist)
    data = load_data()
    extra = [f for f in glob.glob(os.path.join(DATA, "*.json"))
             if os.path.basename(f) not in ("ancestors.json", "families.json", "line.json",
                                            "relatives.json", "living.json", "decisions.json")]
    if os.environ.get("ARCHIVE_OUT"):
        print(outdir.note(dist))
    if not os.path.isdir(dist) or not glob.glob(os.path.join(dist, "people", "*", "index.html")):
        print(f"  FAIL  living-standard  no built person pages under {os.path.relpath(dist, ROOT)}/people — build first")
        return 1
    fails, info = run(data, world, extra)
    for rule, msg in fails[:40]:
        print(f"  FAIL  {rule:14s} {msg}")
    if len(fails) > 40:
        print(f"  ...   {len(fails) - 40} more")
    if "--controls" in argv:
        ok, lines = controls(data, world)
        print("  planted faults, each in a copy of the data or the built pages:")
        print("\n".join(lines))
        if not ok:
            print("  FAIL  living-standard  a planted fault was NOT caught — the gate cannot fail on that rule")
            return 1
    if fails:
        print(f"  FAIL  living-standard  {len(fails)} finding(s)")
        return 1
    print(f"  ok    living-standard  {info['living']} living people have a page; each is noindex, "
          f"carries no structured data, no table, no image and no year anywhere; none is in the "
          f"sitemap, the search index or whoindex.json; {info['dead']} dead pages behave the opposite "
          f"way; every living record holds only name, relatives and place; {info['links']} relatives "
          f"named on a page, each a link to a page that exists")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

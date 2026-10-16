#!/usr/bin/env python3
"""A living person is a name, a relationship, a town and a country. The tree says who is living and what is NOT allowed.

THE RULE (David, 16 October 2026, version 2): a person is LIVING when they are 80
or younger by year, with no death or burial recorded and no public source; a
person with no birth year is not living. A living person is named with their
relationships and their town and country, and nothing more: no date, no record,
no source, no note, no occupation, no photograph, no structured data. Every
person the archive names has a page. A child with a known birth year follows the
same standard as anyone living. Two kinds of person are held out and published
nowhere: an undated person with a living parent, who might be a child, and the
person promised privacy, by id.

THE DEFINITION OF LIVING IS THE KIT'S (kit/tools/living_rule.py), written once for
every archive. What this file adds is that it does not take the generator's word
for the FACTS that definition is applied to. tools/gedcom.py prepares a birth
year, a recorded death and a list of citations; this gate reads the same GEDCOM
again, through the tokeniser only, and prepares them itself (own_facts), then
asks the kit. It then holds the generator to the answer, person by person, for
every one of the tree's people, not only the ones published.

It reads the tree, which is the only place that knows who is living, and what it
reads out is no longer their NAMES but everything ELSE about them:

  · every full date attached to a living person's events (day, month, year),
    in the five spellings a page might use — less the dates a dead person also
    carries, which cannot be told apart;
  · every note, source title, occupation, cause of death and place longer than a
    town and a country that the tree holds for a living person — less what a
    dead person's record also holds, for the same reason.

and it searches for them in EVERYTHING THE SITE SERVES (every page, every .json,
the sitemap) and EVERYTHING THE REPOSITORY TRACKS, because every committed file
in this repository is public and a generator that put a living person's
birthday in a data file leaks it whether or not a page ever prints it. The
messages name the file and the kind of thing found, never the thing: a log that
printed it would be the leak.

It also proves the rulings about WHO is published:

  · the generator's verdict (living or not) is the gate's, for every person in the
    tree, and the data's `living` flag is the tree's for every record and every
    spouse entry;
  · a person the tree RECORDS as deceased, a person with a public source, a person
    with no birth year and a person over 80 are none of them flagged living;
  · the people held out (the person promised privacy, by id; every undated person
    with a living parent, by rule) are computed here from the tree by this file's
    own implementation,
    and not one of them is a record, an id or a name in anything published;
  · the people with a page are EXACTLY those the archive names: the direct line
    and the thirteen surnames, plus their parents, brothers and sisters and
    spouses, and nobody else. The tree holds thousands more, and none is published.

And it runs the part that needs only the committed data and the built pages
(tools/check_living_standard.py: noindex, no structured data, nothing in the
sitemap or the search index, only the headings a living page has, every name a
link to a page). That part also runs in the deploy, where there is no tree.
This part cannot, and says so.

    python3 tools/check_living.py             # gate the build
    python3 tools/check_living.py --controls  # plant each fault, show it is caught
"""
import os, sys, json, glob, re, html, subprocess, argparse, copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outdir
import check_living_standard as std

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECL = os.path.join(ROOT, "site", "src", "data", "living.json")
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
        "September", "October", "November", "December"]
FULL = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{4})\b")
TEXT_EXT = (".json", ".astro", ".js", ".mjs", ".md", ".py", ".tsv", ".csv", ".txt", ".html",
            ".yml", ".yaml", ".css", ".xml", ".sh")


def date_forms(raw):
    """Every full date inside one GEDCOM date value — a plain date, or both ends
    of «BET 1 MAR 1949 AND 3 JUN 1950» — as [(key, [forms])]. Each form is a way
    a page might write it, lowercase."""
    out = []
    for m in FULL.finditer(raw or ""):
        d, mon, y = int(m.group(1)), m.group(2).upper(), m.group(3)
        if mon not in MONTHS:
            continue
        i = MONTHS.index(mon)
        forms = [f"{d} {MONTHS[i]} {y}", f"{d} {MONTHS[i].title()} {y}", f"{d} {LONG[i]} {y}",
                 f"{LONG[i]} {d}, {y}", f"{LONG[i]} {d} {y}", f"{y}-{i+1:02d}-{d:02d}",
                 f"{d:02d} {MONTHS[i].title()} {y}"]
        out.append(((d, i + 1, int(y)), sorted({f.lower() for f in forms})))
    return out


def norm(s):
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip().lower()


def harvest(people, families, flags):
    """What the tree holds for a living person that this site may not publish.
    Returns {kind: set(strings)}, each already net of what a dead person also holds."""
    from gedcom import ev
    living = {k: set() for k in ("date", "text", "place")}
    dead = {k: set() for k in ("date", "text", "place")}
    dead_dates = set()
    live_dates = {}

    for pid, p in people.items():
        bucket = living if flags.get(pid) else dead
        for e in p["events"]:
            for key, forms in date_forms(e.get("date", "")):
                if flags.get(pid):
                    live_dates.setdefault(key, set()).update(forms)
                else:
                    dead_dates.add(key)
            for fld in ("detail", "cause", "note", "agency"):
                v = norm(e.get(fld, ""))
                if len(v) >= 14:
                    bucket["text"].add(v[:120])
            pl = norm(e.get("place", ""))
            if len(pl) >= 14 and (pl.count(",") >= 3 or re.search(r"\d", pl)):
                bucket["place"].add(pl)
        for n in p.get("notes", []):
            for chunk in re.split(r"[\n\r]+|(?<=[.!?])\s+", html.unescape(re.sub(r"<[^>]+>", " ", n))):
                v = norm(chunk)
                if len(v) >= 30:
                    bucket["text"].add(v[:120])
        for s in p.get("sources", []):
            v = norm(s)
            if len(v) >= 14:
                bucket["text"].add(v[:120])
    # A marriage is a date about both of the people in it. A couple of the dead
    # is the dead's; a couple with a living partner is a living person's date,
    # and the generator blanks it (build_site_data.spouses).
    for f in families.values():
        both_dead = all(not flags.get(x) for x in (f.get("husb"), f.get("wife"))
                        if x and x in people)
        for e in f["events"]:
            for key, forms in date_forms(e.get("date", "")):
                if both_dead:
                    dead_dates.add(key)
                else:
                    live_dates.setdefault(key, set()).update(forms)
    for key, forms in live_dates.items():
        if key not in dead_dates:
            living["date"].update(forms)
    return {k: living[k] - dead[k] for k in living}


# ---- the facts, prepared HERE and not by the generator -----------------------
# tools/gedcom.py prepares a birth year, a recorded death and a citation list for
# the generator. This gate prepares them again from the raw tree, in its own code,
# so that a generator whose preparation drifts (a date it stops reading, a source
# it starts to count) is caught by something that does not share it. The DECISION
# (living, minor, held out) is the kit's, imported from the same file the
# generator uses: there is one definition.
KIT_TOOLS = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools")
sys.path.insert(0, KIT_TOOLS)
import living_rule as lr           # noqa: E402

CLUSTER_SURNAMES = ["D'Arcy", "Sneyd", "Atkinson", "Murdoch", "Atwell", "Blum", "Keeling",
                    "Creech", "Matson", "Wakefield", "Wright", "Rossiter", "Watt"]
ROOT_PERSON = "@I2@"
TREE_WORDS = ("geni", "wikitree", "family tree", "family trees", "tree index")


def _cite(src, page):
    """What one citation is, as text for lr.public_source()."""
    title = (src.val("TITL") if src else "") or ""
    low = title.lower()
    typ = src.val("_TYPE") if src else ""
    if "familysearch" in low:
        return "FamilySearch: " + title
    if typ in ("Smart Matching", "Discovery"):
        return "MyHeritage family tree: " + title
    if typ == "Collection":
        return ("MyHeritage family tree: " if any(w in low for w in TREE_WORDS)
                else "MyHeritage record collection: ") + title
    return " ".join(x for x in (title, page or "", (src.val("PUBL") if src else "") or "") if x).strip()


def own_tree(path=None):
    """{people: {id: facts}, fams: {id: {...}}} straight from the GEDCOM's tags."""
    import gedcom as G
    recs = G.parse(path) if path else G.parse()
    srcs = {r.xref: r for r in recs if r.tag == "SOUR" and r.xref}
    people, fams = {}, {}
    for r in recs:
        if r.tag == "INDI" and r.xref:
            by = None
            for tag in ("BIRT", "CHR", "BAPM"):
                for e in r.all(tag):
                    d = e.val("DATE")
                    ys = [int(y) for y in re.findall(r"\b(\d{4})\b", d)]
                    if ys and by is None:
                        by = max(ys) if d.upper().startswith("BET") else ys[0]
            nm = r.first("NAME")
            sur = (nm.val("SURN") if nm else "") or (
                nm.value.split("/")[1] if nm and nm.value.count("/") >= 2 else "")
            people[r.xref] = {
                "by": by,
                "dead": any(k.tag in ("DEAT", "BURI") for k in r.kids),
                "cites": [_cite(srcs.get(s.value.strip()), s.val("PAGE")) if s.value.strip().startswith("@")
                          else s.value.strip() for s in r.all("SOUR")],
                "famc": [k.value for k in r.all("FAMC")], "fams": [k.value for k in r.all("FAMS")],
                "surname": sur.strip().lower(),
            }
        elif r.tag == "FAM" and r.xref:
            fams[r.xref] = {"husb": r.val("HUSB"), "wife": r.val("WIFE"),
                            "chil": [k.value for k in r.all("CHIL")]}
    for p in people.values():
        p["parents"] = []
    for f in fams.values():
        for c in f["chil"]:
            if c in people:
                for x in (f["husb"], f["wife"]):
                    if x and x in people and x not in people[c]["parents"]:
                        people[c]["parents"].append(x)
    return {"people": people, "fams": fams}


def own_child_years(tree):
    """{parent: birth year of the youngest child who has one}, derived HERE from this
    gate's own parse of the GEDCOM. It is written a second time on purpose, apart from
    tools/gedcom.py: a gate that took the child's year from the generator it gates would
    agree with it whatever the generator got wrong. A child with no year contributes
    nothing; this reads recorded years and infers none."""
    out = {}
    for c in tree["people"].values():
        if c["by"] is None:
            continue
        for x in c["parents"]:
            if x in tree["people"] and c["by"] > out.get(x, -1):
                out[x] = c["by"]
    return out


def own_living(tree, today=None):
    ty = today or lr.this_year()
    cy = own_child_years(tree)
    return {pid: lr.is_living(p["by"], p["dead"], p["cites"], ty, youngest_child_year=cy.get(pid))
            for pid, p in tree["people"].items()}


def own_held(tree, flags, ids, today=None):
    ty = today or lr.this_year()
    cy = own_child_years(tree)
    out = {}
    for pid, p in tree["people"].items():
        pl = any(flags.get(x) for x in p["parents"])
        if lr.is_held_out(pid, p["by"], p["dead"], p["cites"], pl, ids, ty,
                          youngest_child_year=cy.get(pid)):
            out[pid] = "dna-tester" if pid in set(ids) else "possible-minor"
    return out


def own_pages(tree, held):
    """Everybody who ought to have a page: the numbered ancestors of the root person,
    every bearer of the thirteen surnames, and the parents, brothers and sisters and
    spouses of those — less the held out. Computed here, from the tree's links."""
    P, F = tree["people"], tree["fams"]
    seen, order, queue = set(), [], [ROOT_PERSON]
    while queue:
        pid = queue.pop(0)
        if pid in seen or pid not in P:
            continue
        seen.add(pid)
        for fid in P[pid]["famc"]:
            f = F.get(fid)
            if f:
                queue += [x for x in (f["husb"], f["wife"]) if x]
    scope = set(seen)
    sn = {x.lower() for x in CLUSTER_SURNAMES}
    scope |= {pid for pid, p in P.items() if p["surname"] in sn and pid not in held}
    scope -= set(held)
    rel = set()
    for pid in scope:
        p = P[pid]
        rel |= set(p["parents"])
        for fid in p["famc"]:
            rel |= set(F.get(fid, {}).get("chil", []))
        for fid in p["fams"]:
            f = F.get(fid)
            if f:
                rel |= {f["husb"], f["wife"]}
    rel = {x for x in rel if x in P and x not in held} - scope
    return scope, rel


def arithmetic_fails(tree, flags, ty=None):
    """The rule restated as arithmetic, so a classification that has drifted from
    it is caught even if the kit and the generator drifted together. `flags` is
    the verdict under test."""
    ty = ty or lr.this_year()
    bad = collections_counter()
    cy = own_child_years(tree)
    for pid, p in tree["people"].items():
        v = bool(flags.get(pid))
        pub = lr.public_source(p["cites"])
        if p["dead"] and v:
            bad["recorded-dead"] += 1                 # a recorded death or burial is dead
        if pub and v:
            bad["public-source"] += 1                 # a public source is not living
        # AN UNDATED PERSON IS LIVING IN EXACTLY ONE CASE (David, 16 October 2026): no death,
        # no public source, and a youngest dated child born 60 years ago or less. Stated here
        # in BOTH directions, because a rule that is only ever checked one way drifts the
        # other: «undated and living» without that child is wrong, and so is «undated, that
        # child, and not living».
        recent = pid in cy and ty - cy[pid] <= 60
        if p["by"] is None and v and not (recent and not p["dead"] and not pub):
            bad["undated"] += 1                       # nobody can be shown 80 or younger without a year
        if p["by"] is None and not v and recent and not p["dead"] and not pub:
            bad["undated-parent-of-recent-child-flagged-dead"] += 1
        if p["by"] is not None and ty - p["by"] > 80 and v:
            bad["over-80"] += 1
        if (p["by"] is not None and ty - p["by"] <= 80 and not p["dead"] and not pub) and not v:
            bad["young-flagged-dead"] += 1            # 80 or younger, no death, no public source: living
    return dict(bad)


def held_arith_fails(tree, held):
    """The held-out rule restated as arithmetic (David, 16 October 2026): by rule, only
    an UNDATED person who is not recorded dead, has no public source and has a living
    parent is held out. A child with a known birth year never is, and nobody recorded
    dead or with a public source is. (The person promised privacy is held by id.)"""
    bad = collections_counter()
    P = tree["people"]
    cy_all = own_child_years(tree)
    for pid, rule in held.items():
        if rule != "possible-minor":
            continue
        p = P[pid]
        if p["by"] is not None:
            bad["dated-child-held"] += 1
        if p["dead"]:
            bad["recorded-dead-held"] += 1
        if lr.public_source(p["cites"]):
            bad["public-source-held"] += 1
        # a parent of a recent child is an adult: living, never held out (16 October 2026)
        c = cy_all.get(pid)
        if c is not None and lr.this_year() - c <= 60:
            bad["parent-of-recent-child-held"] += 1
    return dict(bad)


def classify_diff(flags, gen_flags):
    """People about whom the generator and this gate disagree (living or not)."""
    return [p for p in flags if bool(gen_flags.get(p)) != bool(flags.get(p))] + \
           [p for p in gen_flags if p not in flags]


def held_diff(held, gen_held):
    return sorted(set(gen_held) ^ set(held))


def collections_counter():
    import collections
    return collections.Counter()


def held_fails(people, flags, data, corp, held, named_phrases, namesakes):
    """None of the held-out is a record, an id, or a name. A name can only be
    searched for if it is unique: a name two people share proves nothing about
    which of them a page means, so those are counted and not searched, and the
    id check (in the standard) covers them."""
    from gedcom import display
    fails, searched, shared, skipped = [], 0, 0, 0
    ids = set(held)
    for src in ("ancestors", "line", "relatives"):
        for r in data.get(src) or []:
            if r["id"] in ids:
                fails.append(("held", f"{src}: a record for a held-out person"))
    for f in data["families"]:
        for r in f["members"]:
            if r["id"] in ids:
                fails.append(("held", "families: a record for a held-out person"))
    by_name = {}
    for pid, v in people.items():
        by_name.setdefault(norm(display(v)), []).append(pid)
    pats = []
    for pid in ids:
        n = norm(display(people[pid]))
        if len(n.split()) < 2:
            skipped += 1
            continue
        if len(by_name.get(n, [])) > 1:
            shared += 1
            continue
        if n in named_phrases:
            fails.append(("held", "a person named on purpose in prose (living.json) is also held out — one of the two decisions has to give way"))
            continue
        if n in namesakes:
            skipped += 1
            continue
        pats.append(n)
        searched += 1
    if pats:
        rx = re.compile(r"(?<![0-9a-z])(?:" + "|".join(re.escape(x) for x in sorted(pats, key=len, reverse=True)) + r")(?![0-9a-z])")
        # A held-out person's name can sit INSIDE a longer name that somebody with a
        # page carries («Ann Smith» in «Mary Ann Smith»). Those longer names
        # are blanked before the search, so what is left is the bare name, which is
        # the held-out person (or a leak), and not their published relative.
        published = {norm(r.get("name")) for _, r in all_rows(data) if r.get("name")}
        protect = sorted((p for p in published if any(x in p and x != p for x in pats)),
                         key=len, reverse=True)
        prx = re.compile(r"(?<![0-9a-z])(?:" + "|".join(re.escape(p) for p in protect) + r")(?![0-9a-z])") if protect else None
        for name, text in corp.items():
            if prx:
                text = prx.sub(" ", text)
            if rx.search(text):
                fails.append(("held", f"{name}: the name of a held-out person"))
    return fails, {"held": len(ids), "searched": searched, "shared": shared, "skipped": skipped}, pats


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except Exception:
        return None
    return [f for f in out.decode("utf-8").split("\0") if f and f.lower().endswith(TEXT_EXT)]


def read(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def corpus_of(dist):
    """Name -> text. Pages are searched as visible text AND as raw source."""
    c = {}
    for dp, _, fs in os.walk(dist):
        for f in fs:
            if f.lower().endswith((".html", ".json", ".xml", ".txt", ".js")):
                p = os.path.join(dp, f)
                raw = read(p)
                rel = "dist/" + os.path.relpath(p, dist).replace(os.sep, "/")
                c[rel] = norm(re.sub(r"<[^>]+>", " ", raw)) if f.endswith(".html") else norm(raw)
    tr = tracked_files()
    if tr is not None:
        for f in tr:
            c[f] = norm(read(os.path.join(ROOT, f)))
    return c, tr is not None


def compile_all(h):
    pats = {}
    for kind, strings in h.items():
        if strings:
            # Whole tokens only: «2 sep 1949» is inside «12 sep 1949», which is somebody else.
            pats[kind] = re.compile(r"(?<![0-9a-z-])(?:" + "|".join(
                re.escape(s) for s in sorted(strings, key=len, reverse=True)) + r")(?![0-9a-z])")
    return pats


def scan(corp, pats):
    """[(file, kind)] — never the match itself."""
    hits = []
    for name, text in corp.items():
        for kind, rx in pats.items():
            if rx.search(text):
                hits.append((name, kind))
    return hits


def corpus_fails(corp, h):
    """A search that looked in nothing, or for nothing, has not passed."""
    out = []
    if sum(len(v) for v in h.values()) == 0:
        out.append(("scan", "nothing was harvested from the living, so nothing was searched for"))
    if len(corp) < 50:
        out.append(("scan", f"only {len(corp)} file(s) in the corpus — the build is unfinished or missing"))
    return out


def all_rows(data):
    for src in ("ancestors", "line", "relatives"):
        for r in data.get(src) or []:
            yield src, r
    for f in data["families"]:
        for m in f["members"]:
            yield "families", m


def flags_vs_data(people, flags, data):
    """The tree and the data must agree about who is living, for every record and
    every spouse entry."""
    fails = []
    for src, r in all_rows(data):
        if r["id"] not in people:
            fails.append(f"{src}: a record whose id is not in the tree")
            continue
        if bool(r.get("living")) != bool(flags.get(r["id"])):
            fails.append(f"{src}: a record's living flag disagrees with the tree "
                         f"(data says {bool(r.get('living'))}, tree says {bool(flags.get(r['id']))})")
        for s in r.get("spouses") or []:
            sid = s.get("id")
            if sid and sid in people and bool(s.get("living")) != bool(flags.get(sid)):
                fails.append("a spouse entry's living flag disagrees with the tree")
    return fails


def pages_vs_tree(data, expected_scope, expected_rel):
    """The people with a page are exactly the people the archive names."""
    fails = []
    have_scope = {r["id"] for r in data["ancestors"]} | {m["id"] for f in data["families"] for m in f["members"]}
    have_rel = {r["id"] for r in data["relatives"]}
    if have_scope - expected_scope:
        fails.append(f"{len(have_scope - expected_scope)} person(s) have a page by right and the tree does not put them in the direct line or a cluster")
    if expected_scope - have_scope:
        fails.append(f"{len(expected_scope - have_scope)} person(s) the archive gives a page by right have none")
    if have_rel - expected_rel:
        fails.append(f"{len(have_rel - expected_rel)} person(s) are published whom the archive does not name")
    if expected_rel - have_rel:
        fails.append(f"{len(expected_rel - have_rel)} person(s) the archive names have no page")
    return fails


def place_vs_tree(people, flags, data):
    """The place on a living record is exactly the town and country the tree reduces to."""
    import build_site_data as b
    from gedcom import born
    bad = 0
    for src, r in all_rows(data):
        if r.get("living") and r["id"] in people:
            want = b.town_country(born(people[r["id"]]).get("place", ""))
            if (r.get("place") or "") != want:
                bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=None)
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    dist = outdir.resolve(a.dist)
    if outdir.note(dist):
        print(outdir.note(dist))

    if not glob.glob(os.path.join(ROOT, "sources", "*.ged")):
        # Gitignored on purpose — it carries every living person in full — so CI
        # can never have it. A guard that cannot read its source has not passed;
        # but it must not fail a deploy it was never able to run either. So it
        # says which of those two happened, and never pretends to have checked.
        if os.environ.get("CI"):
            print("check_living: NOT RUN. The GEDCOM is gitignored, so CI cannot read it. "
                  "check_living_standard.py, which needs only the committed data and the "
                  "built pages, runs in the deploy instead.")
            return 0
        print("check_living: no GEDCOM under sources/. This guard reads the tree to learn "
              "who is alive, so a missing tree is a FAILURE, not a pass. "
              "(In CI the absence is expected and this exits 0 with a notice.)")
        return 1
    if not os.path.isdir(dist):
        print(f"check_living: no {dist} — build first")
        return 1

    from gedcom import load, classify_living, held_out
    people, families = load()
    tree = own_tree()
    flags = own_living(tree)                      # this gate's verdict, not the generator's
    n_living = sum(1 for v in flags.values() if v)

    data = std.load_data()
    fails = []

    # 0. the generator's verdict is this gate's, person by person, over the WHOLE tree
    gen_flags = classify_living(people, families)
    gen_held = held_out(people, gen_flags)
    diff = classify_diff(flags, gen_flags)
    if diff:
        fails.append(("classify", f"the generator and this gate disagree about who is living for {len(diff)} person(s)"))
    for k, n in sorted(arithmetic_fails(tree, gen_flags).items()):
        fails.append(("classify", f"{n} person(s) break the rule on the {k} test"))

    # 1. the part that needs no tree
    world = std.load_pages(dist)
    extra = [f for f in glob.glob(os.path.join(std.DATA, "*.json"))
             if os.path.basename(f) not in ("ancestors.json", "families.json", "line.json",
                                            "relatives.json", "living.json", "decisions.json")]
    sfails, info = std.run(data, world, extra)
    fails += [("standard/" + r, m) for r, m in sfails]

    # 2. the tree and the data agree about who is living, and the places
    for m in flags_vs_data(people, flags, data):
        fails.append(("flags", m))
    nbad = place_vs_tree(people, flags, data)
    if nbad:
        fails.append(("place", f"{nbad} living record(s) carry a place that is not the town and country the tree reduces to"))

    # 2b. the people with a page are exactly the people the archive names
    held = own_held(tree, flags, data["held"])
    e_scope, e_rel = own_pages(tree, held)
    for m in pages_vs_tree(data, e_scope, e_rel):
        fails.append(("pages", m))
    for k, n in sorted(held_arith_fails(tree, held).items()):
        fails.append(("held", f"{n} person(s) held out by rule break the held-out rule on the {k} test"))
    if held_diff(held, gen_held):
        fails.append(("held", f"the generator and this gate disagree about who is held out ({len(held_diff(held, gen_held))} person(s))"))

    # 3. nothing else the tree holds about a living person is anywhere
    h = harvest(people, families, flags)
    pats = compile_all(h)
    corp, have_git = corpus_of(dist)
    if not have_git:
        fails.append(("scan", "git could not list the tracked files, so the repository was not searched"))
    hits = scan(corp, pats)
    for f, kind in hits[:40]:
        fails.append(("leak", f"{f}: holds a {kind} string that belongs to a living person"))
    if len(hits) > 40:
        fails.append(("leak", f"...and {len(hits) - 40} more"))

    # 3b. the held-out are absent
    decl0 = json.load(open(DECL, encoding="utf-8"))
    named_phrases = {norm(n["phrase"]) for n in decl0.get("named", [])}
    namesakes = {norm(n["phrase"]) for n in decl0.get("namesakes", [])}
    hf, hinfo, hpats = held_fails(people, flags, data, corp, held, named_phrases, namesakes)
    fails += hf
    if not held:
        fails.append(("held", "no held-out person found in the tree, so nothing was proved absent"))
    if data["held"] and not any(v == "dna-tester" for v in held.values()):
        fails.append(("held", "the declared person promised privacy is not in the tree"))
    if not any(v == "possible-minor" for v in held.values()):
        fails.append(("held", "no possible minor found in the tree, so that rule was proved against nothing"))
    # the generator's own count of how many it met must be what the tree says
    ho = (decl0.get("published") or {}).get("heldOut") or {}
    if ho.get("possibleMinorsInTree") != sum(1 for v in held.values() if v == "possible-minor"):
        fails.append(("held", "the generator's count of possible minors in the tree is not the count this gate finds"))

    # 4. an empty search proves nothing
    fails += corpus_fails(corp, h)

    if a.controls:
        ok = controls(people, flags, data, world, h, corp, held, hpats, tree, e_scope, e_rel)
        if not ok:
            return 1

    decl = json.load(open(DECL, encoding="utf-8"))
    counts = {"tree": len(people), "living": n_living, "published": len(people) - n_living,
              "pages": sum(1 for r, _, fs in os.walk(dist) for f in fs if f.endswith(".html"))}
    decl["counts"] = counts
    decl["countsNote"] = ("Written by tools/check_living.py on every build — people, "
                          "not name phrases. Never type these numbers into a page.")
    json.dump(decl, open(DECL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for rule, msg in fails:
        print(f"  FAIL  {rule:16s} {msg}")
    if fails:
        print(f"  FAIL  living      {len(fails)} finding(s)")
        return 1
    if not a.quiet:
        print(f"  ok    classify    the generator and this gate agree about all {len(flags):,} people in the tree "
              f"({n_living:,} living); the rule restated as arithmetic holds for each")
        print(f"  ok    held-out    {hinfo['held']} person(s) held out ({sum(1 for v in held.values() if v == 'dna-tester')} by id, "
              f"{sum(1 for v in held.values() if v == 'possible-minor')} by rule): in no record, no data file, no built page; "
              f"{hinfo['searched']} names searched for in {len(corp):,} files, {hinfo['shared']} shared names covered by id only")
        print(f"  ok    pages       the {len(e_scope) + len(e_rel)} people with a page are exactly the people the archive names "
              f"({len(e_scope)} by right, {len(e_rel)} named beside them); the tree's other people are not published")
        print(f"  ok    living      {info['living']} living people have a page, each noindex and bare; searched {len(corp):,} files "
              f"(the built site and every tracked file) for {len(h['date']):,} dates, "
              f"{len(h['text']):,} notes/sources/occupations and {len(h['place']):,} long places "
              f"belonging to the tree's {n_living:,} living people and found none")
    return 0


# ---- planted faults -----------------------------------------------------------

def controls(people, flags, data, world, h, corp, held=None, hpats=None, tree=None,
             e_scope=None, e_rel=None):
    """Each rule is shown able to fail, in a COPY. Returns True when every one was caught."""
    pats = compile_all(h)
    ok = True

    def check(label, caught):
        nonlocal ok
        ok &= caught
        print(f"  {'caught ' if caught else 'MISSED '} {label}")

    print("  planted faults (this gate; the standard's own are run by check_living_standard.py --controls):")
    # a living person's full date, in a built page
    d = next(iter(sorted(h["date"])))
    c = dict(corp); c["dist/people/x/index.html"] = f"born {d} in a town"
    check("a living person's full date in a built page", bool(scan({"p": c["dist/people/x/index.html"]}, pats)))
    # the same date in a tracked data file
    c = {"site/src/data/x.json": '{"born": "' + d + '"}'}
    check("a living person's full date in a committed data file", bool(scan(c, pats)))
    # a note
    t = next(iter(sorted(h["text"])))
    check("a living person's note / source / occupation in a page", bool(scan({"p": "see: " + t + " ok"}, pats)))
    # a long place
    if h["place"]:
        pl = next(iter(sorted(h["place"])))
        check("a living person's full birthplace in a page", bool(scan({"p": "born " + pl}, pats)))
    # the ISO form
    iso = [x for x in sorted(h["date"]) if re.match(r"\d{4}-\d\d-\d\d$", x)]
    if iso:
        check("a living person's date in ISO form in a search index", bool(scan({"s": '{"q":"' + iso[0] + '"}'}, pats)))
    # a clean page is clean (the scan is not reading everything as a hit)
    check("a clean page is NOT a hit (the scan can say no)", not scan({"p": "a quiet page about a parish register"}, pats))
    # flags
    bad = copy.deepcopy(data)
    for a in bad["ancestors"]:
        if a.get("living"):
            a["living"] = False
            break
    check("a person the tree judges living, flagged dead in the data", bool(flags_vs_data(people, flags, bad)))
    bad = copy.deepcopy(data)
    for a in bad["ancestors"]:
        if not a.get("living"):
            a["living"] = True
            break
    check("a person the tree judges dead, flagged living in the data", bool(flags_vs_data(people, flags, bad)))
    # the rule at its edges, asked of the kit, with year 2026 fixed: 80 is living, 81 is not,
    # no year is not, a recorded death is not, a public source is not, a private tree is.
    T = 2026
    edge = [
        ("a person born 80 years ago, no death recorded, is living", lr.is_living(T - 80, False, [], T) is True),
        ("a person born 81 years ago is not living", lr.is_living(T - 81, False, [], T) is False),
        ("a person with no birth year is not living", lr.is_living(None, False, [], T) is False),
        ("a recorded death (dated or not) makes a young person dead", lr.is_living(T - 30, True, [], T) is False),
        ("a public source (FamilySearch) makes a young person not living", lr.is_living(T - 30, False, ["FamilySearch: x"], T) is False),
        ("a private tree entry does not", lr.is_living(T - 30, False, ["MyHeritage family tree: x"], T) is True),
        ("a child with a KNOWN birth year (aged 5) is NOT held out, even with a living parent", lr.possible_minor(T - 5, False, [], True, T) is False),
        ("nor a child aged 17 whose parent is living", lr.possible_minor(T - 17, False, [], True, T) is False),
        ("a person with no year and a living parent is a possible minor", lr.possible_minor(None, False, [], True, T) is True),
        ("a person with no year and no living parent is not", lr.possible_minor(None, False, [], False, T) is False),
        # THE 16 OCTOBER RULING ON THE INTEGRITY AUDIT: an undated parent of a recent child is living.
        ("undated, no death, no public source, youngest child born exactly 60 years ago: LIVING",
         lr.is_living(None, False, [], T, youngest_child_year=T - 60) is True),
        ("the same with the child born 61 years ago: not living",
         lr.is_living(None, False, [], T, youngest_child_year=T - 61) is False),
        ("undated, a recent child, and no child year supplied (the default): not living, as before",
         lr.is_living(None, False, [], T) is False),
        ("a recent child does not make a person with a recorded death living",
         lr.is_living(None, True, [], T, youngest_child_year=T - 10) is False),
        ("a recent child does not outweigh a public source",
         lr.is_living(None, False, ["FamilySearch: x"], T, youngest_child_year=T - 10) is False),
        ("a person WITH a birth year is judged on it alone, whatever the child says",
         lr.is_living(T - 90, False, [], T, youngest_child_year=T - 10) is False),
        ("an undated adult with a living parent AND a recent child is living and NOT held out",
         lr.possible_minor(None, False, [], True, T, youngest_child_year=T - 10) is False),
        ("an undated person with a living parent and no recent child is still held out",
         lr.possible_minor(None, False, [], True, T, youngest_child_year=T - 61) is True),
    ]
    for label, good in edge:
        check("[kit rule] " + label, good)
    # the generator's verdict, drifted by one person at a time, against the tree
    if tree:
        P = tree["people"]
        ty = lr.this_year()

        def pick(pred):
            return next((p for p, v in P.items() if pred(v)), None)
        cases = [
            ("a person 80 or younger, not recorded dead, no public source, flagged DEAD", "young-flagged-dead",
             pick(lambda v: v["by"] is not None and ty - v["by"] <= 80 and not v["dead"] and not lr.public_source(v["cites"])), False),
            ("a person the tree records as deceased, flagged LIVING", "recorded-dead",
             pick(lambda v: v["dead"] and v["by"] is not None and ty - v["by"] <= 80), True),
            ("a person with no birth year, flagged LIVING", "undated",
             pick(lambda v: v["by"] is None and not v["dead"]), True),
            ("a person over 80, flagged LIVING", "over-80",
             pick(lambda v: v["by"] is not None and ty - v["by"] > 80 and not v["dead"]), True),
        ]
        check("the honest classification passes the arithmetic", not arithmetic_fails(tree, flags))
        dated = pick(lambda v: v["by"] is not None and ty - v["by"] < 18 and not v["dead"] and not lr.public_source(v["cites"]))
        check("a child with a known birth year, held out", bool(dated) and "dated-child-held" in held_arith_fails(tree, {dated: "possible-minor"}))
        check("[planted person] a recorded-dead person, held out",
              "recorded-dead-held" in held_arith_fails({"people": {"@Y2@": {"by": None, "dead": True, "cites": [], "parents": []}}}, {"@Y2@": "possible-minor"}))
        check("[planted person] a person with a public source, held out",
              "public-source-held" in held_arith_fails({"people": {"@Y3@": {"by": None, "dead": False, "cites": ["FamilySearch: x"], "parents": []}}}, {"@Y3@": "possible-minor"}))
        check("the honest held-out set passes the held-out arithmetic", not held_arith_fails(tree, held or {}))
        for label, key, pid, val in cases:
            bad = dict(flags)
            if pid:
                bad[pid] = val
            check(label, bool(pid) and key in arithmetic_fails(tree, bad))
        # a public source, on a planted person (the tree holds nobody young with one)
        syn = {"people": {"@Y1@": {"by": ty - 30, "dead": False, "cites": ["FamilySearch: x"], "parents": []}}, "fams": {}}
        check("[planted person] aged 30, a public source, flagged LIVING",
              "public-source" in arithmetic_fails(syn, {"@Y1@": True}))
        check("[planted person] aged 30, a public source, honestly flagged not living, passes",
              not arithmetic_fails(syn, {"@Y1@": False}))
        # a classification that disagrees with this gate's, one person
        pid = next(iter(flags))
        gen_bad = dict(flags); gen_bad[pid] = not flags[pid]
        check("the generator calling one person living who this gate calls dead (or the reverse)",
              classify_diff(flags, gen_bad) == [pid] and not classify_diff(flags, flags))
        gen_held_bad = dict(held); gen_held_bad[pid if pid not in held else "@Z0@"] = "possible-minor"
        check("the generator holding out one person this gate does not",
              len(held_diff(held, gen_held_bad)) == 1 and not held_diff(held, held))
        # the people with a page
        if e_scope is not None:
            bad = copy.deepcopy(data)
            stranger = next(p for p in P if p not in e_scope and p not in e_rel and p not in held)
            bad["relatives"].append({"id": stranger, "name": "x", "living": False})
            check("a person the archive never names, published", bool(pages_vs_tree(bad, e_scope, e_rel)))
            bad = copy.deepcopy(data)
            bad["relatives"] = bad["relatives"][1:]
            check("a person the archive names, with no page", bool(pages_vs_tree(bad, e_scope, e_rel)))
            bad = copy.deepcopy(data)
            bad["ancestors"] = bad["ancestors"][:-1]
            check("a numbered ancestor with no page", bool(pages_vs_tree(bad, e_scope, e_rel)))
            check("the honest data passes the page rule", not pages_vs_tree(data, e_scope, e_rel))
        # facts: a person the tree dates in 1799 can never be living, a five-year-old is a possible minor
        fake = {"people": {"@X1@": {"by": 1799, "dead": False, "cites": [], "parents": []},
                           "@X2@": {"by": lr.this_year() - 5, "dead": False, "cites": [], "parents": []},
                           "@X3@": {"by": None, "dead": False, "cites": [], "parents": ["@X2@"]}},
                "fams": {}}
        fl = own_living(fake)
        check("[planted people] born 1799 is not living; a five-year-old is; undated is not",
              fl["@X1@"] is False and fl["@X2@"] is True and fl["@X3@"] is False)
        hh = own_held(fake, fl, ["@X9@"])
        check("[planted people] the undated child of a living parent is held out; the five-year-old (a known child) is not, and nor is the 1799 man",
              hh.get("@X3@") == "possible-minor" and "@X2@" not in hh and "@X1@" not in hh)
    # the held out
    if held:
        from gedcom import display
        dna = next((p for p, v in held.items() if v == "dna-tester"), None)
        mnr = next((p for p, v in held.items() if v == "possible-minor"
                    and len([x for x in people.values() if norm(display(x)) == norm(display(people[p]))]) == 1), None)
        for label, pid in (("the DNA tester", dna), ("a possible minor", mnr)):
            if not pid:
                continue
            nm = display(people[pid])
            # a record
            bad = copy.deepcopy(data)
            bad["ancestors"].append({"id": pid, "living": True, "name": nm, "surname": "x", "born": ""})
            hf, _, _ = held_fails(people, flags, bad, corp, held, set(), set())
            check(f"{label}, given a record in the data", bool(hf))
            # a name, as a relative on a page
            hf, _, _ = held_fails(people, flags, data, {"dist/people/x/index.html": norm("Brothers and sisters " + nm)}, held, set(), set())
            check(f"{label}, named as a relative on a built page", bool(hf))
            hf, _, _ = held_fails(people, flags, data, {"site/src/data/x.json": norm('{"siblings": ["' + nm + '"]}')}, held, set(), set())
            check(f"{label}, named in a committed data file", bool(hf))
        hf, _, _ = held_fails(people, flags, data, {"p": "a quiet page about a parish register"}, held, set(), set())
        check("a clean corpus is NOT a held-out hit (the search can say no)", not [f for f in hf if "name of" in f[1]])
    # the empty corpus
    check("an empty build (no files) is refused", bool(corpus_fails({}, h)))
    check("a tree that yields nothing to search for is refused", bool(corpus_fails(corp, {"date": set(), "text": set(), "place": set()})))
    # the standard's own, through the same module
    ok2, lines = std.controls(data, world)
    print("\n".join(lines))
    ok &= ok2
    if not ok:
        print("  FAIL  living      a planted fault was NOT caught — the gate cannot fail on that rule")
    return ok


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""A living person is a name, a relationship, a town and a country. The tree says what is NOT allowed.

THE RULE (David, 16 October 2026, made knowing the tree holds 2,034 people it
judges living): this archive adopts the standard the Defranceschi archive keeps.
A living person is named, with their town and country, and nothing more: no date,
no record, no source, no note, no occupation, no photograph, no structured data.

THIS FILE USED TO ENFORCE THE OPPOSITE. Until that day the rule was «no living
person is published as a person, and no living NAME appears anywhere», and this
was the gate: it read the tree, built 1,768 name phrases, and refused to ship if
any appeared on a page. A name is now allowed, so that test is gone — and what
replaces it must not be weaker than what it replaced, so it is turned the other
way. It still reads the tree, which is the only place that knows who is living,
and what it reads out is no longer their NAMES but everything ELSE about them:

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

It also proves three rulings David made on the same day about WHO is published:

  · a person the tree RECORDS as deceased (a death or burial event, with or
    without a date) is dead, so none of them is flagged living, and nobody born
    within a hundred years who is not recorded dead is flagged dead (this is
    computed here from the events, independently of gedcom.classify_living);
  · the DNA tester is held out: not a record, not an id, not a name anywhere;
  · every living person with no birth year in the tree who has a living parent is
    held out: the same. These are computed here from the tree, by their own rule,
    not read from the generator's, and what is reported is a count.

It also checks that the data and the tree agree about WHO IS LIVING, which is the
fault that matters most under a rule that publishes living people by name: a
person the tree judges living and the data does not flag would be emitted with
their full record, and nothing in the page layer would know.

And it runs the part that needs only the committed data and the built pages
(tools/check_living_standard.py: noindex, no structured data, nothing in the
sitemap or the search index, only the headings a living page has). That part
also runs in the deploy, where there is no tree. This part cannot, and says so.

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


def has_year(person):
    from gedcom import born
    return re.search(r"\b\d{4}\b", born(person).get("date", "") or "") is not None


def recorded_dead(person):
    return any(e["kind"] in ("death", "burial") for e in person["events"])


def dead_vs_tree(people, flags, today=2026):
    """THE RECORD'S OWN WORD. Computed here and not by gedcom.classify_living, so
    that a classifier that stops reading the record is caught by something that
    does not share its code."""
    fails = []
    wrong_living = [p for p, v in people.items() if recorded_dead(v) and flags.get(p)]
    if wrong_living:
        fails.append(f"{len(wrong_living)} person(s) the tree records as deceased are flagged living")
    # nobody born within a hundred years, and not recorded dead, may be dead
    from gedcom import born, year
    wrong_dead = [p for p, v in people.items()
                  if not recorded_dead(v) and not flags.get(p)
                  and (year(born(v).get("date", "")) or 0) > today - 100]
    if wrong_dead:
        fails.append(f"{len(wrong_dead)} person(s) born within a hundred years and not recorded dead are flagged dead")
    return fails


def held_set(people, flags, tester):
    """Who must be absent: the declared DNA tester, and every living person with
    no birth year who has a living parent. This gate's own implementation."""
    out = {}
    for pid, v in people.items():
        if flags.get(pid) and not has_year(v) and any(flags.get(x) for x in v["parents"]):
            out[pid] = "possible-minor"
    for t in tester:
        if t in people and flags.get(t):
            out[t] = "dna-tester"
    return out


def held_fails(people, flags, data, corp, held, named_phrases, namesakes):
    """None of the held-out is a record, an id, or a name. A name can only be
    searched for if it is unique: a name two people share proves nothing about
    which of them a page means, so those are counted and not searched, and the
    id check (in the standard) covers them."""
    from gedcom import display
    fails, searched, shared, skipped = [], 0, 0, 0
    ids = set(held)
    for src in ("ancestors", "line"):
        for r in data[src]:
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
        for name, text in corp.items():
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


def flags_vs_data(people, flags, data):
    """The tree and the data must agree about who is living."""
    fails = []
    seen = {}
    for src in ("ancestors", "families", "line"):
        rows = data[src] if src != "families" else [m for f in data[src] for m in f["members"]]
        for r in rows:
            seen[r["id"]] = r
            if r["id"] not in people:
                fails.append(f"{src}: a record whose id is not in the tree")
                continue
            if bool(r.get("living")) != bool(flags.get(r["id"])):
                fails.append(f"{src}: a record's living flag disagrees with the tree "
                             f"(data says {bool(r.get('living'))}, tree says {bool(flags.get(r['id']))})")
    for r in seen.values():
        for s in r.get("spouses") or []:
            sid = s.get("id")
            if sid and sid in people and bool(s.get("living")) != bool(flags.get(sid)):
                fails.append("a spouse entry's living flag disagrees with the tree")
    return fails


def place_vs_tree(people, flags, data):
    """The place on a living record is exactly the town and country the tree reduces to."""
    import build_site_data as b
    from gedcom import born
    bad = 0
    for src in ("ancestors", "families"):
        rows = data[src] if src != "families" else [m for f in data[src] for m in f["members"]]
        for r in rows:
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

    from gedcom import load, classify_living
    people, families = load()
    flags = classify_living(people, families)
    n_living = sum(1 for v in flags.values() if v)

    data = std.load_data()
    fails = []

    # 1. the part that needs no tree
    world = std.load_pages(dist)
    extra = [f for f in glob.glob(os.path.join(std.DATA, "*.json"))
             if os.path.basename(f) not in ("ancestors.json", "families.json", "line.json",
                                            "living.json", "decisions.json")]
    sfails, info = std.run(data, world, extra)
    fails += [("standard/" + r, m) for r, m in sfails]

    # 2. the tree and the data agree about who is living
    for m in flags_vs_data(people, flags, data):
        fails.append(("flags", m))
    nbad = place_vs_tree(people, flags, data)
    if nbad:
        fails.append(("place", f"{nbad} living record(s) carry a place that is not the town and country the tree reduces to"))

    # 2b. a recorded death is a death
    for m in dead_vs_tree(people, flags):
        fails.append(("recorded-dead", m))

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
    held = held_set(people, flags, data["held"])
    hf, hinfo, hpats = held_fails(people, flags, data, corp, held, named_phrases, namesakes)
    fails += hf
    if not held:
        fails.append(("held", "no held-out person found in the tree, so nothing was proved absent"))
    if data["held"] and not any(v == "dna-tester" for v in held.values()):
        fails.append(("held", "the declared DNA tester is not in the tree as a living person"))
    # the generator's own count of how many it met must be what the tree says
    ho = (decl0.get("published") or {}).get("heldOut") or {}
    if ho.get("possibleMinorsInTree") != sum(1 for v in held.values() if v == "possible-minor"):
        fails.append(("held", "the generator's count of possible minors in the tree is not the count this gate finds"))

    # 4. an empty search proves nothing
    fails += corpus_fails(corp, h)

    if a.controls:
        ok = controls(people, flags, data, world, h, corp, held, hpats)
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
        print(f"  ok    held-out    {hinfo['held']} person(s) held out ({sum(1 for v in held.values() if v == 'dna-tester')} by id, "
              f"{sum(1 for v in held.values() if v == 'possible-minor')} by rule): in no record, no data file, no built page; "
              f"{hinfo['searched']} names searched for in {len(corp):,} files, {hinfo['shared']} shared names covered by id only")
        print(f"  ok    recorded    every person the tree records as deceased is flagged dead; nobody born within a hundred years and not recorded dead is")
        print(f"  ok    living      {n_living:,} people the tree judges living; "
              f"{info['living']} have a page, each noindex and bare; searched {len(corp):,} files "
              f"(the built site and every tracked file) for {len(h['date']):,} dates, "
              f"{len(h['text']):,} notes/sources/occupations and {len(h['place']):,} long places "
              f"belonging to them and found none")
    return 0


# ---- planted faults -----------------------------------------------------------

def controls(people, flags, data, world, h, corp, held=None, hpats=None):
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
    # the record's own word
    rd = next((p for p, v in people.items() if recorded_dead(v) and not flags.get(p)), None)
    bad = dict(flags)
    if rd:
        bad[rd] = True
    check("a person the tree records as deceased, wrongly marked living", bool(rd) and bool(dead_vs_tree(people, bad)))
    from gedcom import born, year
    lv = next((p for p, v in people.items() if flags.get(p) and not recorded_dead(v)
               and (year(born(v).get("date", "")) or 0) > 1926), None)
    bad = dict(flags)
    if lv:
        bad[lv] = False
    check("a living person (born within a hundred years, not recorded dead), wrongly marked dead", bool(lv) and bool(dead_vs_tree(people, bad)))
    check("the honest classification passes the record's-word rule", not dead_vs_tree(people, flags))
    in_data = {r["id"] for r in data["ancestors"] + [m for f in data["families"] for m in f["members"]]}
    nodate = next((p for p, v in people.items() if p in in_data and recorded_dead(v) and not flags.get(p)
                   and not any(e.get("date") for e in v["events"] if e["kind"] in ("death", "burial"))), None)
    bad2 = copy.deepcopy(data)
    for rows in (bad2["ancestors"], [m for f in bad2["families"] for m in f["members"]]):
        for r in rows:
            if r["id"] == nodate:
                r["living"] = True
    check("a recorded-dead person with no death date, flagged living in the data",
          bool(nodate) and bool(flags_vs_data(people, flags, bad2)))
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

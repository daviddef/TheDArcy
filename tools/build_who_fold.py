#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The /who/ dossier lines that are also set out on a person's page (23 November 2026).

    python3 tools/build_who_fold.py            # writes site/src/data/who-fold.json
    python3 tools/build_who_fold.py --check    # refuses a stale file (npm run check:who-fold-data, before astro)

/who/<slug>/ is a dossier of the register lines that name a person who is in no family tree page. Eleven of those names are
also the name of a person page (tools/namesakes-who-known.json), a page that said "No record has been found for them" while
the lines sat on /who/ only. David ruled "fold in, keep /who/": the lines that are demonstrably about the person are readable on
the person's page too, and /who/ is not touched (it is built from site/src/data/dossiers.json, which this tool only reads).

THE RULING is by hand and line by line, tools/who-fold-rulings.json, each entry with the evidence for it. THIS TOOL copies the chosen
lines VERBATIM from dossiers.json (says, source, link: nothing is reworded, shortened or joined) into site/src/data/who-fold.json:

    pages     person slug -> {who, name, kind, total, rows[]}      the lines set out on that person's page
    pointers  person slug -> {who, name, total, why[, elsewhere]}  a page that links to the dossier and sets nothing out

It refuses: a dossier that is not in dossiers.json, a line number out of range, a line given to two pages, a page named twice, a
person slug that is no built person page (read from the site's own address rule, tools/slugrule.py), a living person's page, a name
that is not the dossier's name once accents and case are folded, and an entry of a kind or reason it does not know.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, "site", "src", "data")
RULINGS = os.path.join(HERE, "who-fold-rulings.json")
DOSSIERS = os.path.join(D, "dossiers.json")
OUT = os.path.join(D, "who-fold.json")
KINDS = {"agrees", "only", "ruled"}
WHYS = {"other", "unsplit", "elsewhere"}

sys.path.insert(0, HERE)


def fold(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def people():
    """{slug: record} for every person with a page, by the archive's own address rule."""
    import slugrule
    base, rel = slugrule.records()
    ids = slugrule.assign(base, rel)
    out = {}
    for r in base + rel:
        out[ids[r["id"]]] = r
    return out


def build():
    rules = json.load(open(RULINGS, encoding="utf-8"))
    dos = json.load(open(DOSSIERS, encoding="utf-8"))["people"]
    ppl = people()
    errs, pages, pointers, used_rows = [], {}, {}, {}

    def person(slug, ctx):
        r = ppl.get(slug)
        if r is None:
            errs.append("%s: %s is not a person page" % (ctx, slug))
            return None
        if r.get("living"):
            errs.append("%s: a living person's page is never named here" % ctx)
            return None
        return r

    for e in rules["fold"]:
        who, to = e["who"], e["to"]
        ctx = "fold %s -> %s" % (who, to)
        w = dos.get(who)
        if not w:
            errs.append("%s: no such dossier" % ctx)
            continue
        if e.get("kind") not in KINDS:
            errs.append("%s: kind %r is not one of %s" % (ctx, e.get("kind"), sorted(KINDS)))
        if not str(e.get("evidence", "")).strip():
            errs.append("%s: no evidence written" % ctx)
        p = person(to, ctx)
        if p is None:
            continue
        if fold(p["name"]) != fold(w["name"]):
            errs.append("%s: the page's name %r is not the dossier's name %r" % (ctx, p["name"], w["name"]))
        if to in pages or to in pointers:
            errs.append("%s: %s is named twice" % (ctx, to))
        rows = []
        for i in e["rows"]:
            if not isinstance(i, int) or not 0 <= i < len(w["rows"]):
                errs.append("%s: line %r is out of range (the dossier has %d)" % (ctx, i, len(w["rows"])))
                continue
            if (who, i) in used_rows:
                errs.append("%s: line %d is already given to %s" % (ctx, i, used_rows[(who, i)]))
            used_rows[(who, i)] = to
            r = w["rows"][i]
            rows.append({"says": r["says"], "source": r["source"], "link": r["link"]})
        if not rows:
            errs.append("%s: no line chosen" % ctx)
        pages[to] = {"who": who, "name": w["name"], "kind": e["kind"], "total": len(w["rows"]), "rows": rows}

    for e in rules["pointer"]:
        who = e["who"]
        w = dos.get(who)
        if not w:
            errs.append("pointer %s: no such dossier" % who)
            continue
        if e.get("why") not in WHYS:
            errs.append("pointer %s: why %r is not one of %s" % (who, e.get("why"), sorted(WHYS)))
        if not str(e.get("evidence", "")).strip():
            errs.append("pointer %s: no evidence written" % who)
        for to in e["to"]:
            ctx = "pointer %s -> %s" % (who, to)
            p = person(to, ctx)
            if p is None:
                continue
            if fold(p["name"]) != fold(w["name"]):
                errs.append("%s: the page's name %r is not the dossier's name %r" % (ctx, p["name"], w["name"]))
            if to in pages or to in pointers:
                errs.append("%s: %s is named twice" % (ctx, to))
            q = {"who": who, "name": w["name"], "total": len(w["rows"]), "why": e["why"]}
            if e["why"] == "elsewhere":
                el = e.get("elsewhere")
                if not el or el not in pages:
                    errs.append("%s: 'elsewhere' must name a page that sets the lines out" % ctx)
                else:
                    q["elsewhere"] = el
            pointers[to] = q

    # every dossier whose name a person page carries is either folded or pointed at, on every such page
    byname = {}
    for s, r in ppl.items():
        if not r.get("living"):
            byname.setdefault(fold(r["name"]), []).append(s)
    for who, w in dos.items():
        for s in byname.get(fold(w["name"]), []):
            if s not in pages and s not in pointers:
                errs.append("dossier %s shares its name with /people/%s/, which is neither folded into nor pointed at" % (who, s))
    return errs, {"pages": dict(sorted(pages.items())), "pointers": dict(sorted(pointers.items()))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    errs, data = build()
    if errs:
        for e in errs:
            print("  FAIL  " + e)
        print("build_who_fold: %d finding(s)" % len(errs))
        return 1
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    n = sum(len(v["rows"]) for v in data["pages"].values())
    summary = "%d line(s) set out on %d person page(s), %d page(s) point to a dossier" % (n, len(data["pages"]), len(data["pointers"]))
    if a.check:
        try:
            have = open(OUT, encoding="utf-8").read()
        except OSError:
            have = None
        if have != text:
            print("  FAIL  site/src/data/who-fold.json is %s: run python3 tools/build_who_fold.py and commit it" % ("missing" if have is None else "not what tools/who-fold-rulings.json and dossiers.json make"))
            return 1
        print("  ok    who-fold-data  " + summary)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("who-fold: " + summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())

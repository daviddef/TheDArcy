#!/usr/bin/env python3
"""Who is alive in this archive — the kit decides whether any of them got out.

This archive's rule is the strictest in the estate: LIVING PEOPLE ARE NOT
PUBLISHED AT ALL — not hidden, not gated, absent from the output.
build_site_data.py applies it once, at the boundary between the research data
and the site, so that nobody can be living on one page and dead on another.
This is the check that the rule held, and it reads the BUILT HTML, because
source can be correct and output wrong: a living person's name reaches a page
through a deceased relative's spouses, parents and children long after they
were filtered out of the person list.

WHY THE NAMES ARE NOT COMMITTED. This tree holds over two thousand living
people. A file listing them, in a PUBLIC repository, would be precisely the
disclosure the rule exists to prevent — a machine-readable directory of living
relatives, committed forever to a git history. And a hand-kept list goes
stale. The GEDCOM is the authority, it is regenerated whenever the tree is
exported, and it is gitignored. So the names are read at check time and never
written down. What IS committed is site/src/data/living.json: the policy, the
exceptions and the counts. Exceptions need human judgement and version
control. Names need neither.

WHAT THIS FILE IS NOW. The matching — name phrases, exact-namesake
subtraction, longer-published-name subtraction, the combined single-pass
regex — was written here and now lives in the kit, where the other six
archives get it too. This file is what only this archive can do: open its own
tree and say who is alive. That split is the whole of the convergence.

    python3 tools/check_living.py            # gate the build
    python3 tools/check_living.py --verbose  # show what matched and why
"""
import os, sys, json, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "site", "node_modules", "@daviddef",
                                "archive-kit", "kit", "tools"))
from gedcom import load, display, classify_living          # noqa: E402
import checkliving                                          # noqa: E402

DIST = os.path.join(ROOT, "site", "dist")
DECL = os.path.join(ROOT, "site", "src", "data", "living.json")


def _n_pages(dist):
    return sum(1 for r, _, fs in os.walk(dist) for f in fs if f.endswith(".html"))


def json_pass(dist, living, publish, quiet=False):
    """The .json this site SERVES, which the kit's feed() has never opened.

    feed() walks .html. This archive also ships three JSON files to the
    browser — searchindex.json at 2.1MB, atlas-data.json, whoindex.json — and
    an atlas serves its places that way and a search box its index. They are
    regenerated from the same tree on every build, so "they happen to be clean"
    is a fact about today and not a guarantee about tomorrow.

    THE TEST IS NARROWER THAN feed()'S, AND DELIBERATELY. A substring sweep over
    these files reports twenty-five hits and every one is noise: "George" inside
    George Pitt D'Arcy, "William Murdoch" inside Keith William Murdoch
    1925-1996, "Geraldine" inside Geraldine D'Arcy 1872-1937. What matters in a
    structured index is not whether a living person's name occurs somewhere in
    two megabytes of text — it is whether the file NAMES A LIVING PERSON AS A
    PERSON. So this reads the fields that carry a person's name and compares
    them whole:

        searchindex.json   {"k": "Person", "t": <name>}
        whoindex.json      [<name>, <slug>, <count>]
        atlas-data.json    "people": [{"n": <name>}]

    A whole-field match against a living phrase is not noise. It is a person
    entry, with a link, for somebody who is alive.
    """
    import re as _re
    fields = []
    for f in sorted(glob.glob(os.path.join(dist, "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  WARN  {os.path.basename(f)} will not parse — {e}")
            continue
        name = os.path.basename(f)

        def walk(o):
            if isinstance(o, dict):
                if o.get("k") == "Person" and o.get("t"):
                    fields.append((name, o["t"]))
                if "n" in o and isinstance(o["n"], str):
                    fields.append((name, o["n"]))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                if o and isinstance(o[0], str) and len(o) == 3:
                    fields.append((name, o[0]))
                for v in o:
                    walk(v)
        walk(d)

    # EXACT-NAMESAKE SUBTRACTION, the same allowance feed() makes on the HTML.
    # Without it this fires on every dead person who shares a name with a living
    # relative, and in a family that reuses forenames the way this one does it
    # would be switched off inside a week. The archive publishes a William
    # Murdoch born 1856 at St Quivox and a James Atwell of 1853-1907; living
    # people carry both names too. A phrase that also belongs to somebody
    # publishable is not evidence that anybody living got out.
    norm = checkliving.norm
    lv = {norm(x) for x in living if x} - {norm(x) for x in publish if x}
    bad = [(f, t) for f, t in fields if norm(t) in lv]
    if not quiet:
        print(f"  {'ok  ' if not bad else 'FAIL'}  living/json  "
              f"{len(fields):,} person name(s) across {len(glob.glob(os.path.join(dist, '*.json')))} "
              f"served json file(s) — {len(bad)} name a living person")
    for f, t in bad[:20]:
        print(f"   LEAK {f}: person entry named {t!r}")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=DIST)
    ap.add_argument("--declared", default=DECL)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not glob.glob(os.path.join(ROOT, "sources", "*.ged")):
        # Gitignored on purpose — it carries every living person in full — so CI
        # can never have it. A guard that cannot read its source has not passed;
        # but it must not fail a deploy it was never able to run either. So it
        # says which of those two happened, and never pretends to have checked.
        if os.environ.get("CI"):
            print("check_living: NOT RUN. The GEDCOM is gitignored, so CI cannot read "
                  "it. This gates locally, where the tree exists; in CI the kit's "
                  "check:living runs against the committed data.")
            return 0
        print("check_living: no GEDCOM under sources/. This guard reads the tree to "
              "learn who is alive, so a missing tree is a FAILURE, not a pass. "
              "(In CI the absence is expected and this exits 0 with a notice.)")
        return 1

    if not os.path.exists(a.declared):
        print(f"check_living: no declaration at {a.declared}. The exceptions are the "
              f"part a human has to judge, so a missing declaration is a FAILURE.")
        return 1
    decl = json.load(open(a.declared, encoding="utf-8"))
    # Two kinds of exception, kept apart on purpose. A NAMESAKE is not a living
    # person at all — a historical Richard Smith, a middle name inside a longer
    # one. A NAMED entry IS a living person this archive has decided to name.
    allow = set(decl.get("allow", []))
    allow |= {e["phrase"] for e in decl.get("namesakes", []) if e.get("phrase")}
    allow |= {e["phrase"] for e in decl.get("named", []) if e.get("phrase")}

    people, families = load()
    living_ids = classify_living(people, families)
    living = {checkliving.norm(display(people[p]) or "") for p in people if living_ids.get(p)}
    publish = {checkliving.norm(display(people[p]) or "") for p in people if not living_ids.get(p)}
    living.discard(""); publish.discard("")

    # PEOPLE, not names. The sets above are distinct name phrases — two living
    # cousins called John Smith are one phrase and two people — so counting the
    # sets would quietly understate the rule's reach. /about, /index, /method,
    # /register and /the-other-archives all quote these, and they were hardcoded
    # on all five until they drifted once already.
    n_living = sum(1 for p in people if living_ids.get(p))
    counts = {"tree": len(people), "living": n_living,
              "published": len(people) - n_living,
              "phrases": len(living), "pages": _n_pages(a.dist)}
    decl["counts"] = counts
    decl["countsNote"] = ("Written by tools/check_living.py on every build — people, "
                          "not name phrases. Never type these numbers into a page.")
    json.dump(decl, open(a.declared, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    rc_json = json_pass(a.dist, living, publish, quiet=a.quiet)

    return (checkliving.feed(
        a.dist, living, publish,
        allow=allow, allow_files=decl.get("allowFiles", []), quiet=a.quiet,
        label=f"{len(people):,} in the tree, {counts['published']:,} publishable; "
              f"{n_living:,} living people under {len(living):,} distinct names") or rc_json)


if __name__ == "__main__":
    sys.exit(main())

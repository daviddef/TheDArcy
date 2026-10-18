#!/usr/bin/env python3
"""Does the run-time linker ever send a reader to the WRONG namesake?

18 October 2026. site/public/wholink.js reads /whoindex.json and turns a person's
name in any page's prose into a link. The index was built as {name: slug}, so a
name that two or more people bear collapsed to ONE arbitrary slug, and every
mention of it went there: "George Pitt D'Arcy" (1780 to 1849 and 1864 to 1931)
always went to the 1864 man, "Ralph Sneyd" (nine people) to one of nine. Measured
on twelve narrative pages, 62 of the 153 links the linker made pointed at one of
several people of that name. A link that is confidently wrong is worse than no
link, and nothing noticed, because the file is well formed and every slug in it
is a real page.

tools/build_mentions.py now writes a row per name: kind "p" (a /people/ page) or
"w" (a /who/ page) only when EXACTLY ONE page bears the name, and kind "a" with
no slug for a name two or more pages bear, which wholink.js sends to the
search at /people/?q=<name>. This reads the served index against the built pages
and refuses the old fault:

  - a "p" or "w" row whose name (case, spacing and apostrophes folded) is borne
    by two or more pages, living and noindex pages counted, a declared copy
    (canonical naming another /people/ page) not counted: it is the same person
  - a "p" or "w" row whose slug is not a built page of that kind, or is noindex
    (a living person is never linked), or whose page does not bear that name
  - an "a" row that carries a slug, or whose name fewer than two pages bear, or
    whose name only noindex pages bear
  - the same name in two rows, a row of the old three-field shape (it cannot say
    whether the name is unique), a row for a name no page bears

IT TESTS ITSELF FIRST, every run, on a small dist built in a temporary directory:
a planted collision (two pages, one name, one slug), a planted case-only
collision, a planted living namesake, and a planted noindex target must each be
refused, and a clean index must pass. A gate that has not been shown to fail
proves nothing by passing.

It reads the BUILT site and no tree data, so it runs wherever the build does.
"""
import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outdir
outdir.strict_argv()
import build_mentions as bm

KINDS = {"p": "people", "w": "who"}


def check(dist, rows):
    """Findings (strings) for index `rows` against the pages built under `dist`."""
    pages = bm.built_pages(dist)
    groups = bm.name_groups(pages)
    fails, seen = [], {}
    for r in rows:
        if not (isinstance(r, list) and len(r) == 5):
            fails.append(f"row {r!r} is not [name, slug, count, kind, n]: the old three-field shape cannot "
                         f"say whether a name is borne by one person")
            continue
        name, slug, count, kind, n = r
        key = bm.fold(name)
        if key in seen:
            fails.append(f"{name!r} is in the index twice (also {seen[key]!r})")
        seen[key] = name
        members = groups.get(key)
        if not members:
            fails.append(f"{name!r}: no built page bears this name")
            continue
        pub = [m for m in members if not m[3]]
        if kind == "a":
            if slug:
                fails.append(f"{name!r}: an ambiguous row must carry no slug, and carries {slug!r}")
            if len(members) < 2:
                fails.append(f"{name!r}: an ambiguous row for a name only one page bears")
            if not pub:
                fails.append(f"{name!r}: every page bearing this name is noindex (a living person); it must not be in the index")
            if n != len(members):
                fails.append(f"{name!r}: the row says {n} people, the built pages say {len(members)}")
        elif kind in KINDS:
            if len(members) != 1:
                who = ", ".join(f"/{m[0]}/{m[1]}/" for m in members[:4])
                fails.append(f"{name!r} maps to {slug!r} and {len(members)} pages bear this name ({who}"
                             f"{', ...' if len(members) > 4 else ''}): a reader would be sent to a guess")
            elif (members[0][0], members[0][1]) != (KINDS[kind], slug):
                fails.append(f"{name!r} maps to /{KINDS[kind]}/{slug}/ and the page that bears it is "
                             f"/{members[0][0]}/{members[0][1]}/")
            elif members[0][3]:
                fails.append(f"{name!r} maps to /{KINDS[kind]}/{slug}/, which is noindex (a living person is never linked)")
        else:
            fails.append(f"{name!r}: unknown kind {kind!r}")
    return fails


# ---- the self-test: a small dist in a temporary directory -------------------

def _page(root, kind, slug, name, noindex=False, canonical=None):
    d = os.path.join(root, kind, slug)
    os.makedirs(d, exist_ok=True)
    head = ""
    if noindex:
        head += '<meta name="robots" content="noindex">'
    if canonical:
        head += f'<link rel="canonical" href="https://example.test/people/{canonical}/">'
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"<html><head>{head}</head><body><main><h1>{name}</h1><p>text</p></main></body></html>")


def selftest():
    """Returns (faults in this gate itself, planted cases tried); no faults when it can fail and can pass."""
    bad = []
    with tempfile.TemporaryDirectory() as root:
        _page(root, "people", "john-smith-1800", "John Smith")
        _page(root, "people", "john-smith-1850", "John Smith")
        _page(root, "people", "hannah-saniger", "Hannah SANIGER")
        _page(root, "people", "hannah-saniger-2", "Hannah Saniger")
        _page(root, "people", "ann-brown", "Ann Brown")
        _page(root, "people", "ann-brown-living", "Ann Brown", noindex=True)
        _page(root, "people", "eve-jones", "Eve Jones")
        _page(root, "people", "eve-jones-copy", "Eve Jones", canonical="eve-jones")
        _page(root, "people", "sam-living", "Sam Living", noindex=True)
        _page(root, "people", "mary-who", "Mary Who")
        _page(root, "who", "mary-who", "Mary Who")
        _page(root, "who", "tom-witness", "Tom Witness")
        planted = {
            "a name two pages bear, mapped to one slug": [["John Smith", "john-smith-1850", 3, "p", 1]],
            "a case-only namesake, mapped to one slug": [["Hannah SANIGER", "hannah-saniger", 3, "p", 1]],
            "a living namesake, the dead one mapped alone": [["Ann Brown", "ann-brown", 2, "p", 1]],
            "a /who/ name that a /people/ page also bears": [["Mary Who", "mary-who", 1, "w", 1]],
            "a row pointing at a noindex page": [["Sam Living", "sam-living", 1, "p", 1]],
            "an ambiguous row that carries a slug": [["John Smith", "john-smith-1850", 3, "a", 2]],
            "an ambiguous row for a name only noindex pages bear": [["Sam Living", "", 1, "a", 2]],
            "the old three-field shape": [["Eve Jones", "eve-jones", 1]],
            "the same name in two rows": [["John Smith", "", 3, "a", 2], ["john smith", "", 3, "a", 2]],
            "a name no page bears": [["Nobody Here", "nobody-here", 1, "p", 1]],
        }
        for what, rows in planted.items():
            if not check(root, rows):
                bad.append(f"self-test: the gate did not refuse {what}")
        clean = [["John Smith", "", 3, "a", 2], ["Hannah SANIGER", "", 2, "a", 2],
                 ["Ann Brown", "", 2, "a", 2], ["Mary Who", "", 1, "a", 2],
                 ["Eve Jones", "eve-jones", 1, "p", 1], ["Tom Witness", "tom-witness", 1, "w", 1]]
        got = check(root, clean)
        if got:
            bad.append(f"self-test: a clean index was refused: {got[0]}")
    return bad, len(planted)


def main():
    bad, tried = selftest()
    if bad:
        print(f"  FAIL  whoindex   the gate cannot be trusted: {len(bad)} self-test fault(s)")
        for m in bad[:6]:
            print(f"          {m}")
        return 1
    dist = outdir.out()
    f = os.path.join(dist, "whoindex.json")
    if not os.path.isfile(f):
        print(f"  FAIL  whoindex   no whoindex.json under {dist} — nothing was examined")
        return 1
    rows = json.load(open(f, encoding="utf-8"))
    if not rows:
        print("  FAIL  whoindex   whoindex.json is empty — a gate with nothing to check cannot fail")
        return 1
    if not os.path.isdir(os.path.join(dist, "people")):
        print(f"  FAIL  whoindex   no built person pages under {dist} — nothing was examined")
        return 1
    fails = check(dist, rows)
    if fails:
        print(f"  FAIL  whoindex   {len(fails)} finding(s) in {len(rows)} index row(s)")
        for m in fails[:8]:
            print(f"          {m}")
        return 1
    k = {x: sum(1 for r in rows if r[3] == x) for x in "pwa"}
    print(f"  ok    whoindex   {len(rows)} rows ({k['p']} people and {k['w']} witnesses each borne by exactly one page, "
          f"{k['a']} shared names sent to the search); self-test refused all {tried} planted faults and passed a clean index")
    return 0


if __name__ == "__main__":
    sys.exit(main())

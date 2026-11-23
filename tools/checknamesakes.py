#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One page per person: does every person's page list exactly the other people of their name?

    python3 ../tools/checknamesakes.py --dist "${ARCHIVE_OUT:-dist}"        # from site/; `npm run check:namesakes`
    python3 ../tools/checknamesakes.py --selftest                           # plants one fault per rule

WHAT THIS ARCHIVE'S /who/ IS (23 November 2026). Not a name page. /who/<slug>/ is a DOSSIER of the register lines that name a person
who is in no family tree page: a witness, a constable, a clerk (215 of them). It holds the record sentences and their sources, which
exist on no other page, so it is not redirected; the rule "a person's page lists the other people who carry the same name" is
carried by the person page's section "Others of the same name" (id `namesakes`, the kit's PersonPage anchor), which this gate holds
to the built pages and to nothing the page generator used:

  sets      derived HERE from the h1 of every built person page (/people/<slug>/), accents and case folded and every run of
            anything that is not a letter or a digit read as one space (the fold of site/src/lib/people.js nameKey). The
            others of a page are the rest of its set, never a living person, and a living person's page lists nobody.
  missing   a page's list lacks a person of its name.
  extra     it lists a page that does not carry the name, a living person, or itself.
  absent    a name is shared and the page has no list, or the page has a list and nobody shares its name.
  living    a living person's page (noindex) carries a list.
  filed     a /who/ dossier whose name is also a person page's name. The register rows filed under it are on /who/ and not on the
            person page, which says so ("No record has been found for them"): two pages for one name, left for David to rule on
            (see tools/namesakes-who-known.json, each entry with the reason). A NEW one fails; so does an entry that no longer
            overlaps (the list only shrinks, on purpose and by hand).
  redirect  a /who/<slug>/ that is a static redirect (a meta refresh stub, 23 November 2026) is not one the ruling lists
            (tools/who-fold-rulings.json, key "redirect": the names whose every line is set out on the one person page that bears
            them), or does not land on /people/<same slug>/, or is not noindex with that page as its canonical; and a name the
            ruling lists is not a stub. A stub is no dossier, so it is never a "filed" name: the six redirects are not in
            tools/namesakes-who-known.json.
  index     /who/ links to a /who/<slug>/ that is not built.

A living person is never named in a message (their slug can carry a year): their page is reported as "a living person's page".
Exit 0 clean, 1 findings, 2 it could not see what it checks (no build, no person page, no /who/ index).
"""
import argparse
import html
import json
import os
import re
import sys
import unicodedata

SECTION = "namesakes"
HERE = os.path.dirname(os.path.abspath(__file__))
KNOWN = os.path.join(HERE, "namesakes-who-known.json")


def fold(s):
    s = unicodedata.normalize("NFD", html.unescape(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def text_of(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def read_pages(dist):
    pages = {}
    for root, _dirs, files in os.walk(dist):
        if "index.html" in files:
            rel = os.path.relpath(root, dist).replace(os.sep, "/")
            route = "/" if rel == "." else "/" + rel + "/"
            if not (route.startswith("/people/") or route.startswith("/who/") or route == "/who/"):
                continue
            with open(os.path.join(root, "index.html"), encoding="utf-8", errors="replace") as f:
                pages[route] = f.read()
    return pages


def h1_of(raw):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    return text_of(m.group(1)) if m else ""


def is_noindex(raw):
    return bool(re.search(r'<meta name="robots" content="[^"]*noindex', raw[:8000]))


def listed(raw):
    """(has the section, the person pages its list links to)"""
    m = re.search(r'<section[^>]*\bid="%s"' % SECTION, raw)
    if not m:
        return False, []
    tail = raw[m.end():]
    end = tail.find("</section>")
    return True, re.findall(r'href="(/people/[^"#?]+/)"', tail[: end if end >= 0 else len(tail)])


def load_known(path=KNOWN):
    try:
        with open(path, encoding="utf-8") as f:
            return {e["slug"]: e for e in json.load(f)["known"]}
    except Exception:
        return None


def is_stub(raw):
    """a static redirect written by astro: a meta refresh and no page"""
    return bool(re.search(r'<meta http-equiv="refresh"', raw[:2000])) and "<h1" not in raw


def load_redirects(path=None):
    try:
        with open(path or os.path.join(HERE, "who-fold-rulings.json"), encoding="utf-8") as f:
            return list(json.load(f).get("redirect", []))
    except Exception:
        return None


def check(pages, known, redirects=None):
    """(findings, counts, setof) over an in-memory build: route -> html."""
    if redirects is None:
        redirects = load_redirects()
    persons = {}
    for route, raw in pages.items():
        if route.startswith("/people/") and route != "/people/" and "data-person-page" in raw:
            persons[route] = {"h1": h1_of(raw), "living": is_noindex(raw)}
    allwho = {r: raw for r, raw in pages.items() if r.startswith("/who/") and r != "/who/"}
    who = {r: raw for r, raw in allwho.items() if not is_stub(raw)}
    stubs = {r: raw for r, raw in allwho.items() if is_stub(raw)}
    if not persons or "/who/" not in pages:
        return None, {}, {}
    label = lambda r: "a living person's page" if persons.get(r, {}).get("living") else r
    findings = []

    folded = {r: fold(p["h1"]) for r, p in persons.items()}
    group = {}
    for r, f in folded.items():
        if not persons[r]["living"]:
            group.setdefault(f, []).append(r)
    setof = {}
    for r, f in folded.items():
        setof[r] = set() if persons[r]["living"] else set(group[f]) - {r}

    with_section = shared_pages = 0
    for r, others in sorted(setof.items()):
        has, got = listed(pages[r])
        with_section += has
        shared_pages += bool(others)
        if persons[r]["living"]:
            if has:
                findings.append("living: %s carries a #%s list" % (label(r), SECTION))
            continue
        if others and not has:
            findings.append("absent: %s shares its name with %d other page(s) and has no #%s section" % (label(r), len(others), SECTION))
            continue
        if has and not others:
            findings.append("absent: %s has a #%s section and nobody shares its name" % (label(r), SECTION))
        miss = sorted(others - set(got))
        extra = sorted(set(got) - others)
        if miss:
            findings.append("missing: %s does not list %d of its name: %s" % (label(r), len(miss), ", ".join(label(x) for x in miss)))
        if extra:
            findings.append("extra: %s lists %d that do not carry its name: %s" % (label(r), len(extra), ", ".join(label(x) for x in extra)))

    # ---- the /who/ addresses that are redirects: exactly the ruling's, each to its person page
    if redirects is None:
        findings.append("redirect: tools/who-fold-rulings.json cannot be read")
        redirects = []
    for slug in sorted(set(redirects)):
        r = "/who/%s/" % slug
        if r not in stubs:
            findings.append("redirect: %s is in the ruling as a redirect and is not one" % r)
    for r, raw in sorted(stubs.items()):
        slug = r[len("/who/"):-1]
        to = "/people/%s/" % slug
        if slug not in redirects:
            findings.append("redirect: %s is a redirect and the ruling does not list it" % r)
        elif to not in persons:
            findings.append("redirect: %s redirects to %s, which is not a person page" % (r, to))
        elif not (('content="0;url=%s"' % to) in raw and ('<meta name="robots" content="noindex">' in raw) and re.search(r'rel="canonical" href="[^"]*%s"' % re.escape(to), raw)):
            findings.append("redirect: %s does not land on %s with noindex and that page as its canonical" % (r, to))

    # ---- the /who/ dossiers that share a name with a person page
    overlapping = set()
    for r, raw in sorted(who.items()):
        if folded and fold(h1_of(raw)) in set(folded.values()):
            overlapping.add(r[len("/who/"):-1])
    if known is None:
        findings.append("filed: tools/namesakes-who-known.json cannot be read")
        known = {}
    for slug in sorted(overlapping - set(known)):
        findings.append("filed: /who/%s/ is a dossier for a name a person page carries and is not in tools/namesakes-who-known.json" % slug)
    for slug in sorted(set(known) - overlapping):
        findings.append("filed: tools/namesakes-who-known.json lists %s, which no longer shares a name with a person page (remove it)" % slug)

    # ---- the index
    idx = pages["/who/"]
    for h in sorted(set(re.findall(r'href="(/who/[^"#?]+/)"', idx))):
        if h not in who:
            findings.append("index: /who/ links to %s, which is not built" % h)

    counts = {"person pages": len(persons), "with a list": with_section, "pages whose name is shared": shared_pages,
              "/who/ dossiers": len(who), "of them filed under a name a person page carries": len(overlapping), "/who/ redirects": len(stubs)}
    return findings, counts, setof


def selftest(pages, known):
    f0, _c, setof = check(pages, known)
    ok = True
    print("  control: the untouched build -> %d finding(s)%s" % (len(f0), "" if not f0 else "  <-- SHOULD BE 0"))
    if f0:
        ok = False
    shared = sorted(r for r, o in setof.items() if o)
    solo = sorted(r for r, o in setof.items() if not o and not re.search(r'noindex', pages[r][:8000]))
    living = sorted(r for r in setof if re.search(r'<meta name="robots" content="[^"]*noindex', pages[r][:8000]) and "data-person-page" in pages[r])
    if not shared or not solo or not known:
        print("  nothing shared, unshared or filed to plant against: refusing")
        return False
    a = shared[0]
    other = sorted(setof[a])[0]

    stubs_ = sorted(r for r in pages if r.startswith("/who/") and r != "/who/" and is_stub(pages[r]))

    def planted(name, mutate, want, kn=None, rd=None):
        nonlocal ok
        v = dict(pages)
        mutate(v)
        got, _c2, _s = check(v, known if kn is None else kn, rd)
        hit = any(g.startswith(want) for g in (got or []))
        print("  %-52s %s" % (name, "caught" if hit else "MISSED  <-- the gate cannot see this"))
        ok = ok and hit

    planted("a person of the name left off a list",
            lambda v: v.__setitem__(a, re.sub(r'<li[^>]*>(?:(?!</li>).)*?href="%s".*?</li>' % re.escape(other), "", v[a], count=1, flags=re.S)), "missing")

    def add_stranger(v):
        i = v[a].index('id="%s"' % SECTION)
        j = v[a].index("</ul>", i)
        v[a] = v[a][:j] + '<li><a href="%s">x</a></li>' % solo[0] + v[a][j:]
    planted("a stranger added to a list", add_stranger, "extra")
    planted("a list on a name nobody shares",
            lambda v: v.__setitem__(solo[0], v[solo[0]].replace("</main>", '<section class="psec" id="%s"><ul><li><a href="%s">x</a></li></ul></section></main>' % (SECTION, a), 1)), "absent")
    planted("a shared name with no section", lambda v: v.__setitem__(a, v[a].replace('id="%s"' % SECTION, 'id="nothing"')), "absent")
    if living:
        planted("a list on a living person's page",
                lambda v: v.__setitem__(living[0], v[living[0]].replace("</main>", '<section class="psec" id="%s"><ul><li><a href="%s">x</a></li></ul></section></main>' % (SECTION, a), 1)), "living")
        planted("a living person listed as a namesake",
                lambda v: v.__setitem__(a, re.sub(r'(id="%s".*?<ul[^>]*>)' % SECTION, r'\1<li><a href="%s">x</a></li>' % living[0], v[a], count=1, flags=re.S)), "extra")
    planted("a /who/ dossier filed under a person's name, unlisted", lambda v: None, "filed", kn={k: x for k, x in list(known.items())[1:]})
    planted("a known entry that no longer overlaps", lambda v: None, "filed", kn=dict(known, **{"nobody-of-this-name": {"slug": "nobody-of-this-name"}}))
    if stubs_:
        sr = stubs_[0]
        planted("a redirect that is a page again", lambda v: v.__setitem__(sr, "<html><h1>Someone</h1></html>"), "redirect")
        planted("a redirect the ruling does not list", lambda v: None, "redirect", rd=[x for x in (load_redirects() or []) if "/who/%s/" % x != sr])
        planted("a redirect to the wrong person", lambda v: v.__setitem__(sr, v[sr].replace("/people/", "/people/x-", 2)), "redirect")
    planted("a link on /who/ to a page that is not built", lambda v: v.__setitem__("/who/", v["/who/"].replace("</main>", '<a href="/who/not-built-at-all/">x</a></main>', 1)), "index")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dist):
        print("checknamesakes: %s is not a directory; nothing was checked" % a.dist)
        return 2
    pages = read_pages(a.dist)
    known = load_known()
    if a.selftest:
        return 0 if selftest(pages, known) else 1
    findings, counts, _setof = check(pages, known)
    if findings is None:
        print("checknamesakes: no person page or no /who/ index in %s; nothing was checked" % a.dist)
        return 2
    for f in findings:
        print("  FAIL  " + f)
    print("checknamesakes: " + ", ".join("%d %s" % (v, k) for k, v in counts.items()) + "; %d finding%s" % (len(findings), "" if len(findings) == 1 else "s"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

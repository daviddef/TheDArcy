#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The /who/ research text on the person pages: is it exactly where the ruling puts it, and nowhere else?

    python3 ../tools/checkwhofold.py --dist "${ARCHIVE_OUT:-dist}"        # from site/; `npm run check:who-fold`
    python3 ../tools/checkwhofold.py --selftest --dist dist               # plants one fault per rule

WHAT IT HOLDS (23 November 2026). /who/<slug>/ is a dossier of register lines about a name; where a person page carries the same name,
tools/who-fold-rulings.json says line by line which lines are ALSO set out on that person's page (a "fold") and which pages only link to
the dossier (a "pointer"). This gate reads the RULING and site/src/data/dossiers.json (the data /who/ is built from), and nothing the
person-page generator or tools/build_who_fold.py wrote, and checks the BUILT pages:

  missing    a line the ruling folds onto a page (its text and its source, accents, case and punctuation folded) is not in that page's
             section "Records filed under the name ...".
  elsewhere  a folded line's text is on the built page of any OTHER person: a line is one person's.
  extra      a person page carries a fold section it is not designated for, or carries more lines than the ruling gives it.
  kept       a folded line is no longer on its /who/ page: a fold is a copy, never a move. (Not asked of a name the ruling lists under
             "redirect": its /who/ address is a redirect to the person page, and the line is on that page.)
  dossier    the section does not open with a link to the dossier the ruling names, or that dossier is not built. (Names inside the
             lines are linked by the build's autolink pass, to their own pages and dossiers, and are not the section's link.) For a
             name under "redirect" the section links to NO /who/ page: there is none.
  linked     a built page links to /who/<slug>/ of a name under "redirect": every link to it goes to the person page.
  living     a fold or pointer section on a noindex page (a living person's), or a designated page that is noindex.
  year       a folded line's text prints a year on or after 1946 (the kit's living cutoff): a line about someone alive is never moved.
             (A source's own coverage, "1538-1975", is not the line.)
  pointer    a designated pointer page has no link to its dossier, a page carries a pointer it is not designated for, or an
             'elsewhere' pointer does not link to the page that sets the lines out.
  unfiled    a /who/ dossier shares its name (accents and case folded) with a person page that the ruling neither folds into nor points
             from: a NEW overlap fails until somebody rules on it.
  ruling     the ruling names a dossier, a line or a person page that does not exist, or lists under "redirect" a name that is not folded
             in full onto the one person page of its name, with a fold of kind 'agrees', or that a pointer needs.

A living person is never named in a message: their page is reported as "a living person's page". Exit 0 clean, 1 findings, 2 it could not
see what it checks (no build, no person page, no /who/ index, no ruling).
"""
import argparse
import html
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RULINGS = os.path.join(HERE, "who-fold-rulings.json")
DOSSIERS = os.path.join(ROOT, "site", "src", "data", "dossiers.json")
CUTOFF = 1946
FOLD_ID = "more-records-filed-under-the-name-"
POINT_ID = "more-read-the-research-on-the-name-"


def unaccent(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def fold(s):
    """name fold: letters and digits, runs of anything else as one space"""
    return re.sub(r"[^a-z0-9]+", " ", unaccent(html.unescape(s or "")).lower()).strip()


def squash(s):
    """text fold: letters and digits only, so a link wrapped round a name or a changed quote cannot hide a line"""
    return re.sub(r"[^a-z0-9]+", "", unaccent(html.unescape(s or "")).lower())


def plain(raw):
    t = re.sub(r"<(script|style)\b.*?</\1>", "", raw, flags=re.S)
    return re.sub(r"<[^>]+>", "", t)


def read_pages(dist):
    pages = {}
    for root, _dirs, files in os.walk(dist):
        if "index.html" in files:
            rel = os.path.relpath(root, dist).replace(os.sep, "/")
            route = "/" if rel == "." else "/" + rel + "/"
            if True:
                with open(os.path.join(root, "index.html"), encoding="utf-8", errors="replace") as f:
                    pages[route] = f.read()
    return pages


def h1_of(raw):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip() if m else ""


def is_noindex(raw):
    return bool(re.search(r'<meta name="robots" content="[^"]*noindex', raw[:8000]))


def section(raw, prefix):
    """the html of the <section> whose id starts with prefix, or None"""
    m = re.search(r'<section\b[^>]*\bid="%s[^"]*"' % re.escape(prefix), raw)
    if not m:
        return None
    tail = raw[m.start():]
    end = tail.find("</section>")
    return tail[: end if end >= 0 else len(tail)]


def is_stub(raw):
    """a static redirect written by astro: a meta refresh and no page"""
    return bool(re.search(r'<meta http-equiv="refresh"', raw[:2000])) and "<h1" not in raw


def check(pages, rulings, dossiers):
    """(findings, counts) over an in-memory build: route -> html."""
    persons = {r: p for r, p in pages.items() if r.startswith("/people/") and r != "/people/" and "data-person-page" in p}
    redirects = set(rulings.get("redirect", []))
    whos = {r: p for r, p in pages.items() if r.startswith("/who/") and r != "/who/" and not is_stub(p)}
    if not persons or "/who/" not in pages or not whos:
        return None, {}
    living = {r: is_noindex(p) for r, p in persons.items()}
    label = lambda r: "a living person's page" if living.get(r) else r
    flat = {r: squash(plain(p)) for r, p in persons.items()}
    findings = []
    folded_to = {}      # route -> (who slug, [row dicts])
    pointed = {}        # route -> ruling entry

    for e in rulings.get("fold", []):
        who = dossiers.get(e["who"])
        route = "/people/%s/" % e["to"]
        if who is None:
            findings.append("ruling: fold names the dossier %s, which is not in dossiers.json" % e["who"])
            continue
        if route not in persons:
            findings.append("ruling: fold names %s, which is not a built person page" % route)
            continue
        rows = []
        for i in e["rows"]:
            if not isinstance(i, int) or not 0 <= i < len(who["rows"]):
                findings.append("ruling: fold %s names line %r, which the dossier does not have" % (e["who"], i))
                continue
            rows.append(who["rows"][i])
        folded_to[route] = (e["who"], rows)
    for e in rulings.get("pointer", []):
        for to in e["to"]:
            route = "/people/%s/" % to
            if e["who"] not in dossiers or route not in persons:
                findings.append("ruling: pointer %s -> %s names something that is not built" % (e["who"], to))
                continue
            pointed[route] = e

    # ---- every designated line is on its page, once, and on no other person's page
    n_lines = 0
    for route, (who, rows) in sorted(folded_to.items()):
        raw = persons[route]
        sec = section(raw, FOLD_ID)
        if living[route]:
            findings.append("living: %s is designated for a fold and is noindex" % label(route))
            continue
        if sec is None:
            findings.append("missing: %s has no 'Records filed under the name' section; the ruling gives it %d line(s)" % (route, len(rows)))
            continue
        flat_sec = squash(plain(sec))
        for r in rows:
            n_lines += 1
            if squash(r["says"]) not in flat_sec:
                findings.append("missing: %s lacks a line the ruling folds onto it: %s" % (route, r["says"][:70]))
            if squash(re.sub(r"^record · ", "", r["source"])) not in flat_sec:
                findings.append("missing: %s lacks the source of a folded line: %s" % (route, r["says"][:50]))
            for other, text in flat.items():
                if other != route and squash(r["says"]) in text:
                    findings.append("elsewhere: a line folded onto %s is also on %s: %s" % (label(route), label(other), r["says"][:60]))
            wp = "/who/%s/" % who
            if who not in redirects and (wp not in whos or squash(r["says"]) not in squash(plain(whos[wp]))):
                findings.append("kept: a folded line is not on %s: %s" % (wp, r["says"][:60]))
            for y in re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", r["says"]):
                if int(y) >= CUTOFF:
                    findings.append("year: a folded line prints %s: %s" % (y, r["says"][:60]))
        got = len(re.findall(r">record</span>", sec))
        if got != len(rows):
            findings.append("extra: %s shows %d line(s) in its section and the ruling gives it %d" % (route, got, len(rows)))
        links = re.findall(r'href="(/who/[^"#?]+/)"', sec)
        if who in redirects:
            bad = [x for x in links if x[len("/who/"):-1] in redirects]
            if bad:
                findings.append("dossier: %s's section links to %s, which is a redirect and no page" % (route, bad[0]))
        elif not links or links[0] != "/who/%s/" % who or "/who/%s/" % who not in whos:
            findings.append("dossier: %s's section opens with a link to %s and the ruling names the built dossier /who/%s/" % (route, links[0] if links else "no dossier", who))

    # ---- no section where the ruling gives none, and none on a living page
    for route, raw in sorted(persons.items()):
        f, p = section(raw, FOLD_ID), section(raw, POINT_ID)
        if living[route] and (f is not None or p is not None):
            findings.append("living: %s carries a who-fold section" % label(route))
            continue
        if f is not None and route not in folded_to:
            findings.append("extra: %s carries a 'Records filed under the name' section and the ruling gives it none" % route)
        if p is not None and route not in pointed:
            findings.append("pointer: %s carries a pointer to a dossier and the ruling gives it none" % route)
        if f is not None and p is not None:
            findings.append("extra: %s carries both a fold and a pointer" % route)

    # ---- pointers
    for route, e in sorted(pointed.items()):
        if living[route]:
            findings.append("living: %s is designated for a pointer and is noindex" % label(route))
            continue
        sec = section(persons[route], POINT_ID)
        if sec is None:
            findings.append("pointer: %s has no pointer section; the ruling gives it one" % route)
            continue
        links = set(re.findall(r'href="(/(?:who|people)/[^"#?]+/)"', sec))
        if "/who/%s/" % e["who"] not in links or "/who/%s/" % e["who"] not in whos:
            findings.append("pointer: %s does not link to the built dossier /who/%s/" % (route, e["who"]))
        if e.get("why") == "elsewhere" and "/people/%s/" % e.get("elsewhere") not in links:
            findings.append("pointer: %s says the lines are another bearer's and does not link to /people/%s/" % (route, e.get("elsewhere")))

    # ---- the redirects: each folded in full, and nothing links to the address any more
    folded_who = {}
    for e in rulings.get("fold", []):
        folded_who.setdefault(e["who"], []).append(e)
    for who in sorted(redirects):
        w = dossiers.get(who)
        es = folded_who.get(who, [])
        if w is None or len(es) != 1:
            findings.append("ruling: redirect %s needs a dossier and exactly one fold" % who)
        elif sorted(set(es[0]["rows"])) != list(range(len(w["rows"]))) or es[0].get("kind") != "agrees" or es[0]["to"] != who:
            findings.append("ruling: redirect %s is not folded in full onto /people/%s/ as 'agrees'" % (who, who))
        if any(who in e["to"] and e["who"] == who for e in rulings.get("pointer", [])):
            findings.append("ruling: redirect %s still has a pointer" % who)
    for r, raw in sorted(pages.items()):
        if is_stub(raw):
            continue
        for h in set(re.findall(r'href="/who/([^"#?/]+)/?(?:[#?][^"]*)?"', raw)):
            if h in redirects:
                findings.append("linked: %s links to /who/%s/, which is a redirect to the person page" % (label(r) if r in persons else r, h))

    # ---- a name a dossier and a person page both carry is ruled on, on every such page
    byname = {}
    for r in persons:
        if not living[r]:
            byname.setdefault(fold(h1_of(persons[r])), []).append(r)
    overlaps = 0
    for wr, raw in sorted(whos.items()):
        for r in byname.get(fold(h1_of(raw)), []):
            overlaps += 1
            if r not in folded_to and r not in pointed:
                findings.append("unfiled: %s carries the name of the dossier %s and the ruling neither folds into it nor points from it" % (r, wr))

    counts = {"person pages": len(persons), "/who/ dossiers": len(whos), "redirects": len(redirects), "pages sharing a dossier's name": overlaps,
              "lines folded": n_lines, "pages folded into": len(folded_to), "pages pointing": len(pointed)}
    return findings, counts


def selftest(pages, rulings, dossiers):
    f0, c0 = check(pages, rulings, dossiers)
    ok = True
    print("  control: the untouched build -> %d finding(s)%s" % (len(f0 or []), "" if not f0 else "  <-- SHOULD BE 0"))
    if f0:
        ok = False
    folds = sorted(r for r in pages if r.startswith("/people/") and section(pages[r], FOLD_ID))
    points = sorted(r for r in pages if r.startswith("/people/") and section(pages[r], POINT_ID))
    plainp = sorted(r for r in pages if r.startswith("/people/") and r != "/people/" and "data-person-page" in pages[r]
                    and not section(pages[r], FOLD_ID) and not section(pages[r], POINT_ID) and not is_noindex(pages[r]))
    livingp = sorted(r for r in pages if r.startswith("/people/") and r != "/people/" and "data-person-page" in pages[r] and is_noindex(pages[r]))
    if not folds or not points or not plainp or not livingp:
        print("  nothing folded, pointed, plain or living to plant against: refusing")
        return False
    reds = set(rulings.get("redirect", []))
    linking = [r for r in folds if re.search(r'href="/who/', section(pages[r], FOLD_ID))]
    redirected = [r for r in folds if r[len("/people/"):-1] in reds]
    if not linking or not redirected:
        print("  no fold that links to its dossier, or no redirected name, to plant against: refusing")
        return False
    a = linking[0]
    sec_a = section(pages[a], FOLD_ID)
    who_a = re.search(r'href="(/who/[^"#?]+/)"', sec_a).group(1)
    b = redirected[0]
    sec_b = section(pages[b], FOLD_ID)
    slug_b = b[len("/people/"):-1]

    def planted(name, mutate, want, rul=None, dos=None):
        nonlocal ok
        v = dict(pages)
        mutate(v)
        got, _c = check(v, rulings if rul is None else rul, dossiers if dos is None else dos)
        hit = any(g.startswith(want) for g in (got or []))
        print("  %-60s %s" % (name, "caught" if hit else "MISSED  <-- the gate cannot see this"))
        ok = ok and hit

    rows_html = re.findall(r'<div style="border-left[^"]*">.*?</div>', sec_a, re.S)
    row_a = rows_html[0]
    planted("a folded line left off its page", lambda v: v.__setitem__(a, v[a].replace(row_a, "", 1)), "missing")
    planted("the section left off its page", lambda v: v.__setitem__(a, v[a].replace(sec_a, "", 1)), "missing")
    txt = html.escape(html.unescape(plain(re.search(r"<p>(.*?)</p>", row_a, re.S).group(1))))
    piece = re.match(r"[A-Za-z0-9 ]{12,}", html.unescape(plain(row_a)).strip()).group(0)[:20]
    planted("a folded line on another person's page",
            lambda v: v.__setitem__(plainp[0], v[plainp[0]].replace("</main>", "<p>%s</p></main>" % txt, 1)), "elsewhere")
    planted("a fold section on a page the ruling gives none",
            lambda v: v.__setitem__(plainp[0], v[plainp[0]].replace("</main>", sec_a + "</section></main>", 1)), "extra")
    planted("a fold section on a living person's page",
            lambda v: v.__setitem__(livingp[0], v[livingp[0]].replace("</main>", sec_a + "</section></main>", 1)), "living")
    planted("a second copy of a line in a section", lambda v: v.__setitem__(a, v[a].replace(row_a, row_a + row_a, 1)), "extra")
    planted("the section's link goes to another dossier", lambda v: v.__setitem__(a, v[a].replace(sec_a, sec_a.replace(who_a, "/who/someone-else/"), 1)), "dossier")
    planted("a pointer on a page the ruling gives none",
            lambda v: v.__setitem__(plainp[0], v[plainp[0]].replace("</main>", section(v[points[0]], POINT_ID) + "</section></main>", 1)), "pointer")
    pt = section(pages[points[0]], POINT_ID)
    pw = re.search(r'href="(/who/[^"#?]+/)"', pt).group(1)
    planted("a pointer that no longer links to its dossier", lambda v: v.__setitem__(points[0], v[points[0]].replace(pt, pt.replace(pw, "/people/"), 1)), "pointer")
    planted("a folded line gone from its /who/ page (a move)",
            lambda v: v.__setitem__(who_a, v[who_a].replace(piece, "x" * len(piece))), "kept")
    planted("a redirected name's lines left off its person page", lambda v: v.__setitem__(b, v[b].replace(sec_b, "", 1)), "missing")
    planted("a link to a redirected /who/ address from another page",
            lambda v: v.__setitem__(plainp[0], v[plainp[0]].replace("</main>", '<a href="/who/%s/">x</a></main>' % slug_b, 1)), "linked")
    planted("a redirected name's section linking to its /who/ address",
            lambda v: v.__setitem__(b, v[b].replace(sec_b, sec_b.replace('<div style="border-left', '<a href="/who/%s/">x</a><div style="border-left' % slug_b, 1), 1)), "dossier")
    planted("a redirect for a dossier not folded in full", lambda v: None, "ruling", rul=dict(rulings, redirect=sorted(reds | {"edward-saniger"})))
    planted("a redirect for a fold that only fits", lambda v: None, "ruling", rul=dict(rulings, redirect=sorted(reds | {"christian-saniger"})))
    r_drop = dict(rulings, fold=[e for e in rulings["fold"] if "/people/%s/" % e["to"] != a])
    planted("a dossier name a person page carries, left unruled", lambda v: None, "unfiled", rul=r_drop)
    d_year = json.loads(json.dumps(dossiers))
    for e in rulings["fold"]:
        if "/people/%s/" % e["to"] == a:
            d_year[e["who"]]["rows"][e["rows"][0]]["says"] += " and again in 1999"
    planted("a folded line that prints a year after the cutoff", lambda v: None, "year", dos=d_year)
    r_bad = json.loads(json.dumps(rulings))
    r_bad["fold"][0]["rows"] = [99]
    planted("a ruling that names a line the dossier lacks", lambda v: None, "ruling", rul=r_bad)
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dist):
        print("checkwhofold: %s is not a directory; nothing was checked" % a.dist)
        return 2
    try:
        rulings = json.load(open(RULINGS, encoding="utf-8"))
        dossiers = json.load(open(DOSSIERS, encoding="utf-8"))["people"]
    except Exception as e:
        print("checkwhofold: cannot read the ruling or the dossiers (%s)" % e)
        return 2
    pages = read_pages(a.dist)
    if a.selftest:
        return 0 if selftest(pages, rulings, dossiers) else 1
    findings, counts = check(pages, rulings, dossiers)
    if findings is None:
        print("checkwhofold: no person page or no /who/ index in %s; nothing was checked" % a.dist)
        return 2
    for f in findings:
        print("  FAIL  " + f)
    print("checkwhofold: " + ", ".join("%d %s" % (v, k) for k, v in counts.items()) + "; %d finding%s" % (len(findings), "" if len(findings) == 1 else "s"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

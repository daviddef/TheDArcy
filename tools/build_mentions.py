#!/usr/bin/env python3
"""Find every mention of every published person across the whole site.

Two outputs:
  site/src/data/mentions.json   {slug: [{path, title, snippet}, ...]}
                                consumed at build time by /people/[slug]
  site/public/whoindex.json     [[name, slug, count, kind, n], ...]
                                the SAME resolution the build-time linker uses
                                (tools/build_names_index.py reads this file's rules
                                through built_pages/name_groups below); since 18
                                October 2026 no script in the browser reads it, and
                                tools/check_whoindex.py, check_living_standard.py
                                and selftest.py still grade it.
                                kind "p": a /people/ page, "w": a /who/ page
                                (a witness, an official), "a": AMBIGUOUS, a name
                                borne by n >= 2 pages, slug "" (the linker sends it
                                to /people/?q=<name>, never to a guess)

This reads the BUILT html rather than the .astro sources, because the sources
are full of expressions and components and the rendered text is what a reader
actually sees. That makes the build two-pass:

    npm run build && python3 tools/build_mentions.py && npm run build

The first pass produces pages to scan; the second bakes the mentions in. Running
it on a site with no dist/ simply writes empty indexes, which is harmless.
"""
import json, os, re, html, sys
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import outdir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = outdir.out()
DATA = os.path.join(ROOT, "site", "src", "data")
PUB  = os.path.join(ROOT, "site", "public")

# Pages that are lists of everybody rather than writing about anybody. A name in
# a card grid is not a mention; counting them would make every person look
# equally well documented, which is the opposite of this archive's whole point.
# Directory pages, not prose. A page that lists every person by name would
# otherwise "mention" every person, which tells a reader nothing and drowns the
# handful of pages that actually write about them.
# /contents and /part/ are the BOOK's own table and part openers (src/data/book.json): a chapter's
# title and one line beside every chapter name, so a person named in a blurb is not "mentioned" there.
SKIP_PREFIX = ("/people", "/families", "/places", "/register", "/who",
               "/households", "/marriages", "/graves", "/search", "/contents", "/part")

# A page that says <meta name="robots" content="noindex"> is a living person's
# (David's ruling of 16 October 2026: a living person is named, with their town
# and country, and nothing more; their page is noindex). Such a person is not
# gathered here: no mentions are collected about them, and their name does not
# go into whoindex.json, which wholink.js uses to turn a name in prose into a
# link. A living person is named where a relative's page names them; this
# archive does not go looking for more of them.
NOINDEX = re.compile(r'<meta[^>]*name=["\']robots["\'][^>]*noindex', re.I)

TAGS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


# THE BOOK'S OWN FURNITURE IS NOT PROSE (18 October 2026). BookFoot sits inside <main> (Base.astro), and
# the foot names the neighbouring chapters, so a fresh build turned each neighbour's title into a
# "mention" of any person it happens to contain: nine of them, none of them written about anybody.
# The foot is a <nav class="bk-foot"> carrying data-book-prev / data-book-next; the running head is a
# <div class="bk-head">. Both are cut before the text is read. Neither is moved: the layout is the kit's.
BOOK_NAV = re.compile(r"<nav\b[^>]*\b(?:class=[\"'][^\"']*\bbk-foot\b|data-book-prev|data-book-next)[^>]*>.*?</nav>", re.S | re.I)
BOOK_HEAD = re.compile(r"<div\b[^>]*\bclass=[\"'][^\"']*\bbk-head\b[^>]*>", re.I)
DIV = re.compile(r"<(/?)div\b[^>]*>", re.I)


def drop_book_furniture(raw):
    """Remove the book's Previous/Next foot and its running head from a page's HTML."""
    raw = BOOK_NAV.sub(" ", raw)
    while True:
        m = BOOK_HEAD.search(raw)
        if not m:
            return raw
        depth, end = 1, None
        for d in DIV.finditer(raw, m.end()):
            depth += -1 if d.group(1) else 1
            if depth == 0:
                end = d.end()
                break
        if end is None:          # unbalanced: cut only the opening tag rather than eat the page
            end = m.end()
        raw = raw[:m.start()] + " " + raw[end:]


# NAMESAKES (18 October 2026). `by_name = {name: slug}` collapsed every name two
# people share to one arbitrary slug, so "George Pitt D'Arcy" always went to the
# 1864 man, and 62 of the 153 links wholink.js made on twelve narrative pages
# pointed at one of several people of that name. A name is now linked to a person
# ONLY when exactly one page bears it; otherwise the row is "a" and the reader is
# sent to the search. Case is folded, a living person (a noindex page) counts as
# a namesake but is never given a row, and a declared copy of another page
# (canonical naming a different /people/ page) is the same person and not a
# namesake. tools/check_whoindex.py grades the result.
CANON = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)


def fold(s):
    """The key two spellings of one name share: case, spacing, curly apostrophes."""
    return WS.sub(" ", s.replace("\u2019", "'").replace("\u2018", "'")).strip().casefold()


def built_pages(dist=None):
    """{(kind, slug): {name, noindex, dup}} for every built /people/ and /who/ page."""
    out = {}
    for kind in ("people", "who"):
        d = os.path.join(dist or DIST, kind)
        for slug in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            f = os.path.join(d, slug, "index.html")
            if not os.path.isfile(f):
                continue
            raw = open(f, encoding="utf-8", errors="ignore").read()
            name, _ = text_of(f)
            c = CANON.search(raw)
            dup = bool(c and "/people/" in c.group(1)
                       and c.group(1).rstrip("/").rsplit("/", 1)[-1] != slug)
            out[(kind, slug)] = {"name": name, "noindex": bool(NOINDEX.search(raw)), "dup": dup}
    return out


def name_groups(pages):
    """{folded name: [(kind, slug, name, noindex)]} for names of two words or more."""
    groups = {}
    for (kind, slug), e in pages.items():
        if e["dup"] or len(e["name"].split()) < 2:
            continue
        groups.setdefault(fold(e["name"]), []).append((kind, slug, e["name"], e["noindex"]))
    return groups


def index_rows(groups, pages_for):
    """The rows of whoindex.json: one per name that is published and written about."""
    rows = []
    for key, members in groups.items():
        pub = [m for m in members if not m[3]]
        n = len(pages_for.get(key, ()))
        if not pub or not n:
            continue
        if len(members) == 1:
            kind, slug, name, _ = members[0]
            rows.append([name, slug, n, "p" if kind == "people" else "w", 1])
        elif any(m[0] == "people" for m in pub):
            name = sorted(m[2] for m in pub)[0]
            rows.append([name, "", n, "a", len(members)])
    rows.sort(key=lambda r: (-len(r[0]), r[0].casefold(), r[1]))
    return rows


# THE LINKS THE BUILD-TIME LINKER ADDS ARE NOT TEXT (18 October 2026): see tools/autolink_strip.py. The wrappers
# come off before the page is read, so mentions.json and whoindex.json read the page as they did before the pass.
from autolink_strip import plain as _unlinked


def text_of(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    raw = _unlinked(raw)
    raw = drop_book_furniture(raw)
    title = ""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    if m:
        title = WS.sub(" ", html.unescape(STRIP.sub(" ", m.group(1)))).strip()
    # the nav and footer repeat on every page; cut to <main> where we can
    body = raw
    mm = re.search(r"<main[^>]*>(.*?)</main>", raw, re.S)
    if mm:
        body = mm.group(1)
    body = TAGS.sub(" ", body)
    return title, WS.sub(" ", html.unescape(STRIP.sub(" ", body))).strip()


def main():
    if not os.path.isdir(DIST):
        print("no dist/ — run `npm run build` first; writing empty indexes")
        people = {}
    else:
        # slug -> name, straight off the built person pages
        people = {}
        pdir = os.path.join(DIST, "people")
        for slug in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
            f = os.path.join(pdir, slug, "index.html")
            if not os.path.isfile(f):
                continue
            if NOINDEX.search(open(f, encoding="utf-8", errors="ignore").read()):
                continue
            name, _ = text_of(f)
            # a bare surname or a single word matches far too much
            if name and len(name.split()) >= 2:
                people[slug] = name

    # longest names first so "Arthur William Hartley Sneyd" wins over "Arthur Sneyd"
    ordered = sorted(people.items(), key=lambda kv: -len(kv[1]))
    if ordered:
        pattern = re.compile(
            r"(?<![A-Za-zÀ-ɏ])(" +
            "|".join(re.escape(n) for _, n in ordered) +
            r")(?![A-Za-zÀ-ɏ])")
        by_name = {n: s for s, n in people.items()}
    else:
        pattern, by_name = None, {}

    mentions = {s: [] for s in people}

    bodies = []                      # (path, title, body) of every prose page
    if os.path.isdir(DIST):
        for root, _, files in os.walk(DIST):
            if "index.html" not in files:
                continue
            rel = os.path.relpath(root, DIST).replace(os.sep, "/")
            path = "/" if rel == "." else "/" + rel
            if any(path == p or path.startswith(p + "/") for p in SKIP_PREFIX):
                continue
            title, body = text_of(os.path.join(root, "index.html"))
            bodies.append((path, title, body))

    if pattern:
        for path, title, body in bodies:
            seen = set()
            for m in pattern.finditer(body):
                slug = by_name.get(m.group(1))
                if not slug or (slug, path) in seen:
                    continue
                seen.add((slug, path))
                a, b = max(0, m.start() - 90), min(len(body), m.end() + 130)
                snip = ("…" if a else "") + body[a:b].strip() + ("…" if b < len(body) else "")
                mentions[slug].append({"path": path, "title": title or path, "snippet": snip})

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "mentions.json"), "w", encoding="utf-8") as f:
        json.dump(mentions, f, ensure_ascii=False, indent=0, sort_keys=True)

    # Only names that are actually written about anywhere go in the run-time index,
    # so wholink does not turn every name in a list into a link. A name two or more
    # pages bear is written "a" with no slug (see NAMESAKES above).
    pages = built_pages() if os.path.isdir(DIST) else {}
    groups = name_groups(pages)
    pages_for = {}
    names = sorted({m[2] for ms in groups.values() if any(not x[3] for x in ms) for m in ms},
                   key=lambda n: -len(n))
    if names:
        ipat = re.compile(r"(?<![A-Za-zÀ-ɏ])(" + "|".join(re.escape(n) for n in names) +
                          r")(?![A-Za-zÀ-ɏ])", re.I)
        for path, _, body in bodies:
            for m in ipat.finditer(body):
                pages_for.setdefault(fold(m.group(1)), set()).add(path)
    idx = index_rows(groups, pages_for)
    os.makedirs(PUB, exist_ok=True)
    with open(os.path.join(PUB, "whoindex.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False)

    total = sum(len(v) for v in mentions.values())
    print(f"people scanned      : {len(people)}")
    print(f"index rows          : {len(idx)}  (people {sum(r[3]=='p' for r in idx)}, who {sum(r[3]=='w' for r in idx)}, ambiguous {sum(r[3]=='a' for r in idx)})")
    print(f"mentions found      : {total}")
    top = sorted(idx, key=lambda r: -r[2])[:8]
    for n, s, c, *_ in top:
        print(f"   {c:>3}  {n}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Find every mention of every published person across the whole site.

Two outputs:
  site/src/data/mentions.json   {slug: [{path, title, snippet}, ...]}
                                consumed at build time by /people/[slug]
  site/public/whoindex.json     [[name, slug, count], ...]
                                consumed at run time by wholink.js, which turns
                                a person's name in any page's prose into a link
                                to their page

This reads the BUILT html rather than the .astro sources, because the sources
are full of expressions and components and the rendered text is what a reader
actually sees. That makes the build two-pass:

    npm run build && python3 tools/build_mentions.py && npm run build

The first pass produces pages to scan; the second bakes the mentions in. Running
it on a site with no dist/ simply writes empty indexes, which is harmless.
"""
import json, os, re, html, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "site", "dist")
DATA = os.path.join(ROOT, "site", "src", "data")
PUB  = os.path.join(ROOT, "site", "public")

# Pages that are lists of everybody rather than writing about anybody. A name in
# a card grid is not a mention; counting them would make every person look
# equally well documented, which is the opposite of this archive's whole point.
SKIP_PREFIX = ("/people", "/families", "/places", "/register")

TAGS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def text_of(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
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

    if pattern:
        for root, _, files in os.walk(DIST):
            if "index.html" not in files:
                continue
            rel = os.path.relpath(root, DIST).replace(os.sep, "/")
            path = "/" if rel == "." else "/" + rel
            if any(path == p or path.startswith(p + "/") for p in SKIP_PREFIX):
                continue
            title, body = text_of(os.path.join(root, "index.html"))
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

    # only people who are actually written about anywhere go in the run-time
    # index, so wholink does not turn every name in a list into a link
    idx = [[people[s], s, len(v)] for s, v in mentions.items() if v]
    idx.sort(key=lambda r: -len(r[0]))
    os.makedirs(PUB, exist_ok=True)
    with open(os.path.join(PUB, "whoindex.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False)

    total = sum(len(v) for v in mentions.values())
    print(f"people scanned      : {len(people)}")
    print(f"people with mentions: {len(idx)}")
    print(f"mentions found      : {total}")
    top = sorted(idx, key=lambda r: -r[2])[:8]
    for n, s, c in top:
        print(f"   {c:>3}  {n}")


if __name__ == "__main__":
    main()

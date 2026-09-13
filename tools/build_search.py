#!/usr/bin/env python3
"""One flat index over everything this archive can point at.

The sibling archives fold diacritics so a reader typing "Gracisce" finds
"Gračišće". This family's problem is different and worse: the spelling of its
surnames moves about within English. A reader who knows their
great-grandmother as a SANIGER will not find SINNEGAR, and the archive's own
/berkeley page lists eleven forms of that one name. So every entry carries an
alias blob alongside its text, and a search for any form finds all of them.

Writes site/src/data/searchindex.json.
"""
import json, os, re, sys, unicodedata, html, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")
DIST = os.path.join(ROOT, "site", "dist")
# Written to public/, not src/data/: at ~300 KB this is fetched by the search
# page on demand rather than inlined into every build of the HTML.
OUT = os.path.join(ROOT, "site", "public", "searchindex.json")

# ── Spelling families. Type any member, find every member. ───────────────────
# Sources: /name (D'Arcy coined twice), /berkeley (eleven Saniger forms found in
# the Gloucestershire registers), and the Queensland death index, which spells
# the same woman Mulcahy, Mulchy and Mulchay in three registrations.
ALIASES = [
    ["d'arcy", "darcy", "d arcy", "darcey", "d'arcey", "darci", "dorchaidhe",
     "o dorchaidhe", "arcy"],
    ["sneyd", "snead", "sneed", "snayd", "sneid", "snyde"],
    ["saniger", "sainger", "sanigar", "sanigaer", "sinager", "sinneger",
     "sinnegar", "sinegar", "synegar", "synager", "singer",
     "sanigor", "sanigear", "sinagar", "sinigar", "sinnigar", "swanhanger"],
    ["mulcahy", "mulchy", "mulchay", "mulcahey", "mulcahy"],
    ["blum", "blume", "bloom"],
    ["murdoch", "murdock", "murdo"],
    ["atkinson", "atkinsone"],
    ["wakefield", "wakefeild"],
    ["keeling", "keelinge"],
    ["creech", "creagh"],
    ["atwell", "attwell"],
    ["lindesay", "lindsay", "lindsey"],
    ["seigfried", "seigfred", "siegfried"],
]
ALIAS = collections.defaultdict(set)
for grp in ALIASES:
    for w in grp:
        ALIAS[w] |= set(grp)


def fold(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("’", "'").replace("æ", "ae")


def expand(text):
    """Every alias of every word in the text, so any spelling finds the rest."""
    out = set()
    for w in re.findall(r"[a-z']+", fold(text).lower()):
        if w in ALIAS:
            out |= ALIAS[w]
    return " ".join(sorted(out))


rows = []
seen = set()


def add(kind, title, sub, href, extra=""):
    key = (kind, title, href)
    if key in seen:
        return
    seen.add(key)
    raw = " ".join(x for x in (title, sub, extra) if x)
    low = fold(raw).lower()
    rows.append({"k": kind, "t": title, "s": sub[:150], "h": href,
                 "q": (low + " " + expand(raw)).strip()})


def L(f):
    p = os.path.join(D, f)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def main():
    # ── people, from the built pages so living-person redaction is honoured ──
    reg = L("register.json") or {"groups": []}
    prov = L("provenance.json") or {}

    people = {}
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] != "tree":
                continue
            slug = r["link"].rsplit("/", 1)[-1]
            people[slug] = r
            pv = prov.get(slug, {})
            tags = []
            if pv.get("line"):
                tags.append("direct line ancestor")
            if pv.get("graft"):
                tags.append(f"above the {pv['graft']} graft")
            if pv.get("rel"):
                tags.append("relationship written in a record")
            add("Person", r["name"], r["says"], r["link"] + "/",
                g["surname"] + " " + " ".join(tags))

    # ── register entries that are NOT tree people: the non-kin this archive met
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "record":
                add("Register", r["name"], f'{r["says"]} — {r["source"]}',
                    "/register/?q=" + r["name"].replace(" ", "%20"), g["surname"])

    for pl in (L("places.json") or []):
        nm = pl.get("name") or pl.get("place") or ""
        if nm:
            add("Place", nm, pl.get("region") or pl.get("country") or "",
                "/places/", nm)

    for f in (L("families.json") or []):
        add("Family", f["surname"], f"{f.get('published', 0)} people published",
            "/families/", f["surname"])

    # ── every page of the site, from its own built HTML ─────────────────────
    if os.path.isdir(DIST):
        for dirpath, _, files in os.walk(DIST):
            if "index.html" not in files:
                continue
            rel = os.path.relpath(dirpath, DIST).replace(os.sep, "/")
            if rel == ".":
                rel = ""
            if rel.startswith(("people/", "who/")):
                continue                       # already indexed, one row each
            src = open(os.path.join(dirpath, "index.html"),
                       encoding="utf-8", errors="ignore").read()
            m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
            if not m:
                continue
            title = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
            dek = re.search(r'<meta name="description" content="([^"]*)"', src)
            body = html.unescape(re.sub(r"<[^>]+>", " ", src))
            body = re.sub(r"\s+", " ", body)[:4000]
            add("Page", title, html.unescape(dek.group(1)) if dek else "",
                "/" + rel + ("/" if rel else ""), body)

    rows.sort(key=lambda r: (r["k"], r["t"]))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    kinds = collections.Counter(r["k"] for r in rows)
    size = os.path.getsize(OUT) / 1024
    print(f"search index: {len(rows)} entries, {size:.0f} KB")
    for k, n in kinds.most_common():
        print(f"   {k:10s} {n}")


if __name__ == "__main__":
    main()

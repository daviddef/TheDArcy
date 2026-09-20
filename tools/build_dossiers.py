#!/usr/bin/env python3
"""A page for every person this archive can name — including the ones who are
not relatives.

/people is the tree. /register is the raw catch. Neither gives a page to the
constable who recovered a body in 1902, or to the six men who gave six
different accounts of one death at Pozières, or to the convicts who broke open
a major's crate of dinner ware in the South Atlantic. They are named in records
this archive has read, they are part of the evidence, and until now every one of
them dead-ended at an external link.

Writes site/src/data/dossiers.json: one entry per person named in a record but
absent from the family tree, with every register line that names them gathered
together.
"""
import json, os, re, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")
OUT = os.path.join(D, "dossiers.json")


def kebab(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "unnamed"


def main():
    reg = json.load(open(os.path.join(D, "register.json"), encoding="utf-8"))

    tree_names = set()
    tree_slug = {}
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "tree":
                tree_names.add(r["name"].lower())
                tree_slug.setdefault(r["name"].lower(), r["link"])

    people = collections.OrderedDict()
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] != "record":
                continue
            nm = r["name"]
            key = nm.lower()
            e = people.setdefault(key, {
                "name": nm, "surname": g["surname"], "rows": [],
                "inTree": key in tree_names,
                "treeLink": tree_slug.get(key, ""),
            })
            e["rows"].append({"says": r["says"], "source": r["source"], "link": r["link"]})

    # Records this archive has decided belong to NOBODY in the family tree,
    # even though the tree carries their name. tools/record-owners.json says so
    # explicitly, rule by rule.
    #
    # This exists because of Thomas Saniger, baptised Berkeley 3 July 1808, son
    # of John and brother of Hannah. Four register lines are his. He is not in
    # the tree, so /people/ has nothing for him — and the loop below used to
    # skip him anyway, because the tree carries two OTHER men of his name. He
    # fell between both mechanisms and had no page at all while his brother-in-
    # law and his sister both had one.
    orphaned = collections.defaultdict(list)
    op = os.path.join(ROOT, "tools", "record-owners.json")
    if os.path.exists(op):
        rules = json.load(open(op, encoding="utf-8"))
        for nm, rs in rules.items():
            if nm.startswith("_"):
                continue
            for rule in rs.get("rules", []):
                if rule.get("slug") is None:
                    orphaned[nm].append(rule["match"].lower())

    def is_orphan(key, says):
        return any(m in says.lower() for m in orphaned.get(key, []))

    # only people the tree does NOT carry need a page of their own; the rest
    # already have one, and duplicating them would split the same human in two
    out = {}
    used = set()
    for key, e in people.items():
        if e["inTree"]:
            orph = [r for r in e["rows"] if is_orphan(key, r["says"])]
            if not orph:
                continue
            e = dict(e, rows=orph, inTree=False, orphan=True, treeLink="")
        slug = kebab(e["name"])
        while slug in used:
            slug += "-2"
        used.add(slug)
        e["slug"] = slug
        e["n"] = len(e["rows"])
        out[slug] = e

    linked = sum(1 for e in people.values() if e["inTree"])
    data = {
        "people": out,
        "counts": {
            "named": len(people),
            "withTreePage": linked,
            "ownPage": len(out),
            "mentions": sum(len(e["rows"]) for e in people.values()),
        },
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    c = data["counts"]
    print(f"dossiers: {c['named']} people named in records · "
          f"{c['withTreePage']} already have a tree page · "
          f"{c['ownPage']} get one of their own · {c['mentions']} register lines")


if __name__ == "__main__":
    main()

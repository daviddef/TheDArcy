#!/usr/bin/env python3
"""The records this archive has read, delivered to the person they name.

THE FAULT THIS FIXES. register.json holds two kinds of row: `tree` rows, which
carry a /people/<slug> link, and `record` rows, which carry a name and what a
document says about it. build_dossiers.py reads both, and then does this:

    if e["inTree"]:
        continue            # "the rest already have one"

The assumption is that a person the family tree also carries already shows their
records on their own page. They do not. /people/[slug].astro never reads
register.json and never reads dossiers.json; it reads provenance.json, which is
built from a hand-kept list of RELATIONSHIP edges and knows nothing about record
rows. So 176 record lines naming 55 people in the tree reached /register/ and
/who/ and stopped there, and 30 of those people had pages saying

    "No relationship on this page has been checked against a record."

under a chip reading

    "Asserted by the family tree. No record has been found for them."

about people with six London Gazette commissions, two censuses and a burial
register between them. The data was right. The build dropped it, and no gate
refused. Found on 17 September 2026 after the Mazza archive had the same fault.

THE JOIN, AND ITS LIMIT. Record rows carry a NAME and no id, so a name is the
only join there is, and this family reuses forenames without mercy. Of the 55
names, 47 match exactly one person in the tree. Eight — William Sneyd, Thomas
Saniger, Catherine D'Arcy, Constantine D'Arcy, George Pitt D'Arcy, James Sneyd,
Mary Sneyd, Samuel Charles Sneyd — match between two and four. Those records are
attached to every candidate and marked `shared`, so the page can say plainly
that they are filed under the name and at least one belongs to somebody else.
THE ALTERNATIVE IS WORSE BOTH WAYS: dropping them is the bug, and picking one is
the merge this archive exists to refuse.

Writes site/src/data/person-records.json, keyed by slug.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")
OUT = os.path.join(D, "person-records.json")


def main():
    reg = json.load(open(os.path.join(D, "register.json"), encoding="utf-8"))

    tree = collections.defaultdict(list)   # lower name -> [slug, ...]
    recs = collections.defaultdict(list)   # lower name -> [record row, ...]
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "tree" and r["link"].startswith("/people/"):
                tree[r["name"].lower()].append(r["link"].rsplit("/", 1)[-1])
            elif r["kind"] == "record":
                recs[r["name"].lower()].append(r)

    out, shared_n = {}, 0
    for name, rows in recs.items():
        slugs = tree.get(name)
        if not slugs:
            continue                        # not in the tree: /who/ has them
        shared = len(slugs) > 1
        if shared:
            shared_n += 1
        for s in slugs:
            e = out.setdefault(s, {"name": rows[0]["name"], "shared": shared,
                                   "alsoNamed": [x for x in slugs if x != s],
                                   "rows": []})
            for r in rows:
                e["rows"].append({"says": r["says"],
                                  "source": r["source"].replace("record · ", ""),
                                  "link": r["link"]})

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    n_rows = sum(len(v["rows"]) for v in out.values())
    print(f"person records: {n_rows} record line(s) delivered to {len(out)} people in the tree "
          f"· {shared_n} name(s) carried by more than one person, marked shared")


if __name__ == "__main__":
    main()

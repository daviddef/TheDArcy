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

SETTLED, 20 SEPTEMBER 2026. Seven of the eight shared names now separate on a
date, through tools/record-owners.json, which names a distinguishing string from
each record's own text and the slug it belongs to. One — WILLIAM SNEYD — is
declared unsettled on purpose and keeps the old behaviour, because four men of
that name are in the tree and their baptism and burial ages contradict each
other. Choosing there would be inventing a man.

The rules also caught something the old behaviour hid: four of the eight THOMAS
SANIGER records belong to a third Thomas, baptised Berkeley 3 July 1808, who is
not in the family tree at all. Showing them on both tree Thomases had been
quietly offering a reader two men born ninety-seven years apart as candidates
for a life that belonged to neither.

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


def owners():
    p = os.path.join(ROOT, "tools", "record-owners.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def owner_of(rule_set, says):
    """The slug this record belongs to, or False if the rules do not decide.

    Returns None where a rule says the record belongs to no one in the tree —
    which is a decision, and must not be confused with «no rule matched»."""
    for r in rule_set.get("rules", []):
        if r["match"].lower() in says.lower():
            return r["slug"]
    if "default" in rule_set:
        return rule_set["default"]
    return False


def main():
    reg = json.load(open(os.path.join(D, "register.json"), encoding="utf-8"))
    OWN = owners()

    tree = collections.defaultdict(list)   # lower name -> [slug, ...]
    recs = collections.defaultdict(list)   # lower name -> [record row, ...]
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "tree" and r["link"].startswith("/people/"):
                tree[r["name"].lower()].append(r["link"].rsplit("/", 1)[-1])
            elif r["kind"] == "record":
                recs[r["name"].lower()].append(r)

    out, shared_n, settled_n, orphan_n = {}, 0, 0, 0
    for name, rows in recs.items():
        slugs = tree.get(name)
        if not slugs:
            continue                        # not in the tree: /who/ has them
        rule_set = OWN.get(name, {})
        ambiguous = len(slugs) > 1
        decided = ambiguous and not rule_set.get("unsettled") and rule_set

        def put(s, r, shared):
            e = out.setdefault(s, {"name": rows[0]["name"], "shared": shared,
                                   "alsoNamed": [x for x in slugs if x != s],
                                   "rows": []})
            if shared:
                e["shared"] = True
            e["rows"].append({"says": r["says"],
                              "source": r["source"].replace("record · ", ""),
                              "link": r["link"]})

        if not ambiguous:
            for r in rows:
                put(slugs[0], r, False)
            continue

        if not decided:
            shared_n += 1
            for s in slugs:
                for r in rows:
                    put(s, r, True)
            continue

        settled_n += 1
        for s2 in slugs:
            out.setdefault(s2, {"name": rows[0]["name"], "shared": False,
                                "alsoNamed": [x for x in slugs if x != s2],
                                "rows": []})["settled"] = True
        for r in rows:
            who = owner_of(rule_set, r["says"])
            if who is False:                # no rule reached it — stay shared
                for s in slugs:
                    put(s, r, True)
            elif who is None:               # belongs to nobody in the tree
                orphan_n += 1
            else:
                put(who, r, False)

    # A settled name gives every candidate an entry so the page can say the name
    # is shared — but a candidate who ended up with no records needs no section
    # at all, and printing "these records have been assigned to this one" above
    # nothing is worse than silence. Filter BEFORE writing, not after.
    out = {k: v for k, v in out.items() if v["rows"]}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    n_rows = sum(len(v["rows"]) for v in out.values())
    print(f"person records: {n_rows} record line(s) delivered to {len(out)} people in the tree "
          f"· {settled_n} shared name(s) settled by rule, {shared_n} left shared "
          f"· {orphan_n} line(s) belong to nobody in the tree")


if __name__ == "__main__":
    main()

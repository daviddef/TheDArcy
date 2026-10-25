#!/usr/bin/env python3
"""The lines figure's data: site/src/data/lines.json, made from this archive's own people data.

    python3 tools/build_lines.py            write site/src/data/lines.json
    python3 tools/build_lines.py --check    refuse (exit 1) if the committed file is not what the data builds
    python3 tools/build_lines.py --living-slugs   write the slugs of the living (JSON list) OUTSIDE the repository, for
                                                  check:lines --living (a living person's name is in their address)
    python3 tools/build_lines.py --living-path    print where that file is ($LINES_LIVING overrides it)

WHAT THIS IS. The kit's rivers figure (kit/components/BranchRivers.astro, contract kit/docs/lines.md) draws each line of
descent as a lane: a status that says how far its EVIDENCE reaches, dated places along it, and under the lanes the pens
that say who is not on any lane. This file is the one place this archive states those things. Two kinds of fact live here
and they are kept apart on purpose:

  1. LANES (the LANE table below) are written by hand, because a status is a research decision. Each one is taken from
     what an ARCHIVE PAGE says and the page is named beside it ("from": ...). Where the archive does not state a status
     there is no entry. A node's evidence word is the page's, never guessed from the tree.
  2. PEOPLE (members, pens, counts) are never typed. They are worked out here from ancestors.json, families.json,
     relatives.json, provenance.json, same-person.json and family-lines.json, with the slugs of tools/slugrule.py:
       - a person above one of the two grafts (provenance.json `graft`) is in the Hornby lane (a graft that is unevidenced)
         or in the Keele pen (a graft that was tested and disproved: a different stock of the name Sneyd);
       - otherwise a DEAD published person whose surname is a lane's surname is a member of that lane if the published
         tree joins them to it (the same union of parents, brothers and sisters, spouses and children that
         site/src/lib/familyLines.js `groupsFor` makes), and in the "not joined" pen if it does not;
       - everyone else stands in the pen of the other names.
     A LIVING PERSON IS NEVER LISTED: they are not members, not nodes, not counted in a pen (the pens count the dead).
     A declared copy (same-person.json) is not listed; its primary is.

The counts printed on the page come from the kit's ledger(lines) over this file.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slugrule as S  # noqa: E402

ROOT = S.ROOT
D = S.D
OUT = os.path.join(D, "lines.json")


def J(name):
    return json.load(open(os.path.join(D, name), encoding="utf-8"))


def living_path():
    if os.environ.get("LINES_LIVING"):
        return os.environ["LINES_LIVING"]
    return os.path.join(os.path.expanduser("~"), ".local", "state", "darcy-archive", "lines-living.json")


def key_of(s):
    """The surname key the archive uses everywhere (site/src/lib/familyLines.js surnameKey)."""
    s = re.sub(r"['\"’*]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", re.split(r"[,(\[]", s)[0]).strip()


# --------------------------------------------------------------------------------------------------------------------
# THE LANES. Every status below is read from a page of this archive; "from" says which page and what it says.
# Order is the drawing's order: the line this archive descends from first.
# --------------------------------------------------------------------------------------------------------------------
LANES = [
    {
        "key": "darcy", "colour": "var(--accent)", "surnames": ["darcy"],
        "label": "D'Arcy: Robert D'Arcy at Chatham to Brisbane",
        "href": "/direct-line/", "read": "The direct line, generation by generation →",
        "status": "origin-unknown", "span": [1776, None],
        "statusNote": "Robert's parentage not found; the Hornby descent above him is drawn apart",
        "from": "/hornby/ and /how-far-back/: nothing between his 1776 commission and his 1827 will better than the Portsea baptism of 1780; "
                "'no baptism for Robert exists in any indexed English collection'",
        "nodes": [
            ("Portsea", "1780", "Joseph D'Arcy baptised: father Robert, mother Jean. The first record of the family in England.", "joseph-d-arcy", "read"),
            ("Chatham", "1827", "Robert D'Arcy buried 19 May, entry 1571, aged 76.", "robert-d-arcy", "read"),
            ("Parramatta", "1829", "George Lindsay D'Arcy born, the Parramatta end of the crossing.", "george-lindsay-d-arcy", "read"),
            ("Brisbane", "1864", "George Pitt D'Arcy born at Brisbane.", "george-pitt-d-arcy-1864", "read"),
        ],
        "ends": [("Brisbane, Queensland", "/brisbane/", "where the line settles")],
        "anchor": "robert-d-arcy",
    },
    {
        "key": "hornby", "colour": "var(--r-plantagenet)", "surnames": [],
        "label": "Hornby: the descent the tree claims above Robert D'Arcy",
        "href": "/hornby/", "read": "The Hornby claim →",
        "status": "family-lore",
        "statusNote": "unevidenced: a legitimate descent from the 4th Earl is excluded by the peerage record",
        "from": "/how-far-back/ 'Graft one · unevidenced'; /hornby/ 'what cannot be shown'; the 1866 Notes and Queries item 'from family tradition'",
        "nodes": [
            ("Hornby Castle", "1570", "Conyers (of Hornby Castle) D'Arcy: the tree's earliest on this line.", "conyers-of-hornby-castle-d-arcy", "tree"),
            ("St James's Palace", "1681", "Thomas (Francis) D'Arcy, said to be born here: the one link above Robert, with no record.", "thomas-francis-d-arcy", "disputed"),
        ],
        "ends": [("Robert D'Arcy, Chatham?", "/hornby/", "the join the tree makes and no record supports")],
        "graft": "Hornby",
    },
    {
        "key": "saniger", "colour": "var(--r-modern)", "surnames": ["saniger", "sanigar", "sanyger", "sanigor"],
        "label": "Saniger: Berkeley, Gloucestershire",
        "href": "/saniger-line/", "read": "Six generations at Berkeley →",
        "status": "origin-unknown", "span": [1679, 1804],
        "statusNote": "origin not found: the deepest William is a name in a register",
        "from": "/saniger-line/: 'every one of those generations is now on a parish record'; 'The deepest Saniger this archive can reach. He is a name in a register and nothing else.'",
        "nodes": [
            ("Berkeley", "1679", "William Saniger baptised 12 October, father William.", "william-saniger", "read"),
            ("Berkeley", "1744", "Thomas Saniger baptised 23 August, father Thomas.", "thomas-saniger-1744", "read"),
            ("Berkeley", "1769", "Thomas marries Catherine Cotton on 10 April; John is christened five weeks later.", "john-saniger", "read"),
            ("Berkeley", "1804", "Hannah baptised as SANIGOR, 18 August: the last link, found under another spelling.", "hannah-saniger", "read"),
        ],
        "ends": [("Bristol, the Wakefield lane", "/wakefields/", "Hannah marries James Wakefield, 17 October 1831")],
    },
    {
        "key": "wakefield", "colour": "var(--terra)", "surnames": ["wakefield"],
        "label": "Wakefield: Stroud, Bristol, Brisbane",
        "href": "/wakefields/", "read": "The Wakefields →",
        "status": "documented", "span": [1806, 1857],
        "statusNote": "James's baptism names his parents",
        "from": "/wakefields/: 'A life in six records': baptised 6 April 1806 at Stroud, father Richard Wakefield, mother Elizabeth Webb; 1841 and 1851 censuses; 1854 passage; died 1857",
        "nodes": [
            ("Stroud", "1806", "James Wakefield baptised 6 April: father Richard, mother Elizabeth Webb.", "james-wakefield", "read"),
            ("Bristol", "1841", "Drivers Fields, St Paul: James, a mason journeyman, with Hannah and three children.", None, "read", "/drivers-fields/"),
            ("Brisbane", "1854", "Miriam Wakefield, fourteen, lands on the General Hewitt with her father and mother and five brothers and sisters; James dies in 1857.", "miriam-wakefield", "read"),
        ],
        "ends": [("The Sneyd lane, Brisbane", "/sneyds/", "Miriam Wakefield marries William Hartley Sneyd, 1859")],
    },
    {
        "key": "sneyd", "colour": "var(--ochre)", "surnames": ["sneyd", "snead"],
        "label": "Sneyd: Madeley and Hanley to Brisbane",
        "href": "/sneyds/", "read": "The Sneyds of the Potteries →",
        "status": "inferred", "span": [1811, 1885],
        "statusNote": "origin inferred: the 1781 Madeley baptism is the best candidate, not proved",
        "from": "/sneyds/: the weaver's family at Madeley 'is offered as a reading rather than a reconstruction'; the 1781 Samuel 'remains the best candidate'; "
                "/how-far-back/: the Hanley christening of 1811 and Samuel Charles's service and death are documented",
        "nodes": [
            ("Madeley", "1781", "Samuel Sneyd baptised 4 June, father William: the best candidate for the Hanley grocer, not proved.", "samuel-sneyd", "inferred"),
            ("Hanley", "1811", "Samuel Charles Sneyd christened 28 April, son of Samuel.", "samuel-charles-sneyd-1810", "read"),
            ("New South Wales", "1832", "Samuel Charles Sneyd sails with the 4th (King's Own) Regiment.", None, "read", "/sergeant-sneyd/"),
            ("Brisbane", "1885", "Samuel Charles Sneyd dies at Enoggera, 4 July; Governor of Brisbane Gaol from 1859.", None, "read", "/sergeant-sneyd/"),
        ],
        "ends": [("Boulia, Queensland", "/sneyd/", "Ivy Miriam Sneyd's people")],
    },
    {
        "key": "atkinson", "colour": "var(--r-stuart)", "surnames": ["atkinson"],
        "label": "Atkinson: Limerick to Wickham Terrace",
        "href": "/atkinson/", "read": "The Atkinsons →",
        "status": "inferred", "span": [1832, 1906],
        "statusNote": "five generations above rest on the tree alone",
        "from": "/atkinson/: the 1832 Limerick christening 'is the record that names Richard and Anne'; 'the tree carries five generations above Paul Cole Atkinson, all of them in Limerick'",
        "nodes": [
            ("Limerick", "1725", "Richard Atkinson: the tree's earliest on this line; no record read.", "richard-atkinson-1725", "tree"),
            ("Limerick", "1832", "Paul Cole Atkinson christened 9 July, St Mary's Cathedral: the record that names Richard and Anne.", "paul-cole-atkinson", "read"),
            ("Brisbane", "1864", "Paul Cole Atkinson installs the first organ at All Saints' Wickham Terrace, on 3 August.", None, "read", "/atkinson/"),
        ],
        "ends": [("Brisbane, Queensland", "/atkinson/", "Ida Kathleen Atkinson marries George Pitt D'Arcy, 1888")],
    },
    {
        "key": "murdoch", "colour": "var(--r-medieval)", "surnames": ["murdoch"],
        "label": "Murdoch: St Quivox, Ayrshire, to Toowoomba",
        "href": "/murdoch/", "read": "The Murdochs →",
        "status": "documented", "span": [1854, None],
        "statusNote": "Scottish statutory register names the parents of William",
        "from": "/murdoch/: William's birth 'is how this line is documented rather than asserted'; Francis and Marion married at Avondale on 6 May 1854",
        "nodes": [
            ("Avondale", "1854", "Francis Murdoch marries Marion Watt on 6 May: 1854, not the 1853 the tree carries.", "francis-murdoch-1824", "read"),
            ("St Quivox", "1856", "William Murdoch born 7 October; the statutory register names Francis Murdoch and Marion Watt.", "william-murdoch", "read"),
            ("Gympie", "1894", "William James Fraser Murdoch born at Gympie, Queensland: the generation that emigrated has arrived.", "william-james-fraser-bill-murdoch", "tree"),
        ],
        "ends": [("Toowoomba, Queensland", "/murdoch/", "Audrey \"Dell\" Murdoch marries Kenneth Lindsay D'Arcy, 1952")],
    },
]

# A candidate join, drawn dotted and faint: told, not read.
BRIDGES = [
    {"from": "hornby", "to": "darcy", "conf": "lore", "label": "the tree joins these at Robert D'Arcy; no record does", "href": "/hornby/"},
]

KEELE_PEN = {
    "id": "keele", "kind": "different-stock",
    "head": "A different stock of the name Sneyd: the Keele descent",
    "note": "The tree hangs these people on a William Sneyd baptised at Madeley in 1742. The register names a different father. "
            "Tested and disproved; kept on the site, because a disproved claim published is worth more than a disproved claim deleted.",
    "item": ("The Sneyds of Keele Hall", "/how-far-back/", "behind a single link, found wrong"),
}

OTHER_HEAD = "Families the archive follows and has not yet drawn as a line"
UNJOINED_HEAD = "People of these lines' names whom the published tree does not join to them"


def load():
    base, rel = S.records()
    slug = S.assign(base, rel)
    people = {}
    for r in base + rel:
        people[r["id"]] = r
    prov = J("provenance.json")
    same = J("same-person.json")
    copies = {p["copy"] for p in same.get("pairs", [])}
    clusters = {m["id"]: f["surname"] for f in J("families.json") for m in f["members"]}
    fam_lines = J("family-lines.json")
    return people, slug, prov, copies, clusters, fam_lines


def related(p):
    """Every id the archive names beside a person: parents, brothers and sisters, spouses, children."""
    out = set()
    for r in p.get("parents") or []:
        out.add(r.get("id"))
    for r in p.get("siblings") or []:
        out.add(r.get("id"))
    for s in p.get("spouses") or []:
        out.add(s.get("id"))
        out.update(s.get("children") or [])
    out.discard(None)
    return out


def groups_for(ids, people, skip=frozenset()):
    """site/src/lib/familyLines.js groupsFor, in Python: union members through the people the archive names beside
    them (parent, brother or sister, spouse, child), and members who share any such person. `skip` are people a join
    may not pass through: the people above a graft, since the graft is exactly the link that is in question."""
    ids = set(ids)
    root = {i: i for i in ids}

    def find(x):
        while root[x] != x:
            root[x] = root[root[x]]
            x = root[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            root[ra] = rb

    via = {}

    def touch(m, other):
        if not other or other in skip:
            return
        if other in ids:
            union(m, other)
        else:
            via.setdefault(other, []).append(m)

    for m in ids:
        p = people[m]
        for r in p.get("parents") or []:
            touch(m, r.get("id"))
        for r in p.get("siblings") or []:
            touch(m, r.get("id"))
        for s in p.get("spouses") or []:
            touch(m, s.get("id"))
            for c in s.get("children") or []:
                touch(m, c)
    for lst in via.values():
        for i in range(1, len(lst)):
            union(lst[0], lst[i])
    out = {}
    for m in ids:
        out.setdefault(find(m), []).append(m)
    return list(out.values())


def build():
    people, slug, prov, copies, clusters, fam_lines = load()
    by_slug = {s: i for i, s in slug.items()}
    dead = {i for i, r in people.items() if not r.get("living") and i not in copies}

    def born_year(i):
        m = re.search(r"\d{4}", people[i].get("born") or people[i].get("died") or "")
        return int(m.group(0)) if m else 9999

    def order(ids):
        return sorted(ids, key=lambda i: (born_year(i), slug[i]))

    assigned = {}          # id -> ("lane", key) | ("keele",) | ("unjoined",) | ("other",)
    node_persons = {}      # lane key -> set of ids named by its nodes

    # 1. the grafts first
    for i in dead:
        g = (prov.get(slug[i]) or {}).get("graft")
        if g == "Keele":
            assigned[i] = ("keele",)
        elif g == "Hornby":
            assigned[i] = ("lane", "hornby")

    # 2. the nodes' people belong to their lane, whatever their surname (a node is a stated fact about a lane)
    for ln in LANES:
        ids = set()
        for n in ln["nodes"]:
            s = n[3]
            if s is None:
                continue
            if s not in by_slug:
                raise SystemExit(f"build_lines: lane {ln['key']}: node person {s!r} has no page")
            i = by_slug[s]
            if i not in dead:
                raise SystemExit(f"build_lines: lane {ln['key']}: node person {s!r} is living or a declared copy")
            if i in assigned and assigned[i] != ("lane", ln["key"]):
                raise SystemExit(f"build_lines: {s!r} is a node of {ln['key']} and already placed at {assigned[i]}")
            assigned[i] = ("lane", ln["key"])
            ids.add(i)
        node_persons[ln["key"]] = ids

    graft_ids = {i for i in people if (prov.get(slug[i]) or {}).get("graft") in ("Hornby", "Keele")}
    graft_of = {i: (prov.get(slug[i]) or {}).get("graft") for i in graft_ids}

    # 3. surname lanes: the joined group is the lane, the rest of the name is the "not joined" pen
    unjoined = []
    for ln in LANES:
        keys = set(ln["surnames"])
        if not keys:
            continue
        # every published person of the name, living ones too, as the archive's own groups use them
        everyone = [i for i, r in people.items() if key_of(r.get("surname")) in keys and i not in copies]
        # a graft person is not a member of the name's group: they are above the join
        everyone = [i for i in everyone if (prov.get(slug[i]) or {}).get("graft") not in ("Hornby", "Keele")]
        groups = groups_for(everyone, people, skip=graft_ids)
        anchors = {by_slug[s] for s in [n[3] for n in ln["nodes"]] if s} | ({by_slug[ln["anchor"]]} if ln.get("anchor") else set())
        main = None
        for g in groups:
            if set(g) & anchors:
                main = set(g) if main is None else main | set(g)
        if main is None:
            main = set(max(groups, key=len)) if groups else set()
        for g in groups:
            for i in g:
                if i not in dead or i in assigned:
                    continue
                if i in main:
                    assigned[i] = ("lane", ln["key"])
                    continue
                # not joined to the lane except through a graft: they sit beside the people above it
                touching = {graft_of[x] for m in g for x in related(people[m]) if x in graft_of}
                if "Hornby" in touching:
                    assigned[i] = ("lane", "hornby")
                elif "Keele" in touching:
                    assigned[i] = ("keele",)
                else:
                    assigned[i] = ("unjoined",)
                    unjoined.append(i)

    # 4. everyone else: the other names
    other = [i for i in dead if i not in assigned]
    for i in other:
        assigned[i] = ("other",)

    # ---- the lanes
    lanes_out = []
    for ln in LANES:
        members = order([i for i in dead if assigned.get(i) == ("lane", ln["key"])
                         and i not in node_persons[ln["key"]]])
        lane = {"key": ln["key"], "colour": ln["colour"], "label": ln["label"], "href": ln["href"], "read": ln["read"],
                "status": ln["status"]}
        if ln["status"] != "family-lore" and ln.get("span"):
            lane["span"] = ln["span"]
        if ln.get("statusNote"):
            lane["statusNote"] = ln["statusNote"]
        lane["nodes"] = []
        for n in ln["nodes"]:
            o = {"place": n[0], "year": n[1], "why": n[2]}
            if n[3]:
                o["person"] = n[3]
            if len(n) > 5 and n[5]:
                o["href"] = n[5]
            o["evidence"] = n[4]
            lane["nodes"].append(o)
        lane["ends"] = [list(e) for e in ln["ends"]]
        lane["members"] = [slug[i] for i in members]
        lanes_out.append(lane)

    # ---- the pens
    pens = []
    keele_ids = order([i for i in dead if assigned[i] == ("keele",)])
    if keele_ids:
        k = dict(KEELE_PEN)
        item = k.pop("item")
        pens.append({"id": k["id"], "kind": k["kind"], "head": k["head"], "note": k["note"],
                     "items": [list(item)], "members": [slug[i] for i in keele_ids]})
    unj = order(unjoined)
    if unj:
        pens.append({"id": "not-joined", "kind": "not-yet-placed", "head": UNJOINED_HEAD,
                     "note": "These carry the surname of a lane above and are published, but no parent, brother or sister, spouse or child "
                             "named in the archive ties them to that lane. They are listed, not joined: a surname is not a family.",
                     "items": [], "members": [slug[i] for i in unj]})
    # the other names: families with a page of their own first, then everyone else
    fam_pages = []   # (label, href, ids)
    cluster_slug = {}
    for i, name in clusters.items():
        cluster_slug.setdefault(name, S.kebab(name))
    lane_names = {"D'Arcy", "Sneyd", "Atkinson", "Murdoch", "Wakefield"}
    by_cluster = {}
    for i in other:
        c = clusters.get(i)
        if c and c not in lane_names:
            by_cluster.setdefault(c, []).append(i)
    taken = set()
    for name, ids in sorted(by_cluster.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        fam_pages.append((name, f"/families/{S.kebab(name)}/", ids))
        taken |= set(ids)
    # the names the direct line carries (family-lines.json), each by its keys
    fl_keys = {}
    for l in fam_lines["lines"]:
        fl_keys[l["slug"]] = (l["surname"], set(l["keys"]), l.get("alsoWhenNameHas") or {})
    for sl, (name, keys, also) in fl_keys.items():
        ids = []
        for i in other:
            if i in taken:
                continue
            r = people[i]
            k = key_of(r.get("surname"))
            if k in keys or (k in also and also[k] in str(r.get("name", "")).lower()):
                ids.append(i)
        if ids:
            fam_pages.append((name, f"/families/{sl}/", ids))
            taken |= set(ids)
    rest = [i for i in other if i not in taken]
    items = [[f"{n} ({len(ids)})", h, f"{len(ids)} people published under the name"] for n, h, ids in fam_pages]
    if rest:
        items.append([f"All other names ({len(rest)})", "/people/", "relatives named beside the line, and ancestors whose name has no page of its own"])
    n_other = len(other)
    if items:
        pens.append({"id": "other-names", "kind": "not-yet-placed", "head": OTHER_HEAD,
                     "note": "Each of these is a name the direct line carries or a marriage brings in, and most have a page of their own. None is drawn as a lane "
                             "because the archive has not stated, for it, how far its evidence reaches. The people are counted, not listed.",
                     "items": items, "count": n_other})

    out = {
        "title": "The lines of descent this archive follows, and how far the evidence for each reaches",
        "caption": "Each lane is one line, with a status that says how far its evidence reaches. Hover or tab any dot to see what it rests on. A dot drawn hollow "
                   "and dashed is not read from a record.",
        "unplacedAfter": "murdoch",
        "lanes": lanes_out,
        "pens": pens,
        "bridges": BRIDGES,
    }
    # a ledger of where every dead published person stands, for the page and the reader (counted, never typed)
    counts = {"dead": len(dead), "lane": sum(len(l["members"]) + len({n["person"] for n in l["nodes"] if n.get("person")}) for l in lanes_out),
              "keele": len(keele_ids), "notJoined": len(unj), "other": n_other}
    assert counts["lane"] + counts["keele"] + counts["notJoined"] + counts["other"] == counts["dead"], counts
    return out, counts, slug, people


def living_slugs():
    people, slug, *_ = load()
    return sorted(slug[i] for i, r in people.items() if r.get("living"))


def main(argv):
    if "--living-path" in argv:
        print(living_path())
        return 0
    if "--living-slugs" in argv:
        fp = living_path()
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        ls = living_slugs()
        if not ls:
            raise SystemExit("build_lines: no living person found; a list of none would make the living gate a verdict on nothing")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(ls, f)
        os.chmod(fp, 0o600)
        print("  lines living list: %d slug(s), kept outside the repository" % len(ls))
        return 0
    out, counts, _slug, _people = build()
    text = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        have = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if have != text:
            print("  FAIL  lines-data  site/src/data/lines.json is not what the data builds; run python3 tools/build_lines.py and commit the result")
            return 1
        print("  ok    lines-data  lines.json is what the data builds (%d lanes; %d dead people placed: %d on lanes, %d in the Keele pen, %d not joined, %d under other names)"
              % (len(out["lanes"]), counts["dead"], counts["lane"], counts["keele"], counts["notJoined"], counts["other"]))
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("lines.json  %d lanes, %d pens; %s" % (len(out["lanes"]), len(out["pens"]), json.dumps(counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

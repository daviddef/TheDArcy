#!/usr/bin/env python3
"""Who belongs to a family LINE, worked out in Python from the committed data.

site/src/lib/familyLines.js decides this for the pages. This is the same rule written a
second time, on purpose, for the two tools that must not take the page's word for it:
tools/check_family_lines.py (the gate) and tools/audit_family_lines.py (the audit that
chose the lines). A gate that reads its answer from the thing it gates cannot fail.

THE RULE (also stated in site/src/data/family-lines.json):
  - the people are the ones the archive already PUBLISHES: the numbered ancestors
    (ancestors.json), the thirteen clusters (families.json) and the relatives named
    beside them (relatives.json);
  - a person belongs to a line when their SURNAME FIELD, lowercased, with apostrophes
    and quotation marks removed and cut at the first comma, bracket or parenthesis,
    equals one of the line's keys (or the line's `alsoWhenNameHas` says their title
    stands in for the surname and their own name contains the word);
  - a person in one of the thirteen clusters is never in a line;
  - a declared copy (same-person.json) is never listed.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, "site", "src", "data")
sys.path.insert(0, HERE)


def _j(name, default=None):
    p = os.path.join(D, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def surname_key(s):
    s = str(s or "").lower()
    s = re.sub(r"['\"’*]", "", s)
    s = re.split(r"[,(\[]", s)[0]
    return re.sub(r"\s+", " ", s).strip()


def published(data_dir=None):
    """{id: record} for everybody the archive publishes, plus the set of ids in the thirteen."""
    global D
    if data_dir:
        D = data_dir
    by, in_cluster = {}, set()
    for r in _j("ancestors.json", []):
        by.setdefault(r["id"], {}).update(r)
    for f in _j("families.json", []):
        for m in f["members"]:
            keep = {k: by[m["id"]][k] for k in ("ahn", "gen") if by.get(m["id"], {}).get(k)}
            by.setdefault(m["id"], {}).update(m)
            by[m["id"]].update(keep)
            in_cluster.add(m["id"])
    for r in _j("relatives.json", []):
        by.setdefault(r["id"], {}).update(r)
    return by, in_cluster


def copies():
    return {x["copy"] for x in (_j("same-person.json", {}) or {}).get("pairs", [])}


def config():
    return _j("family-lines.json", {"lines": []})


def line_of(rec, lines):
    k = surname_key(rec.get("surname"))
    for l in lines:
        if k in l["keys"]:
            return l
    for l in lines:
        w = (l.get("alsoWhenNameHas") or {}).get(k)
        if w and w in str(rec.get("name", "")).lower():
            return l
    return None


def members(data_dir=None):
    """{slug: [records]} for every line in the config; declared copies and cluster members out."""
    by, in_cluster = published(data_dir)
    cp = copies()
    cfg = config()
    out = {l["slug"]: [] for l in cfg["lines"]}
    for pid, r in by.items():
        if pid in in_cluster or pid in cp:
            continue
        l = line_of(r, cfg["lines"])
        if l:
            out[l["slug"]].append(r)
    return out


def slugs():
    import slugrule
    return slugrule.slugs()


# ── the thirteen clusters and the people on no surname page (18 October 2026) ─────────────────────
# A second writing of site/src/lib/familyLines.js: clusterMembers(), groupsFor() and unplacedData().
# tools/check_cluster_groups.py reads the built pages against these.

def cluster_people(data_dir=None):
    """{surname: [records]} for each of the thirteen: its own members, then the people the archive already
    publishes whose surname is the same name written another way (`alsoWritten`). Declared copies out."""
    by, _ = published(data_dir)
    cp = copies()
    out = {}
    for f in _j("families.json", []):
        recs = [m for m in f["members"] if m["id"] not in cp]
        recs += [by[i] for i in f.get("alsoWritten", []) if i in by and i not in cp]
        out[f["surname"]] = recs
    return out


def group_sizes(members):
    """The sizes, largest first, of the groups the published people do not join: union over parents,
    brothers and sisters, spouses and a spouse's children, and over any outside person two members touch."""
    ids = {m["id"] for m in members}
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

    def touch(m, i):
        if not i:
            return
        if i in ids:
            union(m["id"], i)
        else:
            via.setdefault(i, []).append(m["id"])

    for m in members:
        for r in m.get("parents") or []:
            touch(m, r.get("id"))
        for r in m.get("siblings") or []:
            touch(m, r.get("id"))
        for s in m.get("spouses") or []:
            touch(m, s.get("id"))
            for c in s.get("children") or []:
                touch(m, c)
    for lst in via.values():
        for i in range(1, len(lst)):
            union(lst[0], lst[i])
    sizes = {}
    for i in ids:
        sizes[find(i)] = sizes.get(find(i), 0) + 1
    return sorted(sizes.values(), reverse=True)


def unplaced(data_dir=None):
    """Where every published person is counted: a cluster, a line, a declared copy, the Falco side, a page
    elsewhere (Saniger), no surname, or another surname with no page."""
    by, in_cluster = published(data_dir)
    cp = copies()
    cfg = config()
    also = {i for f in _j("families.json", []) for i in f.get("alsoWritten", [])}
    falco = set((cfg.get("otherArchive") or {}).get("keys", []))
    elsewhere = {k for k, v in (cfg.get("pagesElsewhere") or {}).items() if isinstance(v, dict) and v.get("href")}
    out = dict(total=len(by), cluster=0, line=0, copies=0, falco=0, elsewhere=0, unnamed=0, other=0)
    names = set()
    for pid, r in by.items():
        if pid in cp:
            out["copies"] += 1
        elif pid in in_cluster or pid in also:
            out["cluster"] += 1
        elif line_of(r, cfg["lines"]):
            out["line"] += 1
        else:
            k = surname_key(r.get("surname"))
            if k in falco:
                out["falco"] += 1
            elif k in elsewhere:
                out["elsewhere"] += 1
            elif not k or k == "unnamed":
                out["unnamed"] += 1
            else:
                out["other"] += 1
                names.add(k)
    out["surnames"] = len(names)
    return out

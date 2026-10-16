#!/usr/bin/env python3
"""The address of every person page, worked out the way site/src/lib/people.js
works it out, for the Python tools that must link to those pages.

ONE PLACE, SO THE LINKS RESOLVE. build_register.py, build_family_pages.py and
build_search.py each need to know where a person's page is, and each used to
carry its own copy of the rule. The rule has three phases (see people.js):

  1. the DEAD of the direct line and the thirteen surnames, among themselves:
     a name carried twice is told apart by a year;
  2. the dead who are only RELATIVES (relatives.json): the bare name, and if it
     is taken the name and a year, so a newcomer never moves an older page;
  3. the LIVING, from what is left: the bare name, then name-living, then a number.

tools/check_living_standard.py keeps a copy of its own on purpose: the gate must
not read its answer from the thing it gates.
"""
import json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")


def kebab(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _year(r):
    m = re.search(r"\d{4}", (r.get("born") or r.get("died") or ""))
    return m.group(0) if m else ""


def _json(name):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8"))


def records():
    """(base, relatives): every person with a page, in people.js's insertion order.
    base is the direct line then the family clusters, merged by id; relatives
    follow, and are never in base."""
    by_id = {}
    for r in _json("ancestors.json"):
        by_id.setdefault(r["id"], {}).update(r)
    for f in _json("families.json"):
        for r in f["members"]:
            by_id.setdefault(r["id"], {}).update(r)
    base = list(by_id.values())
    rel = [dict(r) for r in _json("relatives.json") if r["id"] not in by_id]
    return base, rel


def assign(base, rel):
    """{id: slug} for everybody, by the three phases."""
    used, out = set(), {}
    dead = [r for r in base if not r.get("living")]
    counts = {}
    for r in dead:
        counts[kebab(r["name"])] = counts.get(kebab(r["name"]), 0) + 1
    for r in dead:
        b = kebab(r["name"]) or "unnamed"
        s = b
        if counts[b] > 1:
            y = _year(r)
            s = f"{b}-{y}" if y else b
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    for r in (x for x in rel if not x.get("living")):
        b = kebab(r["name"]) or "unnamed"
        s = b
        if s in used:
            y = _year(r)
            if y:
                s = f"{b}-{y}"
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    for r in (x for x in base + rel if x.get("living")):
        b = kebab(r["name"]) or "unnamed"
        s = b
        if s in used:
            s = f"{b}-living"
        while s in used:
            s += "-2"
        used.add(s)
        out[r["id"]] = s
    return out


def slugs():
    base, rel = records()
    return assign(base, rel)


if __name__ == "__main__":
    sl = slugs()
    print(len(sl), "pages")

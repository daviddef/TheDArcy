#!/usr/bin/env python3
"""Households, marriages and burials, pulled out of the published people.

Three views the archive has never had, all of them latent in data it already
carries and none of them visible anywhere:

  households  — a couple and the children under one roof, which is the unit a
                census or a parish register actually records
  marriages   — every marriage with a date, in order, which is the only series
                on this site that shows the family moving across the map
  graves      — every burial place recorded, and the ones worth doubting

A living person is a name, a relationship, a town and a country and nothing more
(David's ruling, 16 October 2026). So a living spouse and a living child are
NAMED in a household, and a marriage with a living partner has no row in the
marriages list, because a marriage is a date about both of the people in it.
Households are built from the dead, so a household of two living people is not
drawn. Graves are the dead. Writes households.json, marriages.json and
graves.json.
"""
import json, os, re, collections, unicodedata
import slugrule

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")


def kebab(s):
    """Must match site/src/lib/people.js exactly, including the Unicode step —
    without it Schönburg slugs as "sch-nburg" and every link to that person is
    dead, which is how this shipped the first time."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def load_people(living=False):
    """The people with a page, in site/src/lib/people.js's own terms and in its
    own order (numbered ancestors first, then the family clusters, then the
    relatives named beside them). By default the dead only; living=True is the
    living only, whose slugs people.js assigns after the dead's."""
    by_id = {}
    for r in json.load(open(os.path.join(D, "ancestors.json"), encoding="utf-8")):
        if bool(r.get("living")) == living:
            by_id.setdefault(r["id"], {}).update(r)
    for f in json.load(open(os.path.join(D, "families.json"), encoding="utf-8")):
        for r in f["members"]:
            if bool(r.get("living")) == living:
                by_id.setdefault(r["id"], {}).update(r)
    rp = os.path.join(D, "relatives.json")
    if os.path.exists(rp):
        for r in json.load(open(rp, encoding="utf-8")):
            if bool(r.get("living")) == living:
                by_id.setdefault(r["id"], {}).update(r)
    return by_id


MONTH = {m: i for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def sortable(datestr):
    """GEDCOM dates sort badly as strings. Year first, then month, then day."""
    s = (datestr or "").upper()
    y = re.search(r"\b(\d{4})\b", s)
    if not y:
        return (9999, 99, 99)
    mo = next((MONTH[m] for m in MONTH if m in s), 99)
    d = re.match(r"^(?:ABT |BEF |AFT |)(\d{1,2}) ", s)
    return (int(y.group(1)), mo, int(d.group(1)) if d else 99)


def main():
    people = load_people()
    alive = load_people(living=True)
    # Every address is people.js's, worked out in one place (tools/slugrule.py).
    slug = slugrule.slugs()
    everyone = {**people, **alive}

    name = lambda i: everyone[i]["name"] if i in everyone else ""

    # ── households ─────────────────────────────────────────────────────────
    households, marriages = [], []
    seen = set()
    for r in people.values():
        for sp in (r.get("spouses") or []):
            if not sp.get("name"):
                continue
            pair = tuple(sorted([r["id"], sp.get("id") or sp["name"]]))
            kids = [k for k in (sp.get("children") or []) if k in everyone]

            # A marriage is a date about both of its people: no row when either
            # is living. (build_site_data blanks the date too.)
            if sp.get("married") and not sp.get("living"):
                marriages.append({
                    "date": sp["married"], "sort": sortable(sp["married"]),
                    "place": sp.get("marriedPlace") or "",
                    "a": r["name"], "aSlug": slug.get(r["id"], ""),
                    "b": sp["name"], "bSlug": slug.get(sp.get("id"), ""),
                    "kids": len(kids),
                    "divorced": sp.get("divorced") or "",
                })

            if pair in seen or not (kids or sp.get("married")):
                continue
            seen.add(pair)
            households.append({
                "a": r["name"], "aSlug": slug.get(r["id"], ""),
                "b": sp["name"], "bSlug": slug.get(sp.get("id"), ""),
                "married": sp.get("married") or "", "place": sp.get("marriedPlace") or "",
                "sort": sortable(sp.get("married") or r.get("born")),
                "kids": [{"name": name(k), "slug": slug.get(k, ""),
                          "life": everyone[k].get("life") or ""} for k in kids],
            })

    households.sort(key=lambda h: h["sort"])
    marriages.sort(key=lambda m: m["sort"])
    # one marriage is recorded on both partners; keep the first of each pair
    dedup, seenm = [], set()
    for m in marriages:
        k = (m["sort"], tuple(sorted([m["a"], m["b"]])))
        if k in seenm:
            continue
        seenm.add(k)
        dedup.append(m)
    marriages = dedup

    # ── graves ─────────────────────────────────────────────────────────────
    graves = collections.defaultdict(list)
    for r in people.values():
        b = (r.get("burial") or "").strip()
        if not b:
            continue
        graves[b].append({"name": r["name"], "slug": slug.get(r["id"], ""),
                          "life": r.get("life") or "", "died": r.get("died") or ""})

    # a plot reference shared by two people is either quietly true or a
    # copy-and-paste error, and the archive cannot tell which without the register
    shared = {k: v for k, v in graves.items() if len(v) > 1 and re.search(r"\bplot\b|grave \d|section", k, re.I)}

    gl = sorted(([{"place": k, "people": sorted(v, key=lambda p: p["name"]),
                   "n": len(v), "shared": k in shared}
                  for k, v in graves.items()]), key=lambda g: (-g["n"], g["place"]))

    for fn, obj in (("households", {"rows": households, "n": len(households)}),
                    ("marriages", {"rows": marriages, "n": len(marriages)}),
                    ("graves", {"rows": gl, "n": len(gl),
                                "buried": sum(g["n"] for g in gl),
                                "sharedPlots": len(shared)})):
        json.dump(obj, open(os.path.join(D, fn + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0)

    print(f"households {len(households)} · marriages {len(marriages)} · "
          f"burial places {len(gl)} covering {sum(g['n'] for g in gl)} people "
          f"({len(shared)} plot references shared by more than one person)")


if __name__ == "__main__":
    main()

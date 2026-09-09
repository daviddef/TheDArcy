#!/usr/bin/env python3
"""Turn the parsed GEDCOM into the JSON the site reads.

The living-person rule is applied here, once, at the boundary between the
research data and the published build. Anything that reaches site/src/data is
publishable; anything filtered out here never enters the build at all.
"""
import json, os, collections, re
from gedcom import (load, display, born, died, year, ev, lifespan, classify_living)

# Filled in by main(). One graph-wide judgement, used everywhere below, so that
# a person cannot be living on one page and dead on another.
LIVING = {}


def is_living(p):
    return LIVING.get(p["id"], True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "src", "data")
CRISTINA = "@I2@"

# Surnames the archive treats as its own families, in the order they matter.
FAMILIES = [
    ("D'Arcy",   "the name the archive carries"),
    ("Sneyd",    "Ivy Miriam Sneyd's people, of Boulia and Brisbane"),
    ("Atkinson", "Ida Kathleen Atkinson's people, out of Limerick"),
    ("Murdoch",  "Audrey Dell Murdoch's people, out of Ayrshire"),
    ("Atwell",   "Barbara 'Goldie' Atwell's people, out of Somerset"),
    ("Blum",     "Martha Blum's people, out of Germany by way of Rockhampton"),
    ("Keeling",  "Eliza Keeling of London, who married into the line at Brisbane"),
    ("Creech",   "Jane Creech of Limerick"),
    ("Matson",   "Catherine Jane Matson of County Monaghan"),
    ("Wakefield","Miriam Wakefield of Bristol"),
    ("Wright",   "Sarah Wright of Lanarkshire"),
    ("Rossiter", "Maria Rossiter of Long Ashton, Somerset"),
    ("Watt",     "Marion Watt of St Quivox"),
]



# Spellings of the same Australian place that the tree treats as different.
_STATE = {
    "qld": "Queensland", "q'ld": "Queensland", "queensland": "Queensland",
    "nsw": "New South Wales", "new south wales": "New South Wales",
    "vic": "Victoria", "wa": "Western Australia", "sa": "South Australia",
    "tas": "Tasmania", "nt": "Northern Territory", "act": "Australian Capital Territory",
}


def canonical_place(p):
    """Collapse the tree's spelling variants so a count counts places.

    Only three things are done, all of them safe: repeated adjacent parts are
    dropped ("Brisbane, Brisbane, Queensland"), state abbreviations are expanded,
    and casing is tidied. Nothing is merged that is not literally the same place.
    """
    parts = [x.strip() for x in re.split(r"\s*,\s*", p) if x.strip()]
    out = []
    for x in parts:
        low = x.lower()
        x = _STATE.get(low, x)
        if low in ("australia", "england", "scotland", "ireland", "wales"):
            x = x.capitalize()
        if out and out[-1].lower() == x.lower():
            continue                      # "Brisbane, Brisbane, ..."
        out.append(x)
    # drop a trailing country that duplicates the one before it
    if len(out) > 1 and out[-1] == "United Kingdom" and out[-2] in (
            "England", "Scotland", "Wales"):
        out = out[:-1]
    return ", ".join(out)


def gen_of(ahn):
    g = 0
    while ahn >= 2 ** (g + 1):
        g += 1
    return g + 1


def ancestors(people, families, start):
    by_ahn, queue, seen = {}, collections.deque([(1, start)]), set()
    while queue:
        ahn, pid = queue.popleft()
        by_ahn[ahn] = pid
        for fid in people.get(pid, {}).get("famc", []):
            f = families.get(fid)
            if not f:
                continue
            for parent, slot in ((f["husb"], 0), (f["wife"], 1)):
                if parent and parent in people and (ahn, parent) not in seen:
                    seen.add((ahn, parent))
                    queue.append((ahn * 2 + slot, parent))
    return by_ahn


def spouses(people, families, pid):
    out = []
    for fid in people[pid]["fams"]:
        f = families.get(fid)
        if not f:
            continue
        other = f["wife"] if f["husb"] == pid else f["husb"]
        m = next((e for e in f["events"] if e["kind"] == "marriage"), {})
        d = next((e for e in f["events"] if e["kind"] == "divorce"), {})
        alive = bool(other in people and is_living(people[other]))
        out.append({
            # A living spouse is never named, not even on a published person.
            "name": "" if alive else (display(people[other]) if other in people else ""),
            "id": "" if alive else other,
            "living": alive,
            "married": "" if alive else m.get("date", ""),
            "marriedPlace": "" if alive else m.get("place", ""),
            "divorced": "" if alive else d.get("date", ""),
            # children who are themselves living are dropped from the list
            "children": [c for c in f["chil"]
                         if c in people and not is_living(people[c])],
        })
    return out


def occupation(p):
    e = ev(p, "occupation") or {}
    return e.get("detail") or e.get("note") or ""


def person_json(people, families, pid, ahn=None):
    p = people[pid]
    b, d = born(p), died(p)
    bur = ev(p, "burial") or {}
    return {
        "id": pid,
        "mh": p["mh"],
        "name": display(p),
        "surname": p["surname"],
        "sex": p["sex"],
        "ahn": ahn,
        "gen": gen_of(ahn) if ahn else None,
        "born": b.get("date", ""), "bornPlace": b.get("place", ""),
        "died": d.get("date", ""), "diedPlace": d.get("place", ""),
        "cause": d.get("cause", ""),
        "burial": bur.get("place", ""),
        "occupation": occupation(p),
        "life": lifespan(p),
        "spouses": [s for s in spouses(people, families, pid)],
        # A living parent is not named, even on a published child's page.
        "parents": [display(people[x]) for x in p["parents"]
                    if x in people and not is_living(people[x])],
        "sources": p["sources"][:6],
        "notes": p["notes"],
        "living": is_living(p),
    }


def redact(rec):
    """A living person is reduced to the fact that they exist and no more.

    They are kept in the graph only so that a line does not appear to stop; no
    date, no place, no note, no name beyond the surname reaches the build.
    """
    return {
        "id": rec["id"], "name": "—", "surname": rec["surname"],
        "living": True, "gen": rec.get("gen"), "ahn": rec.get("ahn"),
        "born": "", "bornPlace": "", "died": "", "diedPlace": "",
        "life": "", "occupation": "", "spouses": [], "parents": [],
        "sources": [], "notes": [], "cause": "", "burial": "", "mh": "",
        "sex": rec.get("sex", ""),
    }


def main():
    global LIVING
    people, families = load()
    LIVING = classify_living(people, families)
    os.makedirs(OUT, exist_ok=True)
    by_ahn = ancestors(people, families, CRISTINA)

    # ---- every ancestor, living redacted -------------------------------
    anc = []
    for ahn, pid in sorted(by_ahn.items()):
        rec = person_json(people, families, pid, ahn)
        anc.append(redact(rec) if rec["living"] else rec)
    json.dump(anc, open(os.path.join(OUT, "ancestors.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- the male D'Arcy spine ------------------------------------------
    spine, ahn = [], 1
    while ahn in by_ahn:
        rec = person_json(people, families, by_ahn[ahn], ahn)
        spine.append(redact(rec) if rec["living"] else rec)
        ahn *= 2
    json.dump(spine, open(os.path.join(OUT, "line.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- the families, as surname clusters ------------------------------
    fam_out = []
    for sn, blurb in FAMILIES:
        members = [p for p in people.values() if p["surname"].lower() == sn.lower()]
        members.sort(key=lambda p: year(born(p).get("date", "")) or 9999)
        recs = []
        for m in members:
            r = person_json(people, families, m["id"])
            recs.append(redact(r) if r["living"] else r)
        fam_out.append({
            "surname": sn, "blurb": blurb,
            "total": len(recs),
            "published": sum(1 for r in recs if not r["living"]),
            "members": recs,
        })
    json.dump(fam_out, open(os.path.join(OUT, "families.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- places, counted off the ancestor set ---------------------------
    # The tree spells the same place four ways — "Brisbane, Brisbane,
    # Queensland, Australia", "Brisbane, QLD, Australia", and so on — so a raw
    # count of the strings counts spellings rather than places. Canonicalise
    # first, keep the variants, and record the earliest year each place appears,
    # so the list can be read in the order the family actually moved.
    agg = {}
    for rec in anc:
        for pkey, dkey in (("bornPlace", "born"), ("diedPlace", "died")):
            v = (rec.get(pkey) or "").strip()
            if not v:
                continue
            canon = canonical_place(v)
            e = agg.setdefault(canon, {"place": canon, "n": 0, "variants": set(),
                                       "first": None})
            e["n"] += 1
            if v != canon:
                e["variants"].add(v)
            y = year(rec.get(dkey, "") or "")
            if y and (e["first"] is None or y < e["first"]):
                e["first"] = y
    out = []
    for e in agg.values():
        out.append({"place": e["place"], "n": e["n"], "first": e["first"],
                    "variants": sorted(e["variants"])})
    out.sort(key=lambda x: (-x["n"], x["place"]))
    json.dump(out, open(os.path.join(OUT, "places.json"), "w"),
              ensure_ascii=False, indent=1)
    places = agg

    living = sum(1 for r in anc if r["living"])
    print(f"ancestors.json  {len(anc)} ({living} living, redacted)")
    print(f"line.json       {len(spine)} generations")
    print(f"families.json   {len(fam_out)} surnames, "
          f"{sum(f['total'] for f in fam_out)} people, "
          f"{sum(f['total']-f['published'] for f in fam_out)} redacted")
    print(f"places.json     {len(places)} places")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Walk the ancestry of the root person out of the GEDCOM and write it down.

Three outputs:
  data/ancestors.tsv    every ancestor found, with the Ahnentafel number that
                        says exactly where they sit (1 = the root person,
                        2 = father, 3 = mother, 2n / 2n+1 upward from there)
  data/darcy-spine.tsv  the male D'Arcy line only — the pedigree the family
                        carries, generation by generation
  data/surname-*.tsv    every bearer of a surname of interest in the tree

Ahnentafel is used rather than a home-made numbering because it is the standard
and because it makes a gap obvious: a missing number is a missing ancestor.
"""
import csv, os, sys, collections
from gedcom import load, display, lifespan, born, died, year, ev, classify_living

LIVING = {}


def is_living(p):
    return LIVING.get(p["id"], True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ROOT_PERSON = "@I2@"          # the living descendant the sweep starts from
SURNAMES = ["D'Arcy", "Murdoch", "Sneyd", "Atkinson", "Bamford", "Peters"]


def ancestors(people, families, start, maxgen=40):
    """Ahnentafel walk. Returns {ahn: person_id} and {person_id: [ahn, ...]}."""
    by_ahn, queue = {}, collections.deque([(1, start)])
    seen_edges = set()
    while queue:
        ahn, pid = queue.popleft()
        if ahn > 2 ** maxgen or pid is None:
            continue
        by_ahn[ahn] = pid
        p = people.get(pid)
        if not p:
            continue
        # the family this person is a child of gives the parents
        for fid in p["famc"]:
            f = families.get(fid)
            if not f:
                continue
            for parent, slot in ((f["husb"], 0), (f["wife"], 1)):
                if not parent or parent not in people:
                    continue
                edge = (ahn, parent)
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                queue.append((ahn * 2 + slot, parent))
    return by_ahn


def gen_of(ahn):
    """Generation number: 1 for the root, 2 for parents, and so on."""
    g = 0
    while ahn >= 2 ** (g + 1):
        g += 1
    return g + 1


def spouse_of(people, families, pid):
    out = []
    for fid in people[pid]["fams"]:
        f = families.get(fid)
        if not f:
            continue
        other = f["wife"] if f["husb"] == pid else f["husb"]
        if other and other in people:
            m = next((e for e in f["events"] if e["kind"] == "marriage"), {})
            out.append((other, m.get("date", ""), m.get("place", "")))
    return out


def occupation(p):
    e = ev(p, "occupation")
    return (e or {}).get("detail") or (e or {}).get("note") or ""


REDACT = True   # never write a living person's details to a committed file


def row_for(people, families, pid, ahn=None):
    p = people[pid]
    if REDACT and is_living(p):
        # The same rule the site build applies, applied here too, because this
        # repository is public and these files are committed to it.
        return {"ahn": ahn or "", "gen": gen_of(ahn) if ahn else "", "id": p["id"],
                "mh": "", "name": "— living, withheld —", "sex": "", "born": "",
                "born_place": "", "died": "", "died_place": "", "cause": "",
                "burial": "", "occupation": "", "spouses": "", "living": "yes",
                "n_notes": "", "sources": ""}
    b, d = born(p), died(p)
    bur = ev(p, "burial") or {}
    sp = spouse_of(people, families, pid)
    return {
        "ahn": ahn or "",
        "gen": gen_of(ahn) if ahn else "",
        "id": p["id"],
        "mh": p["mh"],
        "name": display(p),
        "sex": p["sex"],
        "born": b.get("date", ""),
        "born_place": b.get("place", ""),
        "died": d.get("date", ""),
        "died_place": d.get("place", ""),
        "cause": d.get("cause", ""),
        "burial": bur.get("place", ""),
        "occupation": occupation(p),
        # A living spouse is named nowhere, even on a deceased person's row.
        "spouses": " | ".join(
            ("— living, withheld —" if is_living(people[s]) else display(people[s]))
            + (f' (m. {dt})' if dt and not is_living(people[s]) else "")
            for s, dt, _ in sp),
        "living": "yes" if is_living(p) else "",
        "n_notes": len(p["notes"]),
        "sources": " | ".join(p["sources"][:4]),
    }


FIELDS = ["ahn", "gen", "id", "mh", "name", "sex", "born", "born_place", "died",
          "died_place", "cause", "burial", "occupation", "spouses", "living",
          "n_notes", "sources"]


def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  {len(rows):>5} rows  {os.path.relpath(path, ROOT)}")


def main():
    global LIVING
    people, families = load()
    LIVING = classify_living(people, families)
    print(f"{len(people)} people, {len(families)} families "
          f"({sum(LIVING.values())} judged living)")

    by_ahn = ancestors(people, families, ROOT_PERSON)
    print(f"\n{len(by_ahn)} ancestors of the root person "
          f"(deepest generation {max(gen_of(a) for a in by_ahn)})")

    rows = [row_for(people, families, pid, ahn)
            for ahn, pid in sorted(by_ahn.items())]
    write(os.path.join(DATA, "ancestors.tsv"), rows)

    # The male D'Arcy spine: ahnentafel 1, 2, 4, 8, 16 ... doubling each time.
    spine, ahn = [], 1
    while ahn in by_ahn:
        spine.append(row_for(people, families, by_ahn[ahn], ahn))
        ahn *= 2
    write(os.path.join(DATA, "darcy-spine.tsv"), spine)

    for sn in SURNAMES:
        hits = [p for p in people.values() if p["surname"].lower() == sn.lower()]
        hits.sort(key=lambda p: year(born(p).get("date", "")) or 9999)
        slug = sn.lower().replace("'", "").replace(" ", "-")
        write(os.path.join(DATA, f"surname-{slug}.tsv"),
              [row_for(people, families, p["id"]) for p in hits])

    print("\nThe D'Arcy spine, as the tree currently asserts it:")
    for r in spine:
        print(f'  g{r["gen"]:<3} {r["name"]:<44} {r["born"][-4:] or "?":>4}'
              f'–{r["died"][-4:] or "?":<4}  {r["born_place"][:40]}')

    # how many generations have a source attached at all
    with_src = sum(1 for r in spine if r["sources"])
    print(f"\n{with_src} of {len(spine)} spine generations carry a source string "
          f"in the tree; {len(spine) - with_src} carry none.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""A pin that inherited its parent's coordinate is not a located place.

WHAT THIS REFUSES, AND WHY THE ARCHIVE ALREADY KNEW
---------------------------------------------------
tools/atlas.py carries a comment explaining why three hand-documented hamlets
were left off the map:

    Wanswell, Hinton and Blakeney were tried and every one of them fell back
    to its parish's point — three pins on Berkeley and one on Awre, all
    stamped "exact" by a gazetteer that had simply not heard of them. That is
    false precision, and a map that claims it is worse than a map that omits
    them.

That rule was applied to the nine places this archive adds by hand and never
once run against the hundred and fifty-six it already had. On 21 September
2026 a neighbouring archive, building a graves layer over this map, reported
that twenty place-heads appeared more than once. Grouping by COORDINATE
instead of by head found the real fault underneath it:

    21 different places shared the single point 52.53102, -1.26491, carrying
    34 people, every one stamped `fix: "exact"`. That point is the geocode for
    "England". On it sat BERKELEY with six people — the place this archive is
    about — along with London, Portsmouth, Somerset, Clarkenwell, Theobalds
    Palace and fifteen others.

HOW IT DECIDES
--------------
A place has INHERITED its pin when its coordinate is identical to that of
another place in the same list whose full name is a comma-tail of its own —
"Berkeley, Gloucestershire, England" sharing a point with "England", or
"Wotton-under-Edge, Gloucestershire" with "Gloucestershire". Identical to six
decimal places is not a coincidence between two different towns; it is one
lookup answering for both.

An inherited pin is not deleted and the place is not dropped. The map keeps it
and says what it is. What the gate refuses is an inherited pin that still
CLAIMS to be exact, because that is the only part a reader cannot see.

    python3 tools/check_atlas.py
"""
import json, math, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "..", "site", "public", "atlas-data.json")


def parts(s):
    return [x.strip().lower() for x in (s or "").split(",") if x.strip()]


def inherited(places):
    """[(index, owner index)] for every place sitting on a broader place's pin."""
    by = collections.defaultdict(list)
    for i, r in enumerate(places):
        by[(r.get("lat"), r.get("lon"))].append(i)
    out = []
    for ix in by.values():
        if len(ix) < 2:
            continue
        for i in ix:
            mine = parts(places[i].get("what"))
            for j in ix:
                if i == j:
                    continue
                theirs = parts(places[j].get("what"))
                if not theirs:
                    continue
                # j is the containing place: its whole name is a tail of i's,
                # or it is a single administrative name appearing inside i's.
                if (len(theirs) < len(mine) and mine[-len(theirs):] == theirs) \
                        or (len(theirs) == 1 and theirs[0] in mine[1:]):
                    out.append((i, j))
                    break
    return out


SAME = os.path.join(HERE, "..", "site", "src", "data", "place-same.json")
SPLIT_KM = 2.0


def _km(a, b):
    p = math.pi / 180
    h = (0.5 - math.cos((b[0] - a[0]) * p) / 2
         + math.cos(a[0] * p) * math.cos(b[0] * p) * (1 - math.cos((b[1] - a[1]) * p)) / 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def split_heads(places):
    """Heads whose own pins disagree by more than SPLIT_KM.

    One head, one place, one pin. Two rows called "Hornby Castle" sitting a
    hundred kilometres apart are either one castle geocoded twice or two
    castles sharing a name, and a map may not decline to say which — it draws
    them as two places either way, and splits the people between them so that
    neither shows the true weight.

    Pins already marked `parent` are excluded: an inherited pin is not a claim
    about where a second place is, and it is refused by the check above on its
    own terms.
    """
    heads = collections.defaultdict(list)
    for i, r in enumerate(places):
        if r.get("fix") == "parent":
            continue
        heads[(r.get("name") or "").split(",")[0].strip().lower()].append(i)
    out = []
    for h, ix in heads.items():
        if len(ix) < 2:
            continue
        cs = [(places[i].get("lat"), places[i].get("lon")) for i in ix]
        if any(c[0] is None for c in cs):
            continue
        far = max(_km(a, b) for a in cs for b in cs)
        if far > SPLIT_KM:
            out.append((h, ix, far))
    return out


def settled():
    """Every head this archive has already judged, from place-same.json."""
    if not os.path.exists(SAME):
        return set()
    reg = json.load(open(SAME, encoding="utf-8"))
    return {(g.get("head") or "").strip().lower() for g in reg.get("groups", [])}


def main():
    if not os.path.exists(ATLAS):
        print("  FAIL  atlas      atlas-data.json is missing — nothing to check")
        return 1
    d = json.load(open(ATLAS, encoding="utf-8"))
    places = d.get("places") or []
    if len(places) < 50:
        print(f"  FAIL  atlas      only {len(places)} place(s) — the atlas looks unbuilt")
        return 1

    inh = inherited(places)
    bad = [(i, j) for i, j in inh if places[i].get("fix") == "exact"]

    for i, j in bad:
        p, o = places[i], places[j]
        print(f"  FAIL  atlas      {p.get('name','?')!r} ({p.get('n') or 0} people) claims "
              f"fix=exact on {o.get('name','?')!r}'s own coordinate "
              f"{p.get('lat')},{p.get('lon')} — it inherited that point, it was not found at it")
    if bad:
        ppl = sum(places[i].get("n") or 0 for i, _ in bad)
        print(f"  FAIL  atlas      {len(bad)} inherited pin(s) stamped exact, "
              f"carrying {ppl} people. A map that claims false precision is "
              f"worse than a map that omits the place.")
        return 1

    done = settled()
    split = [(h, ix, km) for h, ix, km in split_heads(places) if h not in done]
    for h, ix, km in split:
        print(f"  FAIL  atlas      {h!r} is drawn as {len(ix)} places {km:.0f} km apart "
              f"and the archive has not said whether it is one. Settle it in "
              f"site/src/data/place-same.json — one head, one place, one pin")
    if split:
        print(f"  FAIL  atlas      {len(split)} head(s) split across coordinates and unsettled")
        return 1

    print(f"  ok    atlas      {len(places)} place(s), {len(inh)} on a broader place's "
          f"coordinate and none of them called exact; {len(done)} head(s) settled, "
          f"no unsettled head split by more than {SPLIT_KM:g} km")
    return 0


if __name__ == "__main__":
    sys.exit(main())

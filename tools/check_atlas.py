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

# ONE RULE, ONE IMPLEMENTATION. This file used to carry its own copy of the
# containment test and its own copy of the string tidying, and the two drifted
# the moment atlas_pins learned to unescape HTML and cut at " or " — the gate
# and the thing it gates disagreeing about what counts as inherited. Worse, the
# local copy returned a LIST OF PAIRS where the caller treated it as a set of
# indices, so `i not in inh` compared an int against tuples, was always true,
# and every row read as un-inherited. A check that cannot fail, in the file
# whose whole job is refusing those.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_pins

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "..", "site", "public", "atlas-data.json")


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


def declared_pins():
    """{(lat, lon): verdict} for coordinates this archive has judged by hand."""
    if not os.path.exists(SAME):
        return {}
    reg = json.load(open(SAME, encoding="utf-8"))
    out = {}
    for e in reg.get("pins") or []:
        at = e.get("at") or []
        if len(at) == 2:
            out[(round(float(at[0]), 5), round(float(at[1]), 5))] = e.get("verdict")
    return out


def fallbacks(places):
    """Coordinates carrying more than one place where none contains another.

    An inherited pin names its own owner and is caught by containment. A
    FALLBACK pin does not: nothing on this map is called "Gloucester" the city,
    so the three villages written «X, Gloucester, England» that were all sent to
    one point had no parent to be attributed to and sat there marked `approx`.
    The verdict cannot be automatic — one such point is Berkeley with the hamlet
    of Saniger deliberately on it — so each is judged in place-same.json and
    this refuses any that is not.
    """
    inh = set(atlas_pins.inherited(places))
    by = collections.defaultdict(list)
    for i, r in enumerate(places):
        if r.get("lat") is None:
            continue
        by[(round(r["lat"], 5), round(r["lon"], 5))].append(i)
    out = []
    for k, ix in by.items():
        free = [i for i in ix if i not in inh]
        if len(free) > 1:
            out.append((k, free))
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

    inh = list(atlas_pins.inherited(places).items())
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

    declared = declared_pins()
    undeclared = [(k, ix) for k, ix in fallbacks(places) if k not in declared]
    for k, ix in undeclared:
        names = ", ".join(repr(places[i].get("name")) for i in ix[:4])
        print(f"  FAIL  atlas      {len(ix)} places share {k[0]},{k[1]} and none contains "
              f"another — {names}. A coordinate several places were sent to is not "
              f"any of them. Judge it in site/src/data/place-same.json under `pins`")
    if undeclared:
        print(f"  FAIL  atlas      {len(undeclared)} shared coordinate(s) unjudged")
        return 1

    bad_shared = [r for r in places
                  if r.get("fix") == "exact"
                  and declared.get((round(r["lat"], 5), round(r["lon"], 5))) == "fallback"]
    for r in bad_shared:
        print(f"  FAIL  atlas      {r.get('name')!r} claims fix=exact on a coordinate "
              f"this archive has judged a fallback")
    if bad_shared:
        return 1

    nsh = sum(1 for r in places if r.get("fix") == "shared")
    print(f"  ok    atlas      {len(declared)} shared coordinate(s) judged, "
          f"{nsh} row(s) stamped `shared`")
    print(f"  ok    atlas      {len(places)} place(s), {len(inh)} on a broader place's "
          f"coordinate and none of them called exact; {len(done)} head(s) settled, "
          f"no unsettled head split by more than {SPLIT_KM:g} km")
    return 0


if __name__ == "__main__":
    sys.exit(main())

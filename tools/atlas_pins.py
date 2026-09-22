#!/usr/bin/env python3
"""Tell the truth about which pins were found and which were settled for.

A gazetteer that cannot find a place does not say so. It answers with the
smallest thing it did recognise — for most of this archive's damaged export
strings, the country at the end — and the confidence field records that the
LOOKUP succeeded, not that it answered the question asked. So on 21 September
2026 twenty-one places sat on 52.53102, -1.26491, which is the geocode for the
word ENGLAND, and every one of them was stamped `fix: "exact"`. Berkeley was
among them, with six people on it.

It is not a coverage problem that better strings would cure. "Teddington,
Middlesex, England", "Walden, Essex, England" and "Wotton-under-Edge,
Gloucestershire, England" are all perfectly well formed and all three land on
the country. The gazetteer simply has not heard of them, and says so by
answering something else.

So this does not geocode anything and does not move any marker. It changes
what a marker CLAIMS. A pin that is identical, to six decimals, to the pin of
a place that contains it was inherited, not found — and is marked `parent`,
with the place it came from named beside it, so the map can draw it as what it
is and the reader can see which is which.

    python3 tools/atlas_pins.py              # report against the built atlas
    python3 tools/atlas_pins.py --write      # mark them in place

Imported by tools/atlas.py, which calls mark() once the kit has written the
file. Kept separate because this is an audit of somebody else's confidence
field, not part of building the rows.
"""
import html as _html
import json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "..", "site", "public", "atlas-data.json")


def _parts(s):
    """The comma levels of a recorded place string, tidied just enough to compare.

    Three kinds of damage in this export stop a plain split from seeing that one
    string contains another, and each of them hid a real fault:

      "Portsmouth, Hampshire, England or West Indies" — the export hedging
      between two places. Its last level is "england or west indies", so it does
      not end in "england" and it sat on the England centroid still stamped
      EXACT after every other pin there had been caught.

      "&lt;Ehrstaedt, Heidelberg, Baden, Germany&gt;" — HTML escapes never
      unescaped, which made one row invisible beside its own twin.

      Trailing "UK." and the like, which is not a different country.
    """
    s = _html.unescape(s or "").replace("<", " ").replace(">", " ")
    s = re.split(r"\s+or\s+", s, maxsplit=1)[0]
    out = []
    for x in s.split(","):
        x = x.strip().lower().rstrip(".")
        if x in ("uk", "united kingdom"):
            x = "england" if "england" in s.lower() else x
        if x:
            out.append(x)
    return out


def inherited(places):
    """{index: owner index} for every place sitting on a containing place's pin.

    Containment is decided on the RECORDED string, not on the coordinate —
    two towns really can be a few metres apart, and this must not accuse them.
    A place inherits when some other place on the identical point is named by
    a comma-tail of its own name, or is a single administrative name that
    appears inside it.
    """
    by = collections.defaultdict(list)
    for i, r in enumerate(places):
        by[(r.get("lat"), r.get("lon"))].append(i)
    out = {}
    for ix in by.values():
        if len(ix) < 2:
            continue
        for i in ix:
            mine = _parts(places[i].get("what"))
            for j in ix:
                if i == j:
                    continue
                theirs = _parts(places[j].get("what"))
                if not theirs:
                    continue
                if (len(theirs) < len(mine) and mine[-len(theirs):] == theirs) \
                        or (len(theirs) == 1 and theirs[0] in mine[1:]):
                    out[i] = j
                    break
    return out


SAME = os.path.join(HERE, "..", "site", "src", "data", "place-same.json")


def _register():
    if not os.path.exists(SAME):
        return []
    return json.load(open(SAME, encoding="utf-8")).get("pins") or []


def shared(places):
    """{index: n_places_on_that_point} for rows on a declared FALLBACK coordinate.

    A fallback pin is the one an inherited pin is not: nothing on the map is
    named as its owner, so there is no parent to attribute it to and nothing
    catches it. Three Gloucestershire villages sat on one of these, all marked
    `approx`, until two of them were folded away and the third was left alone on
    it looking like an ordinary located place. The verdicts live in
    place-same.json because one such point is correct and deliberate — Berkeley
    with the hamlet of Saniger on it — and no rule can tell that from the rest.
    """
    out = {}
    for entry in _register():
        if entry.get("verdict") != "fallback":
            continue
        want = {w.strip().lower() for w in entry.get("places", [])}
        for i, r in enumerate(places):
            if (r.get("what") or "").strip().lower() in want \
                    or (r.get("name") or "").strip().lower() in want:
                out[i] = len(entry.get("places", []))
    return out


def mark(path=ATLAS):
    """Re-stamp inherited pins. Returns (marked, people_on_them)."""
    d = json.load(open(path, encoding="utf-8"))
    places = d.get("places") or []
    inh = inherited(places)
    ppl = 0
    for i, j in inh.items():
        places[i]["fix"] = "parent"
        places[i]["fixFrom"] = places[j].get("name") or places[j].get("what")
        ppl += places[i].get("n") or 0
    sh = shared(places)
    for i in sh:
        if i in inh:            # a declared fallback that is also inherited:
            continue            # `parent` is the more specific answer, keep it
        places[i]["fix"] = "shared"
        places[i]["fixNote"] = "a point several places were sent to — not this place"
    st = d.setdefault("stats", {})
    st["shared"] = sum(1 for r in places if r.get("fix") == "shared")
    st["parent"] = len(inh)
    st["parentPeople"] = ppl
    # `approx` was counted before these were re-stamped, so recount it rather
    # than leave a number describing a state the file is no longer in. Six of
    # the thirty-six were already approximate; the rest called themselves exact.
    st["approx"] = sum(1 for r in places if r.get("fix") == "approx")
    st["exact"] = sum(1 for r in places if r.get("fix") == "exact")
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return len(inh), ppl


def main(argv):
    if not os.path.exists(ATLAS):
        print("  atlas_pins: no atlas-data.json to read")
        return 1
    d = json.load(open(ATLAS, encoding="utf-8"))
    places = d.get("places") or []
    inh = inherited(places)
    if "--write" in argv:
        n, ppl = mark()
        print(f"  ok    atlas_pins  {n} pin(s) marked `parent`, carrying {ppl} people")
        return 0
    byowner = collections.Counter(places[j].get("name") for j in inh.values())
    ppl = sum(places[i].get("n") or 0 for i in inh)
    print(f"  atlas_pins: {len(inh)} inherited pin(s) carrying {ppl} people")
    for owner, n in byowner.most_common():
        print(f"      {n:3}  on {owner!r}'s own coordinate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

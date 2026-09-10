#!/usr/bin/env python3
"""Compare the family tree's prediction against an autosomal ethnicity estimate.

One living descendant of Kenneth Lindsay D'Arcy and Audrey "Dell" Murdoch has
tested with MyHeritage. She is living, so she is not named anywhere in the
output and her kit is not identified — but the numbers are the first check this
archive has ever had from outside the paper record, and they can be published
without her.

The method: walk her pedigree and attribute each lineage to the country of its
DEEPEST RECORDED ancestor. That is what a pedigree actually predicts about deep
origin — an Australian birthplace is never a terminus unless the trail stops
there, and where the trail stops is reported as its own answer rather than
quietly dropped.

Writes site/src/data/dna.json. Re-run it after any research that fills an
ancestor slot: the prediction is supposed to move.
"""
import json, os, sys, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gedcom import load, display, born

OUT = os.path.join(ROOT, "site", "src", "data", "dna.json")
TESTER = "@I23@"          # living — never written to the output

# The two joins this archive has tested and rejected. The prediction is computed
# twice: once with the tree as the family holds it, and once with these cut. The
# second is the one this archive will defend.
GRAFTS = {"@I1872@": "Hornby", "@I501870@": "Keele"}
sys.setrecursionlimit(10000)

# The estimate as it stands on the results page, read 10 September 2026.
ESTIMATE = {
    "provider": "MyHeritage",
    "version": "v2.5",
    "read": "10 September 2026",
    "confidence": "middle of the slider — showing 2 of 3 genetic groups",
    "groups": [
        ["Scottish and Welsh", 41.9, "one lumped region, with “UK and Ireland” nested beneath it"],
        ["English", 19.1, ""],
        ["Irish", 19.1, ""],
        ["Dutch", 5.9, ""],
        ["Danish", 4.4, ""],
        ["Breton", 4.2, ""],
        ["Germanic", 3.8, ""],
        ["French", 1.6, ""],
    ],
    "extra": "England #13",
}

COUNTRY = [
 (r"scotland|ayrshire|midlothian|leith|quivox|glasgow|edinburgh|greenock|renfrew|lanark|\bsctl\b", "Scotland"),
 (r"\bwales\b|glamorgan|swansea|cardiff|monmouth|carmarthen", "Wales"),
 (r"ireland|cork|limerick|monaghan|carrigaline|dublin|galway|wicklow|tipperary|kerry|clare", "Ireland"),
 (r"denmark|danish|k[oø]benhavn|copenhagen|jutland", "Denmark"),
 (r"oldenburg|schomberg|wildeshausen|tecklenburg|diepholz|rietberg|honstein|schauenburg|brandenburg|"
  r"brunswick|germany|prussia|hesse|baden|w[uü]rttemberg|saxony|bavaria|holstein|deutschland|westphalia", "Germany"),
 (r"netherlands|holland|dutch|amsterdam|utrecht", "Netherlands"),
 (r"france|normandy|brittany|breton|picardy|paris|calais", "France"),
 (r"barbados|west indies|bridgetown|jamaica", "Caribbean"),
 (r"england|gloucester|berkeley|bristol|london|kent|chatham|portsea|portsmouth|somerset|staffordshire|"
  r"madeley|keele|yorkshire|hornby|denton|oxford|wolstanton|bradwell|leek|kempsey|headington|middlesex|"
  r"surrey|essex|devon|cornwall|lancashire|norfolk|suffolk|wiltshire|dorset|hampshire|warwick|worcester|"
  r"shropshire|cheshire|durham|northumberland|derby|leicester|lincoln|nottingham|bedford|hertford|"
  r"buckingham|berkshire|sussex|cumberland|westmorland|rutland|huntingdon|cambridge|northampton|teddington|"
  r"putney|aller|long ashton|\beng\.?\b", "England"),
 (r"australia|queensland|brisbane|parramatta|sydney|new south wales|camden|boulia|muttaburra|rockhampton|"
  r"landsborough|gladstone|windsor|toowoomba|gympie|sandgate", "Australia"),
]


def main():
    people, fams = load()

    def parents(pid, cut=False):
        out = []
        for fid in people.get(pid, {}).get("famc", []):
            fam = fams.get(fid, {})
            for r in ("husb", "wife"):
                q = fam.get(r)
                if q and q in people and not (cut and q in GRAFTS):
                    out.append(q)
        return out[:2]

    def place(pid):
        return ((born(people[pid]) or {}).get("place", "") or "")

    def country(pid):
        s = place(pid).lower()
        for pat, c in COUNTRY:
            if re.search(pat, s):
                return c
        return None

    COLD = "the trail stops here"

    def dist(pid, path=frozenset(), cut=False):
        """Attribute each lineage to the deepest ancestor whose COUNTRY IS KNOWN
        — not simply the deepest ancestor on record.

        The difference matters enormously and I got it wrong the first time. The
        tester's great-grandfather was born at St Quivox in Ayrshire; his own
        parents are in the tree as names with no birthplace at all. Recursing to
        the deepest *recorded* ancestor threw St Quivox away and called that
        eighth of the pedigree unknown, which put the tree's predicted Scottish
        share at 0.02% and made the DNA look like it was contradicting the tree.
        It was not. The tree knew perfectly well.

        An Australian birthplace is never an origin: where a line goes cold at an
        Australian, that is reported as its own answer rather than counted."""
        if pid in path:
            return collections.Counter()
        ps = parents(pid, cut)
        own = country(pid)
        if own == "Australia":
            own = None                       # a birthplace, not an origin
        if not ps:
            return collections.Counter({own or COLD: 1.0})
        out = collections.Counter()
        for q in ps:
            sub = collections.Counter(dist(q, path | {pid}, cut))
            if own and sub.get(COLD):        # nothing known above: fall back on this person
                sub[own] += sub.pop(COLD)
            for k, v in sub.items():
                out[k] += v / len(ps)
        return out

    def filled(pid, depth=0, maxd=14):
        """How many of the ancestor slots this archive can actually fill."""
        if depth >= maxd:
            return 0, 0
        ps = parents(pid)
        n, d = len(ps), 2
        for q in ps:
            a, b = filled(q, depth + 1, maxd)
            n += a; d += b
        return n, d

    def deepest_stops(pid, limit=8):
        stops = []
        def walk(x, g, path):
            if x in path:
                return
            ps = parents(x)
            if not ps:
                stops.append((g, display(people[x]), place(x) or ""))
            for q in ps:
                walk(q, g + 1, path | {x})
        walk(pid, 0, frozenset())
        # the shallowest stops are the ones that cost the most information
        return sorted(stops, key=lambda s: (s[0], s[1]))[:limit]

    d = dist(TESTER)
    dcut = dist(TESTER, cut=True)
    cold = d.get(COLD, 0.0)
    known = sum(d.values()) - cold

    sides = []
    for fid in people[TESTER].get("famc", []):
        fam = fams[fid]
        for role, lab in (("husb", "father"), ("wife", "mother")):
            pid = fam.get(role)
            if not pid:
                continue
            n, dd = filled(pid)
            sides.append({
                "role": lab,
                "name": display(people[pid]),
                "filled": n, "slots": dd,
                "pct": round(n / dd * 100),
                "stops": [{"gen": g + 1, "name": nm, "place": pl}
                          for g, nm, pl in deepest_stops(pid)],
            })

    data = {
        "estimate": ESTIMATE,
        "predicted": [{"country": c, "share": round(v * 100, 2),
                       "ofKnown": round(v / known * 100, 1) if known else 0}
                      for c, v in d.most_common() if c != "the trail stops here"],
        "predictedCut": [{"country": c, "share": round(v * 100, 2)}
                         for c, v in dcut.most_common() if c != COLD],
        "coldCut": round(dcut.get(COLD, 0.0) * 100, 1),
        "cold": round(cold * 100, 1),
        "known": round(known * 100, 1),
        "sides": sides,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"prediction covers {data['known']}% of the pedigree; {data['cold']}% goes cold")
    print("  as the tree stands | with both grafts cut")
    cutmap = {r["country"]: r["share"] for r in data["predictedCut"]}
    for r in data["predicted"]:
        print(f"   {r['country']:12s} {r['share']:6.2f}%   {cutmap.get(r['country'], 0.0):6.2f}%")
    print(f"   {'trail cold':12s} {data['cold']:6.1f}%   {data['coldCut']:6.1f}%")
    for s in sides:
        print(f"   {s['role']:8s} {s['name']:34s} {s['filled']}/{s['slots']} = {s['pct']}%")


if __name__ == "__main__":
    main()

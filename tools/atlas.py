#!/usr/bin/env python3
"""D'Arcy's places, for the map.

The place list already carries a count, the earliest year and the spellings
the same town was written under — which is exactly the benchmark's "also
written". The people come from the ancestors file, which records a birthplace
for 148 of them and a place of death for 112.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "site", "node_modules",
                                "@daviddef", "archive-kit", "kit", "tools"))
import atlasdata, geocode as G

D = os.path.join(HERE, "..", "site", "src", "data")
J = lambda n: json.load(open(os.path.join(D, n), encoding="utf-8"))

def cat(p):
    s = p.lower()
    if re.search(r"australia|queensland|nsw|victoria|new south wales", s): return "au"
    if re.search(r"ireland|limerick|cork|dublin|tipperary", s):            return "ie"
    if re.search(r"scotland|edinburgh|leith|lanark", s):                   return "sc"
    if re.search(r"england|london|devon|suffolk|kent|york|sussex|essex|norfolk|middlesex|gloucester|bedford|barbados", s): return "en"
    return "other"

def main():
    places = J("places.json")
    anc = J("ancestors.json")
    who = {}
    for r in anc:
        for key in ("bornPlace", "diedPlace"):
            p = r.get(key)
            if p and r.get("name") and r["name"] != "—":
                who.setdefault(p, []).append(r["name"])
    rows = []
    for p in places:
        name = p["place"]
        names = []
        for k in [name] + (p.get("variants") or []):
            for n in who.get(k, []):
                if n not in names: names.append(n)
        rows.append({
            "name": name.split(",")[0].strip() or name,
            "_lookup": name,
            "cat": cat(name),
            "n": p.get("n") or 0,
            "when": f"first recorded {p['first']}" if p.get("first") else "",
            "what": name,
            "also": [v for v in (p.get("variants") or []) if v != name][:6],
            "people": [{"n": n} for n in names[:12]],
            "more": max(0, len(names) - 12) or None,
        })
    atlasdata.build(rows, os.path.join(HERE, "..", "site", "public", "atlas-data.json"),
                    countries=["United Kingdom","Ireland","Éire","Australia","Barbados","Italia","Italy","France","Deutschland","Germany","España","Spain","Danmark","Denmark","Nederland","Netherlands"])

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Nationality audit of the register, done the same way every time.

This was hand-written as a throwaway regex on each pass and it drifted: the
published figures moved for reasons that had nothing to do with new records.
It is a script now so the number means the same thing in September as it did
in August. Classification is by SOURCE, not by person — the question is which
country's archives this evidence comes out of.
"""
import json, re, sys

AUS = re.compile(r"""Queensland|QSA\b|NAA\b|AWM\b|Trove|Blue Book|Qld\b|Brisbane
    |New South Wales|NSW\b|Victoria(?:n)? (?:BDM|marriages)|Australia""", re.I | re.X)

BRI = re.compile(r"""FreeREG|FreeBMD|FreeCEN|census|TNA\b|PROB\s|ADM\s|WO\s|Connolly
    |Gazette|Bishop|Gloucestershire|Berkeley|Bigland|Collinson|Birmingham
    |National Archives|Diocesan|Hanley|General Register|Chew|Hampshire|Shropshire
    |Somerset|Staffordshire|Cheshire|Stroud|Bristol|England|English|Scotland|Ireland
    |Newspaper|Morning|Standard|Chronicle|Herald|Lady's|Army|Officers|Artillery
    |Peninsular|FamilySearch|Priestlands|Portsea|Chatham|Leith|Oswestry|Madeley""",
    re.I | re.X)

def classify(src):
    if AUS.search(src):
        return "AUS"
    if BRI.search(src):
        return "BRI"
    return "OTHER"

def main():
    reg = json.load(open("site/src/data/register.json", encoding="utf-8"))
    recs = [r for g in reg["groups"] for r in g["rows"] if r["kind"] == "record"]
    buckets = {"AUS": [], "BRI": [], "OTHER": []}
    for r in recs:
        buckets[classify(r["source"])].append(r)
    n = len(recs)
    out = {k: len(v) for k, v in buckets.items()}
    pct = {k: round(v / n * 100) for k, v in out.items()}
    print(f"records {n} · Australian {out['AUS']} ({pct['AUS']}%) · "
          f"British {out['BRI']} ({pct['BRI']}%) · unclassified {out['OTHER']}")
    for r in buckets["OTHER"][:10]:
        print("  unclassified:", r["source"][:80])
    json.dump({"records": n, "aus": out["AUS"], "bri": out["BRI"],
               "other": out["OTHER"], "ausPct": pct["AUS"], "briPct": pct["BRI"]},
              open("site/src/data/audit.json", "w", encoding="utf-8"), indent=1)
    return 0 if out["OTHER"] == 0 else 0

if __name__ == "__main__":
    sys.exit(main())

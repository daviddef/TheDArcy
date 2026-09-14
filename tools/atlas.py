#!/usr/bin/env python3
"""D'Arcy's places, for the map.

The place list already carries a count, the earliest year and the spellings
the same town was written under — which is exactly the benchmark's "also
written". The people come from the ancestors file, which records a birthplace
for 148 of them and a place of death for 112.
"""
import json, os, re, sys, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "site", "node_modules",
                                "@daviddef", "archive-kit", "kit", "tools"))
import atlasdata, geocode as G

D = os.path.join(HERE, "..", "site", "src", "data")
J = lambda n: json.load(open(os.path.join(D, n), encoding="utf-8"))

# ── Tidying the lookup string ────────────────────────────────────────────────
# The place strings come out of a MyHeritage export and carry three kinds of
# damage that stop a gazetteer cold: HTML escapes that were never unescaped
# ("&lt;Ehrstaedt"), nineteenth-century abbreviation ("Butcombe Som Eng",
# "of St Quivox, Ayr, Sctl"), and editorial prose where a place should be
# ("Christened in Berkeley", "Portsmouth, Hampshire, England or West Indies").
#
# None of this changes what the archive SAYS a place is — `what` and `also`
# still carry the string exactly as recorded. This only changes what is handed
# to the geocoder, so the marker lands on the map.
ABBREV = [
    (r"\bSom\b\.?",        "Somerset"),
    (r"\bEng\b\.?",        "England"),
    (r"\bEngl\b\.?",       "England"),
    (r"\bSctl\b\.?",       "Scotland"),
    (r"\bScot\b\.?",       "Scotland"),
    (r"\bQ'?ld\b\.?",      "Queensland"),
    (r"\bNSW\b\.?",        "New South Wales"),
    (r"\bAU\b\.?",         "Australia"),
    (r"\bWuertt\b\.?",     "W\u00fcrttemberg"),
    (r"\bGerm\b\.?",       "Germany"),
    (r"\bStaffs\b\.?",     "Staffordshire"),
    (r"\bLeic\b\.?",       "Leicestershire"),
    (r"\bYorks\b\.?",      "Yorkshire"),
    (r"\bBW\b",             "Baden-W\u00fcrttemberg"),
    (r"\bInglaterra\b",     "England"),
    (r"\bDeutschland\(HRR\)", "Deutschland"),
]
# Prose the export put in a place field. Stripped from the front.
REGION = ["Somerset", "England", "Scotland", "Ireland", "Wales", "Queensland",
          "New South Wales", "Australia", "Staffordshire", "Leicestershire",
          "Yorkshire", "Gloucestershire", "Hampshire", "Shropshire", "Cheshire",
          "Germany", "Deutschland", "W\u00fcrttemberg", "Baden-W\u00fcrttemberg",
          "Warwickshire", "Lincolnshire", "Nottinghamshire", "Middlesex"]

PREFIX = re.compile(r"^\s*(?:of,?|christened in|born in|died in|about|\(about\)|parish of)\s+", re.I)


def tidy(name):
    """What to hand the gazetteer. Never what to print."""
    s = html.unescape(name or "").replace("<", " ").replace(">", " ")
    s = s.replace("/", ", ")
    # "X or Y" — the export hedging between two places. Take the first.
    s = re.split(r"\s+or\s+", s, maxsplit=1)[0]
    for _ in range(3):
        t = PREFIX.sub("", s)
        if t == s:
            break
        s = t
    for pat, rep in ABBREV:
        s = re.sub(pat, rep, s, flags=re.I)
    # "Butcombe Som Eng" expands to "Butcombe Somerset England", which is still
    # not a query — a gazetteer wants the levels separated. Put the commas back
    # in front of any county or country left dangling after a word.
    # Longest first, or "New South Wales" is cut in half at "Wales"; and never
    # after a direction word, or "North Yorkshire" becomes "North, Yorkshire".
    for w in sorted(REGION, key=len, reverse=True):
        s = re.sub(r"(?<!\bNorth)(?<!\bSouth)(?<!\bEast)(?<!\bWest)(?<!\bNew)"
                   r"(?<=[A-Za-z\u00c0-\u024f])\s+(" + w + r")\b", r", \1", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"(,\s*)+,", ", ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,.")
    return s


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
            "_lookup": tidy(name) or name,
            "cat": cat(name),
            "n": p.get("n") or 0,
            "when": f"first recorded {p['first']}" if p.get("first") else "",
            "what": name,
            "also": [v for v in (p.get("variants") or []) if v != name][:6],
            "people": [{"n": n} for n in names[:12]],
            "more": max(0, len(names) - 12) or None,
        })
    atlasdata.build(rows, os.path.join(HERE, "..", "site", "public", "atlas-data.json"),
                    countries=["United Kingdom","England","Scotland","Wales","London","Ireland","\u00c9ire",
                               "Australia","Barbados","Italia","Italy","France","Deutschland","Germany",
                               "Espa\u00f1a","Spain","Danmark","Denmark","Nederland","Netherlands"])

if __name__ == "__main__":
    sys.exit(main())

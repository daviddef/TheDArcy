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

# Places this archive has DOCUMENTED but the tree has never held. places.json is
# written from the GEDCOM, so a hamlet that appears only in thirteenth-century
# deeds is nowhere in it — and the atlas was therefore silent about the one
# place this archive spent a week proving the existence of. They are listed
# separately, and marked, so that nothing here can be mistaken for tree data.
DOCUMENTED = [
    # Only places that resolve to a coordinate of their OWN. Wanswell, Hinton
    # and Blakeney were tried and every one of them fell back to its parish's
    # point — three pins on Berkeley and one on Awre, all stamped "exact" by a
    # gazetteer that had simply not heard of them. That is false precision, and
    # a map that claims it is worse than a map that omits them.
    ("Saniger, Berkeley, Gloucestershire, England",
     "The hamlet the surname came from — on the king's highway from Longbridge "
     "by the mid-13th century, «Swonhunger ats Saniger» in Smyth's survey of "
     "about 1639, and Saniger Farm when Cooke wrote in 1882. THE POINT IS "
     "BERKELEY: the hamlet lies inside that parish and has no coordinate of "
     "its own. Wanswell and Hinton, its neighbours, are on the same point and "
     "are not shown separately for that reason.",
     1250, ["Swonhungre", "Swonhongre", "Swanhanger", "Swonhunger"],
     # The place page is built from this row, so the topography lives here
     # rather than two thirds of the way down a long page about a surname.
     [("mid 13th cent.", "The king's highway runs \u201cfrom LONGEBRUGGE to SWONHUNGER\u201d "
       "past a Berkeley messuage granted by Maurice lord of Berkeley \u00b7 BCM/A/1/12/92"),
      ("1287", "A croft \u201cin the west part of Berkel' towards Swonhungre called ALAGRENE "
       "STREET\u201d \u00b7 BCM/A/1/25/4"),
      ("1317", "Land in Ham \u201clying near Swonhungre, in the field called STODFOLD\u201d, a "
       "third held in dower by Joan Neel \u00b7 BCM/A/1/30/4"),
      ("25 April 1322", "A lease of one selion \u201cin the field called WESTFELD in the furlong "
       "called KYNGAKRE, beside the path from Berkel' to Swonhungre\u201d \u2014 and the deed is "
       "executed AT SANIGER, witnessed by William de Swonhungre \u00b7 BCM/A/1/24/261"),
      ("21 Dec. 1324", "Land in Lokedonne \u201cbeside the road from Berckel' to Swonhungre called "
       "LE MULEWEYE\u201d, the mill way \u00b7 BCM/A/1/65/12"),
      ("7 July 1325", "A croft \u201cin the field called LE WESTFELD beside the king's highway and "
       "the footpath from Berckel' to Swonhungre\u201d \u00b7 BCM/A/1/24/262"),
      ("about 1639", "Smyth lists the hamlets of Hamfallow: \u201cWike ats Wikes-elme, Wanefwell, "
       "SWONHUNGER ATS SANIGER, Halmer ats Ecton, and Egeton\u201d"),
      ("2 Nov. 1601", "JOHN SANIGER of Berkeley, yeoman, releases 3 acres of arable \u201cin "
       "WESTFIELD, SANIGER\u201d \u2014 the same field named in 1322 \u00b7 D2957/41/18"),
      ("1774", "\u201cSaniger Farm\u2026 was sold by EDWARD SANIGER to the Earl of Berkeley\u201d, "
       "according to J. H. Cooke in 1882. The deed has not been found.")]),

]


# TWO QUESTIONS OF THE SAME GROUND — 21 September 2026.
#
# The kit's Atlas has carried a `schemes` prop since Defranceschi's layer
# model was promoted into it, and until this week no archive passed it.
#
#   people  where a named person can be put — the category this file had
#   ground  where somebody is actually buried, out of graves.json
#
# HOW A GRAVE FINDS ITS PLACE, AND WHAT IS REFUSED. graves.json records a
# burial as prose: "Toowong Cemetery, Toowong, Brisbane, Queensland (Port. 4,
# Sect. 35, Grave 3-4)". There is no structured place field, so the join
# reads the comma-parts LEFT TO RIGHT and takes the first that is already a
# place on this map — the most specific one it can honour.
#
# Broad administrative names are REFUSED even when they are on the map.
# Matching "Queensland" would land sixteen specific burials on a state pin
# and "England" another eight, and a Brisbane grave shown in the middle of
# Queensland is worse than a grave not shown: the first is wrong and looks
# right. 41 of 89 rows land on a specific place; the other 48 are named
# under the map rather than guessed at.
BROAD = {"queensland", "england", "australia", "united kingdom", "uk",
         "scotland", "wales", "ireland", "new south wales", "victoria",
         "usa", "united states"}

def grave_places(known):
    """place-head -> (grave rows, people buried). Many rows fold onto one
       place, so this COUNTS. An `=` here would make the last row in the file
       decide what a place says — see kit/docs/traps.md, «A fold needs a rule»."""
    rows_, ppl = {}, {}
    data = J("graves.json")
    for r in (data if isinstance(data, list) else data.get("rows") or []):
        bare = re.sub(r"\([^)]*\)", "", str(r.get("place") or ""))
        parts = [x.strip().lower() for x in bare.split(",") if x.strip()]
        hit = next((p for p in parts if p in known and p not in BROAD), None)
        if not hit:
            continue
        rows_[hit] = rows_.get(hit, 0) + 1
        ppl[hit] = ppl.get(hit, 0) + len(r.get("people") or [])
    return rows_, ppl


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
    for entry in DOCUMENTED:
        name, what, first, also = entry[0], entry[1], entry[2], entry[3]
        evts = entry[4] if len(entry) > 4 else []
        if any(r["what"] == name for r in rows):
            continue
        rows.append({
            "name": name.split(",")[0].strip(),
            "_lookup": tidy(name) or name,
            "cat": cat(name),
            "n": 0,
            "when": f"documented from {first}",
            "what": what,
            "also": also,
            "people": [],
            "more": None,
            "events": [list(e) for e in evts],
        })

    # The layers, attached on the same head() every other join here uses.
    known = {r["name"].split(",")[0].strip().lower() for r in rows}
    gr, gp = grave_places(known)
    # ONE HEAD CAN BE SEVERAL ROWS ON THIS MAP, AND THAT IS ITS OWN PROBLEM.
    # Twenty heads appear more than once — "Brisbane", "Brisbane, Queensland"
    # and "Brisbane, Queensland, Australia" are three rows — and four of them
    # sit at different coordinates, Toowoomba twice six hundred kilometres
    # apart. Giving every row with the head its burials counted the same
    # twenty graves three times over. The layer attaches to ONE row per head,
    # the one holding the most people, so a count on the map is a count of
    # something. The duplication itself is a data question and is left alone.
    principal = {}
    for i, r in enumerate(rows):
        h = r["name"].split(",")[0].strip().lower()
        best = principal.get(h)
        if best is None or (r.get("n") or 0) > (rows[best].get("n") or 0):
            principal[h] = i
    for i, r in enumerate(rows):
        h = r["name"].split(",")[0].strip().lower()
        cats = {}
        if r.get("n"):
            cats["people"] = r["cat"]
        if h in gr and principal.get(h) == i:
            cats["ground"] = "ground"
        if cats:
            r["cats"] = cats
            ns = {}
            if r.get("n"):
                ns["people"] = r["n"]
            if h in gr and principal.get(h) == i:
                ns["ground"] = gp[h]
            r["ns"] = ns

    atlasdata.build(rows, os.path.join(HERE, "..", "site", "public", "atlas-data.json"),
                    countries=["United Kingdom","England","Scotland","Wales","London","Ireland","\u00c9ire",
                               "Australia","Barbados","Italia","Italy","France","Deutschland","Germany",
                               "Espa\u00f1a","Spain","Danmark","Denmark","Nederland","Netherlands"])

if __name__ == "__main__":
    sys.exit(main())

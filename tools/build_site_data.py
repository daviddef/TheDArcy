#!/usr/bin/env python3
"""Turn the parsed GEDCOM into the JSON the site reads.

The living-person standard is applied here, once, at the boundary between the
research data and the published build. Anything that reaches site/src/data has
already been through it.

THE STANDARD (David's ruling, 16 October 2026, made knowing the tree holds 2,034
people it judges living): a living person is published as a NAME, a RELATIONSHIP
and a TOWN AND COUNTRY, and nothing else. living_json() below builds them from
those and from nothing more: it never reads a date, an event, a note, a source,
an occupation or a cause, so none of them can reach a committed file. This used
to build the whole record and blank it afterwards (redact()); a record that is
built and then blanked is one forgotten field away from published.
"""
import json, os, collections, re
from gedcom import (load, display, born, died, year, ev, lifespan, classify_living)

# Filled in by main(). One graph-wide judgement, used everywhere below, so that
# a person cannot be living on one page and dead on another.
LIVING = {}

# Filled in by main(): everybody this archive gives a PAGE — the 243 numbered
# ancestors and every member of the thirteen surname clusters. A living person
# in SCOPE has a page; a living person outside it is named, as a spouse or a
# brother or sister, and is neither linked nor given an identifier.
SCOPE = set()

# Every living person who appears ANYWHERE in what this run writes, as the
# subject of a record or as a relative named in one. Ids only, never written
# out: they exist so the published counts are measured rather than typed.
APPEARS = set()


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
    # British abbreviations the tree uses. Only unambiguous ones: a country
    # cannot be mistaken for anything else, and "Som." with its stop is a
    # county. "Ayr" is deliberately NOT here — it is both a town and a county,
    # and merging it would be a guess rather than an expansion.
    "sctl": "Scotland", "scot": "Scotland", "eng": "England",
    "engl": "England", "irl": "Ireland", "wls": "Wales",
    "som.": "Somerset", "som": "Somerset", "glos": "Gloucestershire",
    "hants": "Hampshire", "staffs": "Staffordshire",
}


def canonical_place(p):
    """Collapse the tree's spelling variants so a count counts places.

    Only four things are done, all of them safe: a leading "of " is dropped,
    repeated adjacent parts are dropped ("Brisbane, Brisbane, Queensland"),
    state abbreviations are expanded, and casing is tidied. Nothing is merged
    that is not literally the same place.

    The "of " is a genealogist's convention meaning residence rather than an
    event — "of St Quivox" is where a man was FROM. Left in, it makes a second
    place: the gazetteer carried "St Quivox, Ayrshire, Scotland", "of St Quivox,
    Ayrshire, Scotland" and "of St Quivox, Ayr, Sctl" as three entries of one
    record each, instead of one place with three. Found by tools/agree.py on
    15 September 2026, which reported one man born in two places.
    """
    p = re.sub(r"^\s*(?:of|at|in|the)\s+", "", p, flags=re.I)
    parts = [x.strip() for x in re.split(r"\s*,\s*", p) if x.strip()]
    out = []
    for x in parts:
        low = x.lower().rstrip(".")     # "Eng." and "Eng" are one abbreviation
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


# ---- town and country --------------------------------------------------------
# The place a living person is shown with. It comes from the one place the tree
# records for them, the place of birth, and is REDUCED to a town and a country:
# a street, a hospital, a farm, a house number, a county or a state is dropped.
# The tree holds no residence for any living person, so there is nothing newer.
COUNTRY = {
    "south africa": "South Africa", "rsa": "South Africa", "s africa": "South Africa",
    "australia": "Australia", "england": "England", "scotland": "Scotland",
    "wales": "Wales", "ireland": "Ireland", "northern ireland": "Northern Ireland",
    "united kingdom": "United Kingdom", "uk": "United Kingdom",
    "usa": "United States", "united states": "United States",
    "united states of america": "United States", "us": "United States",
    "canada": "Canada", "new zealand": "New Zealand", "croatia": "Croatia",
    "hrvatska": "Croatia", "italy": "Italy", "italia": "Italy", "serbia": "Serbia",
    "germany": "Germany", "deutschland": "Germany", "france": "France",
    "zimbabwe": "Zimbabwe", "zambia": "Zambia", "namibia": "Namibia",
    "botswana": "Botswana", "kenya": "Kenya", "mozambique": "Mozambique",
    "puerto rico": "Puerto Rico", "venezuela": "Venezuela", "brazil": "Brazil",
    "brasil": "Brazil", "argentina": "Argentina", "chile": "Chile", "peru": "Peru",
    "mexico": "Mexico", "spain": "Spain", "portugal": "Portugal",
    "netherlands": "Netherlands", "belgium": "Belgium", "switzerland": "Switzerland",
    "austria": "Austria", "poland": "Poland", "slovenia": "Slovenia",
    "bosnia and herzegovina": "Bosnia and Herzegovina", "greece": "Greece",
    "israel": "Israel", "india": "India", "china": "China", "japan": "Japan",
    "singapore": "Singapore", "hong kong": "Hong Kong", "thailand": "Thailand",
    "dubai": "United Arab Emirates", "united arab emirates": "United Arab Emirates",
    "sweden": "Sweden", "norway": "Norway", "denmark": "Denmark", "finland": "Finland",
    "russia": "Russia", "ukraine": "Ukraine", "hungary": "Hungary",
    "czech republic": "Czech Republic", "romania": "Romania", "bulgaria": "Bulgaria",
    "lesotho": "Lesotho", "swaziland": "Eswatini", "eswatini": "Eswatini",
    "malawi": "Malawi", "angola": "Angola", "uruguay": "Uruguay",
    "colombia": "Colombia", "ecuador": "Ecuador", "cuba": "Cuba",
}
# A first component that is a building or a road is not a town.
NOT_A_TOWN = re.compile(
    r"\b(hospital|clinic|nursing|maternity|medical|infirmary|farm|ranch|station|"
    r"street|st\.|road|rd\.?|avenue|ave|drive|lane|court|crescent|place|house|"
    r"school|university|college|church|chapel|prison|barracks|lodge|home|estate|"
    r"po box|private bag)\b", re.I)
# State and province tokens that survive when the tree wrote a place without commas.
STATE_TOKENS = {"qld", "q'ld", "nsw", "vic", "wa", "sa", "tas", "nt", "act",
                "queensland", "new south wales", "victoria", "tasmania",
                "western australia", "south australia", "northern territory"} | {
    # a state or province is coarser than a town, and is not offered as one
    x.lower() for x in (
        "Alabama,Alaska,Arizona,Arkansas,California,Colorado,Connecticut,Delaware,Florida,"
        "Georgia,Hawaii,Idaho,Illinois,Indiana,Iowa,Kansas,Kentucky,Louisiana,Maine,Maryland,"
        "Massachusetts,Michigan,Minnesota,Mississippi,Missouri,Montana,Nebraska,Nevada,"
        "New Hampshire,New Jersey,New Mexico,New York,North Carolina,North Dakota,Ohio,Oklahoma,"
        "Oregon,Pennsylvania,Rhode Island,South Carolina,South Dakota,Tennessee,Texas,Utah,"
        "Vermont,Virginia,Washington,West Virginia,Wisconsin,Wyoming,"
        "Ontario,Quebec,British Columbia,Alberta,Manitoba,Saskatchewan,Nova Scotia,"
        "Gauteng,KwaZulu-Natal,Western Cape,Eastern Cape,Free State,Limpopo,Mpumalanga,"
        "North West,North West Province,Northern Cape,Transvaal,Natal,Cape Province"
    ).split(",")}


def _tidy_case(x):
    x = x.strip(" ,.;")
    return x.title() if x and x == x.lower() else x


def town_country(raw):
    """"Johannesburg, Gauteng, South Africa" -> "Johannesburg, South Africa".

    Returns "" when the tree has no place, or none that survives the reduction.
    A place with a country and no usable town is the country alone; a place with
    a town and no country the tree names is the town alone."""
    raw = re.sub(r"&lt;|&gt;|[<>]", "", raw or "").strip()
    if not raw:
        return ""
    # Anything carrying a digit or a question mark is an address or a guess.
    parts = [x.strip() for x in re.split(r"\s*,\s*", canonical_place(raw)) if x.strip()]
    country = ""
    if len(parts) == 1:
        # "Brisbane Qld Australia": no commas. Peel a trailing country, then states.
        words = parts[0].split()
        for n in (3, 2, 1):
            if len(words) > n - 1 and " ".join(words[-n:]).lower() in COUNTRY:
                country = COUNTRY[" ".join(words[-n:]).lower()]
                words = words[:-n]
                break
        while words and words[-1].lower().strip(".") in STATE_TOKENS:
            words = words[:-1]
        parts = [" ".join(words)] if words else []
    elif parts and parts[-1].lower() in COUNTRY:
        country = COUNTRY[parts[-1].lower()]
        parts = parts[:-1]
    town = ""
    for x in parts:
        if re.search(r"\d|\?", x) or NOT_A_TOWN.search(x) or x.lower() in STATE_TOKENS \
                or x.lower() in COUNTRY:
            continue
        town = _tidy_case(x)
        break
    return ", ".join(x for x in (town, country) if x)


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


def alive(pid, people):
    return pid in people and is_living(people[pid])


def kept_child(c, people):
    """A child is listed on a parent's marriage when somebody can follow the link.

    The dead are listed as they always were. A living child is listed only if
    this archive gives them a page of their own (they are in SCOPE), because a
    child's id is the one thing in that list a reader's page can resolve, and an
    id with no page behind it is a living person's identifier published for
    nothing. A living child with no page still appears by NAME wherever a list of
    names is drawn (a sibling list, a household); this is only the link list."""
    if c not in people:
        return False
    return (not is_living(people[c])) or c in SCOPE


def spouses(people, families, pid):
    out = []
    me_alive = alive(pid, people)
    for fid in people[pid]["fams"]:
        f = families.get(fid)
        if not f:
            continue
        other = f["wife"] if f["husb"] == pid else f["husb"]
        other_alive = alive(other, people)
        if other_alive:
            APPEARS.add(other)
        # A marriage is a date about BOTH of its people. If either is living the
        # date, the place and any divorce are a fact about a living person, and
        # are not published.
        hidden = me_alive or other_alive
        m = {} if hidden else next((e for e in f["events"] if e["kind"] == "marriage"), {})
        d = {} if hidden else next((e for e in f["events"] if e["kind"] == "divorce"), {})
        rec = {
            # A living spouse is NAMED. They are linked only if they have a page.
            "name": display(people[other]) if other in people else "",
            "id": other if (not other_alive or other in SCOPE) else "",
            "living": other_alive,
            "married": m.get("date", ""),
            "marriedPlace": m.get("place", ""),
            "divorced": d.get("date", ""),
            "children": [_note(c, people) for c in f["chil"] if kept_child(c, people)],
        }
        if other_alive:
            rec["place"] = town_country(born(people[other]).get("place", ""))
        out.append(rec)
    return out


def _note(pid, people):
    if alive(pid, people):
        APPEARS.add(pid)
    return pid


def parent_names(people, pid):
    return [display(people[_note(x, people)]) for x in people[pid]["parents"] if x in people]


def sibling_names(people, families, pid):
    return sorted({
        display(people[_note(c, people)])
        for fid in people[pid].get("famc", [])
        for c in families.get(fid, {}).get("chil", [])
        if c != pid and c in people
    })


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
        # A living parent is named, and nothing else about them is.
        "parents": parent_names(people, pid),
        # Brothers and sisters: the other children of whichever family this
        # person is a child of. Mechanical — the GEDCOM carries 4,777 families
        # and 11,630 child links — and the reason the blood chart can show
        # ancestors and aunts and uncles.
        # A living brother or sister is NAMED here, as the standard says, and
        # nothing else about them is: this is a list of names.
        "siblings": sibling_names(people, families, pid),
        "sources": p["sources"][:6],
        "notes": p["notes"],
        "living": False,
    }


def living_json(people, families, pid, ahn=None):
    """A living person: a name, a relationship, a town and a country. Nothing else.

    BUILT FROM THOSE AND NOTHING MORE. This does not call person_json() and blank
    the result; it never reads a date, an event, a note, a source, an occupation,
    a cause, a burial or an alternative name. The one event it touches is the
    place of birth, and only to reduce it to a town and a country (town_country).
    Relationships are names, plus an id where the relative has a page here.

    The empty strings are not leftovers: the pages and the kit's components read
    these keys on every record, and a missing key is an error in one of them
    and a "undefined" on the page in another. tools/check_living.py reads the
    keys of every living record against LIVING_KEYS and refuses any other.
    """
    p = people[pid]
    APPEARS.add(pid)
    return {
        "id": pid, "mh": "",
        "name": display(p) or "\u2014", "surname": p["surname"], "sex": p["sex"],
        "ahn": ahn, "gen": gen_of(ahn) if ahn else None,
        "born": "", "bornPlace": "", "died": "", "diedPlace": "",
        "cause": "", "burial": "", "occupation": "", "life": "",
        "place": town_country(born(p).get("place", "")),
        "spouses": spouses(people, families, pid),
        "parents": parent_names(people, pid),
        "siblings": sibling_names(people, families, pid),
        "sources": [], "notes": [],
        "living": True,
    }


# The keys a living record may carry, and no others. Mirrored in
# tools/check_living.py, which checks the committed data against it.
LIVING_KEYS = {
    "id", "mh", "name", "surname", "sex", "ahn", "gen", "born", "bornPlace", "died",
    "diedPlace", "cause", "burial", "occupation", "life", "place", "spouses",
    "parents", "siblings", "sources", "notes", "living",
}


def record(people, families, pid, ahn=None):
    """The one door. Whoever is living goes through living_json and never
    through person_json, so a field added to person_json later cannot reach one."""
    if is_living(people[pid]):
        return living_json(people, families, pid, ahn)
    return person_json(people, families, pid, ahn)


def write_counts(people, anc, fam_out):
    """Measure what this run published of the living, and write the numbers —
    only numbers — into living.json, where the pages read them. A page that
    typed these figures would drift the first time the tree moved."""
    pages = {r["id"] for r in anc if r["living"]}
    for f in fam_out:
        pages |= {m["id"] for m in f["members"] if m["living"]}
    recs = [r for r in anc if r["living"]] + \
           [m for f in fam_out for m in f["members"] if m["living"]]
    seen, uniq = set(), []
    for r in recs:
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    countries = set(COUNTRY.values())
    town = sum(1 for r in uniq if r["place"] and r["place"] not in countries)
    country_only = sum(1 for r in uniq if r["place"] and r["place"] in countries)
    pub = {
        "withPage": len(pages),
        "namedOnly": len(APPEARS - pages),
        "named": len(APPEARS),
        "withTown": town,
        "countryOnly": country_only,
        "noPlace": len(uniq) - town - country_only,
        "onDirectLine": sum(1 for r in anc if r["living"]),
    }
    path = os.path.join(OUT, "living.json")
    decl = json.load(open(path, encoding="utf-8"))
    decl["published"] = pub
    decl["publishedNote"] = ("Written by tools/build_site_data.py on every build: how many "
                             "living people this run put into the data, counted not typed. "
                             "withPage have a page; namedOnly appear only by name, as a spouse, "
                             "brother, sister or parent. Numbers only, never a name.")
    json.dump(decl, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return pub


def main():
    global LIVING
    people, families = load()
    LIVING = classify_living(people, families)
    os.makedirs(OUT, exist_ok=True)
    by_ahn = ancestors(people, families, CRISTINA)
    APPEARS.clear()
    SCOPE.clear()
    SCOPE.update(by_ahn.values())
    for sn, _ in FAMILIES:
        SCOPE.update(p["id"] for p in people.values()
                     if p["surname"].lower() == sn.lower())

    # ---- every ancestor; the living through living_json -----------------
    anc = []
    for ahn, pid in sorted(by_ahn.items()):
        anc.append(record(people, families, pid, ahn))
    json.dump(anc, open(os.path.join(OUT, "ancestors.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- the male D'Arcy spine ------------------------------------------
    spine, ahn = [], 1
    while ahn in by_ahn:
        spine.append(record(people, families, by_ahn[ahn], ahn))
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
            recs.append(record(people, families, m["id"]))
        fam_out.append({
            "surname": sn, "blurb": blurb,
            "total": len(recs),
            # Everyone of the name now has a place here, the living by name,
            # town and country. `living` says how many of them.
            "published": len(recs),
            "living": sum(1 for r in recs if r["living"]),
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

    write_counts(people, anc, fam_out)

    living = sum(1 for r in anc if r["living"])
    print(f"ancestors.json  {len(anc)} ({living} living: name, relationships, town and country)")
    print(f"line.json       {len(spine)} generations")
    print(f"families.json   {len(fam_out)} surnames, "
          f"{sum(f['total'] for f in fam_out)} people, "
          f"{sum(f['living'] for f in fam_out)} living")
    print(f"places.json     {len(places)} places")


if __name__ == "__main__":
    main()

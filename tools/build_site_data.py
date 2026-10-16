#!/usr/bin/env python3
"""Turn the parsed GEDCOM into the JSON the site reads.

The living-person standard is applied here, once, at the boundary between the
research data and the published build. Anything that reaches site/src/data has
already been through it.

THE STANDARD (David's ruling, 16 October 2026, version 2): a living person is
published as a NAME, a RELATIONSHIP and a TOWN AND COUNTRY, and nothing else.
Who is living is not decided here: tools/gedcom.py prepares a birth year, a
recorded death and the citations, and the kit's living_rule.py decides (80 years
or younger by year with no death recorded and no public source; a person with
no birth year is not living). living_json() below builds a living person from
the name, the relationships and the birth PLACE, and never reads a date, an
event, a note, a source, an occupation or a cause, so none of them can reach a
committed file. This used to build the whole record and blank it afterwards; a
record that is built and then blanked is one forgotten field away from published.

EVERY PERSON THE ARCHIVE NAMES HAS A PAGE. The archive gives a page to the 243
numbered ancestors and to every bearer of the thirteen surnames (SCOPE). The
parents, brothers and sisters and spouses those people are shown with are NAMED,
so each of them is given a page too (RELATIVES, written to relatives.json). A
relative's own relatives are named on their page only where they have a page
already, so naming stops there: the tree holds thousands of people the archive
never names, and they stay unpublished.
"""
import json, os, collections, re
from gedcom import (load, display, born, died, year, ev, lifespan, classify_living,
                    held_out)

# Filled in by main(). One graph-wide judgement, used everywhere below, so that
# a person cannot be living on one page and dead on another.
LIVING = {}

# Filled in by main(): everybody this archive gives a page by right — the 243
# numbered ancestors and every member of the thirteen surname clusters.
SCOPE = set()

# Filled in by main(): SCOPE plus the relatives it names. None means "not yet
# decided", and then nobody is left out of a list of relatives.
PAGES = None


def is_living(p):
    return LIVING.get(p["id"], False)


# HELD OUT (David's ruling, 16 October 2026): a person this archive does not
# publish at all. No page, no record, and no name as anybody's relative. The rule
# is the kit's (living_rule.is_held_out, through gedcom.held_out()) so that this
# build, tools/ancestry.py and the gates cannot disagree about it. Every place
# below that names a relative goes through held(). HELD_SEEN counts, and never
# names, how many held-out people the build met while looking for relatives.
HELD = {}
HELD_SEEN = set()


def held(pid):
    if pid in HELD:
        HELD_SEEN.add(pid)
        return True
    return False


def decide_held(people):
    HELD.clear()
    HELD_SEEN.clear()
    HELD.update(held_out(people, LIVING))


def named(pid):
    """May this person be named as somebody's relative? Not if held out, and not
    if they would have no page."""
    return not held(pid) and (PAGES is None or pid in PAGES)

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


# A state or province names its country, so a place written «Toowoomba QLD» is
# Toowoomba, Australia. Used only when the tree gives no country of its own.
_AUS = {"qld", "q'ld", "nsw", "vic", "wa", "sa", "tas", "nt", "act", "queensland",
        "queenland", "new south wales", "victoria", "tasmania", "western australia",
        "south australia", "northern territory"}
_SA = {x.lower() for x in ("Gauteng,KwaZulu-Natal,Western Cape,Eastern Cape,Free State,Limpopo,"
                           "Mpumalanga,North West,North West Province,Northern Cape,Transvaal,"
                           "Natal,Cape Province").split(",")}
_CA = {x.lower() for x in ("Ontario,Quebec,British Columbia,Alberta,Manitoba,Saskatchewan,"
                           "Nova Scotia").split(",")}


def _state_country(tok):
    t = tok.lower().strip(".")
    if t in _AUS:
        return "Australia"
    if t in _SA:
        return "South Africa"
    if t in _CA:
        return "Canada"
    if t in STATE_TOKENS:
        return "United States"
    return ""


def town_country(raw):
    """"Johannesburg, Gauteng, South Africa" -> "Johannesburg, South Africa".

    The place a living person is shown with: the TOWN OR CITY and the COUNTRY, in
    full, and never a street, an address, an institution, a county or a state.
    Returns "" when the tree has no place, or none that survives the reduction.
    A place with a country and no usable town is the country alone; a place with
    a town and no country the tree names is the town alone, unless a state or
    province in it names the country."""
    raw = re.sub(r"&lt;|&gt;|[<>]", "", raw or "").strip()
    if not raw:
        return ""
    parts = [x.strip() for x in re.split(r"\s*,\s*", canonical_place(raw)) if x.strip()]
    country, state_hint = "", ""
    if len(parts) == 1:
        # "Brisbane Qld Australia": no commas. Peel a trailing country, then states.
        words = parts[0].split()
        for n in (3, 2, 1):
            if len(words) > n - 1 and " ".join(words[-n:]).lower() in COUNTRY:
                country = COUNTRY[" ".join(words[-n:]).lower()]
                words = words[:-n]
                break
        while words and words[-1].lower().strip(".") in STATE_TOKENS:
            state_hint = state_hint or words[-1]
            words = words[:-1]
        parts = [" ".join(words)] if words else []
    elif parts and parts[-1].lower() in COUNTRY:
        country = COUNTRY[parts[-1].lower()]
        parts = parts[:-1]
    town = ""
    for x in parts:
        if x.lower() in STATE_TOKENS:
            state_hint = state_hint or x
    for x in parts:
        if re.search(r"\d|\?", x) or NOT_A_TOWN.search(x) or x.lower() in STATE_TOKENS \
                or x.lower() in COUNTRY:
            continue
        town = _tidy_case(x)
        break
    if not country and state_hint:
        country = _state_country(state_hint)
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


def relatives_of(people, families, pid):
    """Everybody the archive NAMES beside this person: their parents, their
    brothers and sisters (half-siblings included) and their spouses. Held-out
    people are not here. Children are not named by this archive and are not here."""
    p = people[pid]
    out = []

    def add(x):
        if x and x != pid and x in people and x not in out:
            out.append(x)
    for x in p["parents"]:
        add(x)
    for fid in p.get("famc", []):
        for c in families.get(fid, {}).get("chil", []):
            add(c)
    for fid in p["fams"]:
        f = families.get(fid)
        if f:
            add(f["wife"] if f["husb"] == pid else f["husb"])
    return [x for x in out if x not in HELD]


def kept_child(c, people):
    """A child is listed on a parent's marriage when somebody can follow the link:
    they have a page. A child with no page is not named and is not listed."""
    return c in people and not held(c) and (PAGES is None or c in PAGES)


def spouses(people, families, pid):
    out = []
    me_alive = alive(pid, people)
    for fid in people[pid]["fams"]:
        f = families.get(fid)
        if not f:
            continue
        other = f["wife"] if f["husb"] == pid else f["husb"]
        if other and held(other):
            continue                         # not named, and no row to show they exist
        kids = [c for c in f["chil"] if kept_child(c, people)]
        # The tree can hold a marriage and never have held the person (a spouse
        # record with an id, children and NO name): that marriage is kept, with
        # the name left empty. A spouse who has no page here is not named either,
        # and then the marriage is kept only for the children it carries.
        spouse_named = bool(other) and other in people and named(other)
        if other in people and not spouse_named and not kids:
            continue
        other_alive = spouse_named and alive(other, people)
        # A marriage is a date about BOTH of its people. If either is living the
        # date, the place and any divorce are a fact about a living person, and
        # are not published.
        hidden = me_alive or other_alive
        m = {} if hidden else next((e for e in f["events"] if e["kind"] == "marriage"), {})
        d = {} if hidden else next((e for e in f["events"] if e["kind"] == "divorce"), {})
        rec = {
            "name": display(people[other]) if spouse_named else "",
            "id": other if spouse_named else "",
            "living": other_alive,
            "married": m.get("date", ""),
            "marriedPlace": m.get("place", ""),
            "divorced": d.get("date", ""),
            "children": kids,
        }
        if other_alive:
            rec["place"] = town_country(born(people[other]).get("place", ""))
        out.append(rec)
    return out


def parent_refs(people, pid):
    """Parents, by name and id: the id is what lets a page link the name."""
    return [{"name": display(people[x]), "id": x} for x in people[pid]["parents"]
            if x in people and named(x)]


def sibling_refs(people, families, pid):
    ids = []
    for fid in people[pid].get("famc", []):
        for c in families.get(fid, {}).get("chil", []):
            if c != pid and c in people and c not in ids and named(c):
                ids.append(c)
    return sorted(({"name": display(people[c]), "id": c} for c in ids),
                  key=lambda r: (r["name"], r["id"]))


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
        "surname": p["surname"].replace("*", "").strip(),
        "sex": p["sex"],
        "ahn": ahn,
        "gen": gen_of(ahn) if ahn else None,
        "born": b.get("date", ""), "bornPlace": b.get("place", ""),
        "died": d.get("date", ""), "diedPlace": d.get("place", ""),
        "cause": d.get("cause", ""),
        "burial": bur.get("place", ""),
        "occupation": occupation(p),
        "life": lifespan(p),
        "spouses": spouses(people, families, pid),
        "parents": parent_refs(people, pid),
        # Brothers and sisters: the other children of whichever family this
        # person is a child of, half-siblings included.
        "siblings": sibling_refs(people, families, pid),
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
    Relationships are names with the id of the page each has here.

    The empty strings are not leftovers: the pages and the kit's components read
    these keys on every record, and a missing key is an error in one of them
    and a "undefined" on the page in another. tools/check_living.py reads the
    keys of every living record against LIVING_KEYS and refuses any other.
    """
    p = people[pid]
    return {
        "id": pid, "mh": "",
        "name": display(p) or "\u2014", "surname": p["surname"].replace("*", "").strip(), "sex": p["sex"],
        "ahn": ahn, "gen": gen_of(ahn) if ahn else None,
        "born": "", "bornPlace": "", "died": "", "diedPlace": "",
        "cause": "", "burial": "", "occupation": "", "life": "",
        "place": town_country(born(p).get("place", "")),
        "spouses": spouses(people, families, pid),
        "parents": parent_refs(people, pid),
        "siblings": sibling_refs(people, families, pid),
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


def write_counts(people, recs, held_in_tree):
    """Measure what this run published of the living, and write the numbers —
    only numbers — into living.json, where the pages read them. A page that
    typed these figures would drift the first time the tree moved."""
    uniq = list({r["id"]: r for r in recs if r["living"]}.values())
    countries = set(COUNTRY.values())
    town = sum(1 for r in uniq if r["place"] and r["place"] not in countries)
    country_only = sum(1 for r in uniq if r["place"] and r["place"] in countries)
    pub = {
        "withPage": len(uniq),
        "namedOnly": 0,          # every person named has a page; none is named without one
        "named": len(uniq),
        "withTown": town,
        "countryOnly": country_only,
        "noPlace": len(uniq) - town - country_only,
        "onDirectLine": sum(1 for r in recs if r["living"] and r.get("ahn")),
        "relativesWithPage": sum(1 for r in recs if r.get("_rel")),
        "livingRelativesWithPage": sum(1 for r in recs if r["living"] and r.get("_rel")),
    }
    by_rule = collections.Counter(HELD.values())
    seen_rule = collections.Counter(HELD[x] for x in HELD_SEEN)
    pub["heldOut"] = {
        "dnaTester": seen_rule.get("dna-tester", 0),
        "possibleMinors": seen_rule.get("possible-minor", 0),
        "total": len(HELD_SEEN),
        "possibleMinorsInTree": by_rule.get("possible-minor", 0),
    }
    path = os.path.join(OUT, "living.json")
    decl = json.load(open(path, encoding="utf-8"))
    decl["published"] = pub
    decl["publishedNote"] = ("Written by tools/build_site_data.py on every build: how many "
                             "living people this run put into the data, counted not typed. "
                             "Every living person published has a page; heldOut are people left "
                             "out altogether (see decisions.json). Numbers only, never a name.")
    json.dump(decl, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return pub


def by_birth(r, people):
    return (year(born(people[r]).get("date", "")) or 9999, display(people[r]), r)


def main():
    global LIVING, PAGES
    people, families = load()
    LIVING = classify_living(people, families)
    decide_held(people)
    PAGES = None
    os.makedirs(OUT, exist_ok=True)
    by_ahn = ancestors(people, families, CRISTINA)
    on_line = [pid for pid in by_ahn.values() if pid in HELD]
    if on_line:
        # The direct line cannot lose a person without breaking its numbering.
        # None is held today; if one is, that is a decision for David, not a gap.
        raise SystemExit(f"{len(on_line)} held-out person(s) sit on the direct line; "
                         "the archive cannot be built around the gap")
    SCOPE.clear()
    SCOPE.update(by_ahn.values())
    for sn, _ in FAMILIES:
        SCOPE.update(p["id"] for p in people.values()
                     if p["surname"].lower() == sn.lower() and p["id"] not in HELD)

    # ---- who else is NAMED, and so is given a page ---------------------------
    # The parents, brothers and sisters and spouses of everybody SCOPE holds. They
    # are named beside those people (a relative on a page, a card on the spine, a
    # chart node), and a name with no page behind it is not allowed. Their own
    # relatives are not named further: a relative's page lists only people who
    # have a page already.
    rel_ids = set()
    for pid in SCOPE:
        rel_ids.update(relatives_of(people, families, pid))
    rel_ids -= SCOPE
    PAGES = SCOPE | rel_ids

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
        of_name = [p for p in people.values() if p["surname"].lower() == sn.lower()]
        members = [p for p in of_name if not held(p["id"])]
        members.sort(key=lambda p: year(born(p).get("date", "")) or 9999)
        recs = []
        for m in members:
            recs.append(record(people, families, m["id"]))
        fam_out.append({
            "surname": sn, "blurb": blurb,
            # Everyone of the name in the tree; `published` is who is given a
            # place here. The two differ only by the people held out.
            "total": len(of_name),
            "published": len(recs),
            "living": sum(1 for r in recs if r["living"]),
            "members": recs,
        })
    json.dump(fam_out, open(os.path.join(OUT, "families.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- the relatives: named beside someone, given a page of their own ----
    rel_out = [record(people, families, pid)
               for pid in sorted(rel_ids, key=lambda x: by_birth(x, people))]
    json.dump(rel_out, open(os.path.join(OUT, "relatives.json"), "w"),
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

    allrecs = anc + [m for f in fam_out for m in f["members"]] + [dict(r, _rel=True) for r in rel_out]
    write_counts(people, allrecs, len(HELD))

    living = sum(1 for r in anc if r["living"])
    print(f"ancestors.json  {len(anc)} ({living} living: name, relationships, town and country)")
    print(f"line.json       {len(spine)} generations")
    print(f"families.json   {len(fam_out)} surnames, "
          f"{sum(f['total'] for f in fam_out)} people, "
          f"{sum(f['living'] for f in fam_out)} living")
    print(f"relatives.json  {len(rel_out)} people named beside someone and given a page "
          f"({sum(1 for r in rel_out if r['living'])} living)")
    print(f"places.json     {len(places)} places")


if __name__ == "__main__":
    main()

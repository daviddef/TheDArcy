#!/usr/bin/env python3
"""Parse the MyHeritage GEDCOM into a person/family graph the rest of the
archive can walk.

One module, no dependencies. Everything downstream — the ancestry sweep, the
surname clusters, the register — imports `load()` from here so that there is
exactly one place where a GEDCOM line is turned into a fact.
"""
import re, os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GED = os.path.join(ROOT, "sources", "myheritage-tree4-2026-09-09.ged")

# THE ONE DEFINITION OF WHO IS LIVING lives in the shared kit, not here
# (David, 16 October 2026): kit/tools/living_rule.py and kit/data/public-sources.json.
# This archive used to keep its own test (a 100-year upper bound inferred through
# the family graph); it keeps none now. Everything below only PREPARES the
# facts the kit's functions take (a birth year, whether the tree records a death,
# the citations) and hands them over.
_KIT_TOOLS = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools")
if _KIT_TOOLS not in sys.path:
    sys.path.insert(0, _KIT_TOOLS)
import living_rule as lr

LINE = re.compile(r"^\s*(\d+)\s+(?:(@[^@]+@)\s+)?(_?\w+)(?:\s(.*))?$")

# The event tags we keep, and the label each gets in the output.
EVENTS = {
    "BIRT": "birth", "DEAT": "death", "BURI": "burial", "CHR": "christening",
    "BAPM": "baptism", "MARR": "marriage", "DIV": "divorce", "RESI": "residence",
    "OCCU": "occupation", "EDUC": "education", "IMMI": "immigration",
    "EMIG": "emigration", "NATU": "naturalisation", "CENS": "census",
    "PROB": "probate", "WILL": "will", "RETI": "retirement", "EVEN": "event",
    "MILT": "military", "_MILT": "military", "GRAD": "graduation",
}


class Node:
    """One GEDCOM record, kept as a tree of tags so nothing is silently dropped."""
    __slots__ = ("tag", "xref", "value", "kids")

    def __init__(self, tag, xref=None, value=""):
        self.tag, self.xref, self.value, self.kids = tag, xref, value, []

    def all(self, tag):
        return [k for k in self.kids if k.tag == tag]

    def first(self, tag):
        for k in self.kids:
            if k.tag == tag:
                return k
        return None

    def val(self, tag, default=""):
        k = self.first(tag)
        return k.value if k else default


def parse(path=GED):
    """Read the file into a list of level-0 records."""
    records, stack = [], []
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            m = LINE.match(line)
            if not m:
                continue
            lvl, xref, tag, value = int(m.group(1)), m.group(2), m.group(3), m.group(4) or ""

            # CONC joins with no space, CONT starts a new line. Both belong to
            # the node above them, not to a node of their own.
            if tag in ("CONC", "CONT") and stack:
                parent = stack[-1][1]
                parent.value += ("" if tag == "CONC" else "\n") + value
                continue

            node = Node(tag, xref, value)
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            if not stack:
                records.append(node)
            else:
                stack[-1][1].kids.append(node)
            stack.append((lvl, node))
    return records


def _place(node):
    p = node.val("PLAC")
    return re.sub(r"\s*,\s*", ", ", p).strip(" ,")


def _events(node):
    out = []
    for k in node.kids:
        if k.tag not in EVENTS:
            continue
        date, plac = k.val("DATE"), _place(k)
        # OCCU/EDUC carry their detail in the value, not in a PLAC
        detail = k.value.strip()
        cause = k.val("CAUS")
        note = k.val("NOTE")
        agnc = k.val("AGNC")
        typ = k.val("TYPE")
        if not any([date, plac, detail, cause, note, agnc, typ]):
            continue
        out.append({
            "kind": EVENTS[k.tag], "tag": k.tag, "date": date, "place": plac,
            "detail": detail, "cause": cause, "note": note, "agency": agnc, "type": typ,
        })
    return out


def _notes(node, notes_by_id):
    out = []
    for k in node.all("NOTE"):
        v = k.value.strip()
        if v.startswith("@") and v.endswith("@"):
            out.append(notes_by_id.get(v, ""))
        elif v:
            out.append(v)
    return [n for n in out if n]


# What a citation IS, for the kit's public_source(). MyHeritage files a family
# tree entry as a "collection" too (Geni World Family Tree, WikiTree, Filae and
# GenealogieOnline trees), and its record URL looks the same as a census's. The
# kit says a PRIVATE FAMILY-TREE ENTRY does not count, so those are written as
# "MyHeritage family tree" (which the kit's list excludes) and every other
# collection as "MyHeritage record collection" (which it includes). FamilySearch,
# including its Family Tree, always counts, as the kit says.
_TREE_WORDS = ("geni", "wikitree", "family tree", "family trees", "tree index")


def citation_for(src, page=""):
    if not src:
        return ""
    title = (src.get("title") or src.get("abbr") or "").strip()
    typ = src.get("type") or ""
    low = title.lower()
    if "familysearch" in low:
        return "FamilySearch: " + title
    if typ in ("Smart Matching", "Discovery"):
        return "MyHeritage family tree: " + title
    if typ == "Collection":
        if any(w in low for w in _TREE_WORDS):
            return "MyHeritage family tree: " + title
        return "MyHeritage record collection: " + title
    # no type: a source the tree's owner added by hand. Judge it by what it says.
    return " ".join(x for x in (title, page or "", src.get("publication") or "") if x).strip()


def load(path=GED):
    """Return (people, families) as dicts keyed by GEDCOM xref."""
    records = parse(path)

    notes_by_id = {}
    for r in records:
        if r.tag == "NOTE" and r.xref:
            notes_by_id[r.xref] = r.value.strip()

    sources_by_id = {}
    for r in records:
        if r.tag == "SOUR" and r.xref:
            sources_by_id[r.xref] = {
                "title": r.val("TITL"), "abbr": r.val("ABBR"),
                "publication": r.val("PUBL"), "text": r.val("TEXT"),
                "type": r.val("_TYPE"),
            }

    people, families = {}, {}

    for r in records:
        if r.tag == "INDI" and r.xref:
            nm = r.first("NAME")
            raw = nm.value if nm else ""
            given = (nm.val("GIVN") if nm else "") or raw.split("/")[0].strip()
            surn = (nm.val("SURN") if nm else "")
            if not surn and "/" in raw:
                surn = raw.split("/")[1]
            nick = (nm.val("NICK") if nm else "")
            # Married-name / alternate NAME records matter for women
            alts = []
            for extra in r.all("NAME")[1:]:
                alts.append(extra.value.replace("/", "").strip())

            srcs, cites = [], []
            for s in r.all("SOUR"):
                v = s.value.strip()
                cites.append(citation_for(sources_by_id.get(v, {}), s.val("PAGE"))
                             if v.startswith("@") else v)
                if v.startswith("@"):
                    d = sources_by_id.get(v, {})
                    t = d.get("title") or d.get("abbr") or ""
                    if s.val("PAGE"):
                        t = (t + " — " + s.val("PAGE")).strip(" —")
                    if t:
                        srcs.append(t)
                elif v:
                    srcs.append(v)

            people[r.xref] = {
                "id": r.xref,
                "name": raw.replace("/", "").strip() or "(unnamed)",
                "given": given.strip(),
                "surname": surn.strip(),
                "nick": nick.strip(),
                "alt_names": alts,
                "sex": r.val("SEX"),
                "events": _events(r),
                "notes": _notes(r, notes_by_id),
                "sources": srcs,
                "citations": [c for c in cites if c],
                "famc": [k.value for k in r.all("FAMC")],   # family as child
                "fams": [k.value for k in r.all("FAMS")],   # family as spouse
                "uid": r.val("_UID"),
                "mh": (r.val("RIN") or r.xref).strip("@I"),
            }

    for r in records:
        if r.tag == "FAM" and r.xref:
            families[r.xref] = {
                "id": r.xref,
                "husb": r.val("HUSB"),
                "wife": r.val("WIFE"),
                "chil": [k.value for k in r.all("CHIL")],
                "events": _events(r),
                "notes": _notes(r, notes_by_id),
            }

    # back-links, so a person knows their parents without a family lookup
    for f in families.values():
        for c in f["chil"]:
            if c in people:
                people[c].setdefault("parents", [])
                for p in (f["husb"], f["wife"]):
                    if p and p in people and p not in people[c]["parents"]:
                        people[c]["parents"].append(p)
    for p in people.values():
        p.setdefault("parents", [])

    return people, families


# ---- convenience helpers used by the other tools -------------------------

def year(datestr):
    m = re.search(r"\b(\d{4})\b", datestr or "")
    return int(m.group(1)) if m else None


def ev(person, kind):
    for e in person["events"]:
        if e["kind"] == kind:
            return e
    return None


def born(person):
    e = ev(person, "birth") or ev(person, "christening") or ev(person, "baptism")
    return e or {}


def died(person):
    e = ev(person, "death") or ev(person, "burial")
    return e or {}


def lifespan(person):
    b, d = year(born(person).get("date", "")), year(died(person).get("date", ""))
    if b and d:
        return f"{b}–{d}"
    if b:
        return f"b. {b}"
    if d:
        return f"d. {d}"
    return ""


# ---- WHO IS LIVING, AND WHO IS HELD OUT ------------------------------------------
# David's ruling of 16 October 2026, version 2, and the kit's code for it
# (kit/tools/living_rule.py). This file decides nothing; it prepares the three
# facts the rule takes and passes them on.
#
#   birth year    the year of the birth, else christening, else baptism. A range
#                 («BET 1944 AND 1946») takes its LATER end, the younger reading:
#                 where the tree hesitates, the person is not made out older.
#   recorded dead a death or burial event, with or without a date
#   citations     what the tree cites for them (see citation_for above)
#
# Living = 80 or younger by year, with no death recorded, and no public source.
# A person with no birth year cannot be shown to be 80 or younger, so is NOT
# living by this test. The old inference through the family graph (a child born
# in 1990 implies a parent born before 1976) is gone, on purpose: the rule is
# stated on the person's own record.

RECORDED_DEAD_KINDS = ("death", "burial")


def recorded_dead(person):
    """True when the tree RECORDS this person as deceased, with or without a date.

    MyHeritage writes "DEAT Y" for somebody it knows to be dead and does not know
    when; a burial, with or without a date, is the same statement. Only a death
    or burial event counts: a residence, a probate or a will is not a statement
    that the person has died."""
    return any(e["kind"] in RECORDED_DEAD_KINDS for e in person["events"])


def birth_year(person):
    for kind in ("birth", "christening", "baptism"):
        for e in person["events"]:
            if e["kind"] != kind:
                continue
            ys = [int(y) for y in re.findall(r"\b(\d{4})\b", e.get("date") or "")]
            if ys:
                return max(ys) if (e.get("date") or "").upper().startswith("BET") else ys[0]
    return None


def public_source(person):
    return lr.public_source(person.get("citations") or [])


def today():
    return lr.this_year()


def classify_living(people, families=None, today_year=None):
    """{id: True/False}, by the kit's rule, for everybody in the tree."""
    ty = today_year or today()
    return {pid: lr.is_living(birth_year(p), recorded_dead(p), p.get("citations") or [], ty)
            for pid, p in people.items()}


def is_living(person, today_year=None):
    return lr.is_living(birth_year(person), recorded_dead(person),
                        person.get("citations") or [], today_year or today())


# The person promised privacy, BY ID. One id, one person; no file, message or log
# names her. site/src/data/decisions.json records the same id and tools/check_decisions.py
# refuses the build if the two ever differ.
DNA_TESTER = "@I23@"


def held_ids():
    return [DNA_TESTER]


HELD_RULES = {
    "dna-tester": "held by id; a person whose DNA result the archive describes without naming her",
    "possible-minor": "an undated person with a living parent, not recorded dead and with no public source; a child with a known birth year is NOT held out",
}


def held_out(people, living=None, ids=None, today_year=None):
    """{id: rule} for everybody held out, by the kit's rule. Held out is separate
    from living: it covers a possible minor whether or not the 80-year test calls
    them living (an undated child of a living parent is not living by that test),
    and the people promised privacy by id."""
    ty = today_year or today()
    if living is None:
        living = classify_living(people, None, ty)
    ids = list(held_ids() if ids is None else ids)
    out = {}
    for pid, p in people.items():
        parent_living = any(living.get(x) for x in p["parents"])
        if lr.is_held_out(pid, birth_year(p), recorded_dead(p), p.get("citations") or [],
                          parent_living, ids, ty):
            out[pid] = "dna-tester" if str(pid) in {str(i) for i in ids} else "possible-minor"
    return out


def display(person):
    n = person["name"]
    if person["nick"]:
        n = f'{person["given"]} "{person["nick"]}" {person["surname"]}'.strip()
    n = re.sub(r"\s+", " ", n).strip()
    # Two names in the tree carry the owner's own asterisks («Ephraim Wakefield **»),
    # a mark for the owner and not part of anybody's name. Left in, the markup
    # reaches a page as a literal «**» (the self-test refuses it).
    n = re.sub(r"\s*\*+\s*", " ", n).strip()
    # The tree repeats particles: "Conrad V Von von Degenfeld", "Meinhard von
    # von Schonburg", "Adelmann Adelmann von Adelmannsfelden". Collapse an
    # adjacent repeat of the same word, keeping the second form's casing.
    n = re.sub(r"\b(\w+)\s+(\1)\b", lambda m: m.group(2),
               n, flags=re.IGNORECASE)
    return n.strip()


if __name__ == "__main__":
    people, families = load()
    print(f"{len(people)} people, {len(families)} families")
    surname = sys.argv[1] if len(sys.argv) > 1 else "D'Arcy"
    hits = [p for p in people.values() if p["surname"].lower() == surname.lower()]
    print(f"{len(hits)} with surname {surname}")
    for p in sorted(hits, key=lambda x: year(born(x).get("date", "")) or 9999):
        print(f'  {p["id"]:>8}  {display(p):<38} {lifespan(p):<12} '
              f'{born(p).get("place","")[:44]}')

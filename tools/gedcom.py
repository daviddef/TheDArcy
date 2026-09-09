#!/usr/bin/env python3
"""Parse the MyHeritage GEDCOM into a person/family graph the rest of the
archive can walk.

One module, no dependencies. Everything downstream — the ancestry sweep, the
surname clusters, the register — imports `load()` from here so that there is
exactly one place where a GEDCOM line is turned into a fact.
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GED = os.path.join(ROOT, "sources", "myheritage-tree4-2026-09-09.ged")

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

            srcs = []
            for s in r.all("SOUR"):
                v = s.value.strip()
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


def is_living(person, today_year=2026):
    """Per-person fallback. Prefer classify_living(), which uses the whole graph."""
    if died(person).get("date"):
        return False
    b = year(born(person).get("date", ""))
    if b is not None and today_year - b > 100:
        return False
    for e in person["events"]:
        y = year(e.get("date", ""))
        if y is not None and today_year - y > 100:
            return False
    return True


MIN_PARENT_AGE = 14      # nobody is a parent younger than this
MAX_PARENT_AGE = 60      # nor older than this


def classify_living(people, families, today_year=2026, horizon=100):
    """Decide who is living, using the family graph and not just their own dates.

    A tree of this size is full of people with no dates at all — medieval
    nobility, unnamed spouses, half-remembered great-aunts. Judging those by
    their own record alone marks every one of them 'living', which is safe but
    useless: it withholds the fourteenth century.

    So for each person we compute an **upper bound on their birth year** — the
    latest year they could possibly have been born — and treat them as dead only
    when even that latest possible birth is more than `horizon` years ago.

    Every rule below is a genuine upper bound, never a guess:

      · a recorded birth or christening        → born in that year, exactly
      · any recorded event in year E           → born no later than E
      · a child born in year C                 → born no later than C - 14
      · a marriage in year M                   → born no later than M - 14
      · a parent whose bound is P              → born no later than P + 60

    A *recorded* birth is authoritative and is never overridden by inference,
    because an inference that made a living person look older would publish
    them. Where nothing at all is known the bound stays unknown and the person
    is presumed living, which is the safe direction to be wrong in.
    """
    fixed, bound = {}, {}

    def tighten(pid, y):
        if y is None:
            return False
        if pid in fixed:
            return False                     # a recorded birth is not negotiable
        if pid not in bound or y < bound[pid]:
            bound[pid] = y
            return True
        return False

    dead_by_record = set()
    for pid, p in people.items():
        if died(p).get("date"):
            dead_by_record.add(pid)
        b = year(born(p).get("date", ""))
        if b is not None:
            fixed[pid] = b
            bound[pid] = b
            continue
        for e in p["events"]:                # they existed at their own events
            tighten(pid, year(e.get("date", "")))

    kids_of, parents_of = {}, {}
    for f in families.values():
        pair = [x for x in (f["husb"], f["wife"]) if x]
        for par in pair:
            for c in f["chil"]:
                kids_of.setdefault(par, []).append(c)
                parents_of.setdefault(c, []).append(par)
        for e in f["events"]:                # married, so already of age
            y = year(e.get("date", ""))
            for par in pair:
                tighten(par, None if y is None else y - MIN_PARENT_AGE)

    for _ in range(60):
        moved = False
        for pid in people:
            for c in kids_of.get(pid, []):   # older than their children
                if c in bound:
                    moved |= tighten(pid, bound[c] - MIN_PARENT_AGE)
            for par in parents_of.get(pid, []):   # younger than their parents
                if par in bound:
                    moved |= tighten(pid, bound[par] + MAX_PARENT_AGE)
        if not moved:
            break

    out = {}
    for pid in people:
        if pid in dead_by_record:
            out[pid] = False
            continue
        b = bound.get(pid)
        out[pid] = not (b is not None and today_year - b > horizon)
    return out


def display(person):
    n = person["name"]
    if person["nick"]:
        n = f'{person["given"]} "{person["nick"]}" {person["surname"]}'.strip()
    return re.sub(r"\s+", " ", n).strip()


if __name__ == "__main__":
    people, families = load()
    print(f"{len(people)} people, {len(families)} families")
    surname = sys.argv[1] if len(sys.argv) > 1 else "D'Arcy"
    hits = [p for p in people.values() if p["surname"].lower() == surname.lower()]
    print(f"{len(hits)} with surname {surname}")
    for p in sorted(hits, key=lambda x: year(born(x).get("date", "")) or 9999):
        print(f'  {p["id"]:>8}  {display(p):<38} {lifespan(p):<12} '
              f'{born(p).get("place","")[:44]}')

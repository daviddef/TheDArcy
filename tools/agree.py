#!/usr/bin/env python3
"""Check this archive's dates against each other.

Written on 15 September 2026, immediately after finding that Robert D'Arcy's
first commission had been printed as 1776 on five pages and 1778 on a sixth
for weeks, and that nothing in the build would ever have noticed. crossread.py
reads the archive against its OPEN QUESTIONS. This reads it against ITSELF.

The unit is a (person, event) pair. For every person the archive names often
enough to matter, and every event word that carries a date — born, baptised,
married, died, buried, commissioned, gazetted, promoted, sailed, arrived — it
collects every year that appears near both, and reports the pairs that carry
more than one year.

    python3 tools/agree.py              # everything
    python3 tools/agree.py --min 2      # only conflicts with 2+ sources each
    python3 tools/agree.py darcy        # only people whose key matches

It proves nothing on its own. A person really can be gazetted twice, and a
burial really can fall in the year after a death. What it does is refuse to
let two numbers for one event sit on two pages without anybody looking.

WHAT IT HAS ACTUALLY CAUGHT, and what it has not
------------------------------------------------
First run, 15 September 2026: one real fault, found immediately — Robert
D'Arcy's first commission printed as 1778 on six files after it had been
corrected to 1776 everywhere else, including in tools/build_register.py,
which generates a register row and would have reproduced the wrong date on
every future build.

Every one of the 31 pairs still flagged after that was then triaged by hand,
and every one is a false positive. There are exactly three kinds, and none
of them is fixable by tightening the window further:

  1. REPEATED FORENAMES. This family has a Thomas Saniger in 1677, 1744,
     1769, 1803 and 1851. The tool matches on a name, so five men look like
     one man with five dates.
  2. ADJACENT EVENTS. "m. Robert D'Arcy, Portsea, 21 June 1779" sits one
     line above "Joseph D'Arcy, baptised Portsea, 19 March 1780", and a
     proximity test cannot tell a neighbour from a contradiction.
  3. A BIRTH AND A LATE BAPTISM. "29 Apr 1825 / bapt. 31 Mar 1826" is one
     child, correctly recorded, whose two years differ by eleven months.

So the honest summary is: it found one bug, it found it at once, and it has
found nothing since. That is a reasonable thing for a check to do, but do
not read a long list from it as a long list of problems.
"""
import json, os, re, sys, glob, html, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "site", "src", "data")
DIST = os.path.join(ROOT, "site", "dist")

# Event words, and the span in characters within which a year counts as "near".
EVENTS = {
    "born":        r"\bborn\b|\bb\.\s|\bbirth\b",
    "baptised":    r"\bbaptis|\bchristen",
    "married":     r"\bmarri(?:ed|age)\b|\bwed\b",
    "died":        r"\bdied\b|\bdeath\b|\bd\.\s",
    "buried":      r"\bburied\b|\bburial\b",
    "commissioned": r"\bcommission",
    "gazetted":    r"\bgazett",
    "promoted":    r"\bpromot|\bmajor-general\b|\blieutenant-colonel\b",
    "sailed":      r"\bsailed\b|\bembark",
    "arrived":     r"\barrived\b|\blanded\b",
}
NEAR = 70           # characters either side — tight on purpose, see SKIP below

# Aggregation pages are the enemy of a proximity test. A register, a surname
# index or a person page lists dozens of people and dozens of years within a
# few hundred characters, and every one of them looks like a contradiction.
# The first run of this script reported 234 conflicts and almost all of them
# came from these; a check that cries wolf is worse than no check.
SKIP = re.compile(r"^(/people|/who|/register|/families|/searched|/changes|/atlas|"
                  r"/graves|/marriages|/households|/timeline|/direct-line|/spine|"
                  r"/crossread|/index|/$)|mentions\.json|register\.json|"
                  r"families\.json|households\.json|ancestors\.json|line\.json|"
                  r"searched\.json|changes\.json|graves\.json|marriages\.json")
YEAR = re.compile(r"\b(1[5-9]\d\d)\b")

# This archive states wrong dates on purpose. Its method is to record what was
# rejected — "the tree said 1856; the register says 1855" — so a page that
# DISAGREES with a date looks exactly like a page that ASSERTS it. Without this
# filter the checker flags the archive's own corrections as contradictions,
# which it did on its first run: /jean-ward was reported for 1777 in a sentence
# reading "none of which can be hers, since she married ... in June 1779".
NEGATED = re.compile(
    r"\bnot\b|\bnone\b|\bcannot\b|\bno\b|\brather than\b|\binstead\b|"
    r"\bwrong\b|\bcorrect|\bsaid until\b|\bused to\b|\bmistak|\berror\b|"
    r"\bdisproved?\b|\brefut|\bwould have\b|\bif \b|\bclaims?\b|\balleged\b|"
    r"\bsupposed\b|\bunevidenced\b|\bdiffers?\b|\bconflict|"
    # The archive's house idiom for a correction. It prints the wrong date
    # beside the right one on purpose — "the tree says 10 March 1824, ten
    # months early" — and without these the checker reports the correction
    # itself as the contradiction it was written to fix.
    r"\bthe tree (?:says|gives|has|dates|puts)\b|\btree's\b|"
    r"\b(?:months?|years?|days?) (?:early|late|out|before|after)\b|"
    r"\buntil \d{1,2} \w+ 20\d\d\b|\bsaid\b", re.I)

# People worth checking: a first name and a surname, both capitalised, that the
# archive uses as a unit. Kept deliberately narrow — this is a contradiction
# detector, not a name extractor, and a loose pattern drowns it in noise.
PEOPLE = re.compile(
    r"\b((?:Robert|Joseph|George Pitt|Constantine|Jean|Hannah|John|Thomas|Richard|"
    r"Samuel|William|James|Catherine|Charlotte|Margaret|Lydia|Martha|Arthur|Frederick)"
    r"(?:\s+[A-Z][a-z]+){0,2}\s+"
    r"(?:D'Arcy|Darcy|Saniger|Sanigar|Sneyd|Wakefield|Ward|Cotton|Jones|Hurford|Murdoch))\b")


def place_vocab():
    """The archive already generates a gazetteer. Reuse it rather than guess.

    places.json is written from the GEDCOM by build_site_data.py, so it is the
    archive's own vocabulary of places rather than a list somebody typed. Only
    the leading element of each place is taken — "Berkeley, Gloucestershire,
    England" contributes BERKELEY — because that is what prose actually says,
    and the county would match half the county's parishes.
    """
    path = os.path.join(DATA, "places.json")
    if not os.path.exists(path):
        return {}
    out = {}
    for row in json.load(open(path, encoding="utf-8")):
        for name in [row.get("place", "")] + list(row.get("variants") or []):
            head = name.split(",")[0].strip()
            if len(head) < 4 or head.lower() in SKIP_PLACES:
                continue
            out.setdefault(head, set()).add(head)
    return out


# Places too common or too generic to carry information in this archive.
SKIP_PLACES = {"england", "australia", "scotland", "ireland", "wales", "united kingdom",
               "queensland", "gloucestershire", "hampshire", "staffordshire", "kent",
               "somerset", "sussex", "new south wales", "london", "unknown", "none"}


def text_of(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    if path.endswith(".html"):
        raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", raw)


def sources():
    for p in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        name = "data/" + os.path.basename(p)
        if SKIP.search(name):
            continue
        yield name, text_of(p)
    for p in sorted(glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)):
        rel = os.path.relpath(os.path.dirname(p), DIST)
        name = "/" + ("" if rel == "." else rel)
        if SKIP.search(name):
            continue
        yield name, text_of(p)


def main(argv):
    want_min = 1
    if "--min" in argv:
        i = argv.index("--min"); want_min = int(argv[i + 1]); del argv[i:i + 2]
    filters = [a.lower() for a in argv if not a.startswith("-")]

    vocab = place_vocab()
    prx = re.compile(r"\b(" + "|".join(re.escape(p) for p in
                     sorted(vocab, key=len, reverse=True)) + r")\b") if vocab else None

    # (person, event) -> year -> set of sources ; and the same for places
    found = collections.defaultdict(lambda: collections.defaultdict(set))
    where = collections.defaultdict(lambda: collections.defaultdict(set))
    nsrc = 0
    for name, txt in sources():
        nsrc += 1
        for pm in PEOPLE.finditer(txt):
            who = re.sub(r"\s+", " ", pm.group(1)).strip()
            lo, hi = max(0, pm.start() - NEAR), min(len(txt), pm.end() + NEAR)
            window = txt[lo:hi]
            years = {int(y) for y in YEAR.findall(window)}
            if not years:
                continue
            if NEGATED.search(window):
                continue          # the archive is arguing, not asserting
            for ev, rx in EVENTS.items():
                if not re.search(rx, window, re.I):
                    continue
                for y in years:
                    found[(who, ev)][y].add(name)
                if prx:
                    for pl in set(prx.findall(window)):
                        where[(who, ev)][pl].add(name)

    print(f"agree: {nsrc} data files and pages, "
          f"{len(found):,} (person, event) pairs with a date, "
          f"{len(where):,} with a place")

    conflicts = []
    for (who, ev), years in found.items():
        if filters and not any(f in who.lower() for f in filters):
            continue
        strong = {y: s for y, s in years.items() if len(s) >= want_min}
        # More than four years for one event is not a contradiction, it is a
        # list that slipped through SKIP. Report the tight disagreements.
        if 1 < len(strong) <= 4:
            conflicts.append((who, ev, strong))

    # The same shape again for places. A person can legitimately be married in
    # one parish and buried in another, so only the events that happen ONCE and
    # in ONE place are worth checking: a birth, a baptism, a burial.
    SINGLE = {"born", "baptised", "buried", "died"}
    pconf = []
    for (who, ev), places in where.items():
        if ev not in SINGLE:
            continue
        if filters and not any(f in who.lower() for f in filters):
            continue
        strong = {pl: s for pl, s in places.items() if len(s) >= want_min}
        if 1 < len(strong) <= 4:
            pconf.append((who, ev, strong))
    pconf.sort(key=lambda c: (-sum(len(s) for s in c[2].values()), c[0]))

    conflicts.sort(key=lambda c: (-sum(len(s) for s in c[2].values()), c[0]))
    if not conflicts:
        print("  no pair carries more than one year. That is the clean result.")
        return 0

    print(f"  {len(conflicts)} pair(s) carry more than one year:\n")
    for who, ev, years in conflicts:
        spread = max(years) - min(years)
        print(f"  {who} — {ev}  ({len(years)} different years, spread {spread})")
        for y in sorted(years):
            src = sorted(years[y])
            shown = ", ".join(src[:4]) + (f" … +{len(src)-4}" if len(src) > 4 else "")
            print(f"      {y}  ×{len(src):<3} {shown}")
        print()

    if pconf:
        print(f"  {len(pconf)} (person, event) pair(s) carry more than one PLACE:\n")
        for who, ev, places in pconf:
            print(f"  {who} — {ev}  ({len(places)} different places)")
            for pl in sorted(places):
                src = sorted(places[pl])
                shown = ", ".join(src[:3]) + (f" … +{len(src)-3}" if len(src) > 3 else "")
                print(f"      {pl:<22} ×{len(src):<3} {shown}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

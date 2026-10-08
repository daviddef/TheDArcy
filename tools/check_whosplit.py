#!/usr/bin/env python3
"""One human, one dossier. Two names for the same person split the evidence.

9 October 2026. Asked whether the research reaches the PEOPLE and not only the
pages, and it had split one of them in half. Joseph D'Arcy's first wife had two
`/who` pages: «Lady Catherine Georgiana West» carried the two death notices,
and «Catherine Georgiana West» carried her burial and the Westminster baptisms
of her sons. A reader landing on either saw half of her, and neither page said
the other existed.

build_dossiers.py already guards against this and says so in its own comment —
«duplicating them would split the same human in two» — but it compares the
TREE's names against the register's, exactly. Two different strings for one
person in register.json never meet that test. The guard was real and the fault
walked around it.

So this asks a narrower question the other one cannot: are there two dossiers
whose names differ only by a title, a courtesy, or a trailing qualifier? Those
are the forms this archive actually produces — «Lady X» beside «X», «X, née Y»
beside «X». It REFUSES rather than reports, because the fix is to pick one name
in build_register.py and the cost of not doing it is a halved record.

ALLOW carries the pairs that are genuinely two people. There is one: two women
called Catherine Sneyd, one of whom died aged four in 1849 and the other née
Mulcahy in 1858.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outdir
outdir.strict_argv()

# Pairs confirmed to be different humans, with the reason.
ALLOW = {
    ("catherine-sneyd", "catherine-sneyd-nee-mulcahy"):
        "two women: one died aged four in 1849, the other née Mulcahy in 1858",
}

TITLES = r"(?:lady|sir|lord|major|colonel|captain|revd?|reverend|dr|mrs|miss|mr|general|lieut|lieutenant)"
TRAIL = r"(?:-nee-[a-z-]+|-jun|-jnr|-snr|-sen|-\d+)$"


def base(slug):
    s = re.sub(r"^(?:%s)-" % TITLES, "", slug)
    return re.sub(TRAIL, "", s)


def main():
    p = os.path.join(ROOT, "site/src/data/dossiers.json")
    try:
        people = json.load(open(p, encoding="utf-8"))["people"]
    except Exception as e:
        print(f"  FAIL  whosplit   cannot read dossiers.json — {e}")
        return 1

    bybase = {}
    for slug, e in people.items():
        bybase.setdefault(base(slug), []).append(slug)

    bad = []
    for b, slugs in sorted(bybase.items()):
        if len(slugs) < 2:
            continue
        key = tuple(sorted(slugs))
        if key in ALLOW:
            continue
        bad.append((b, sorted(slugs)))

    if not bad:
        print(f"  ok    whosplit   {len(people)} dossier(s), no person split across two names "
              f"({len(ALLOW)} pair(s) declared as different people)")
        return 0

    for b, slugs in bad:
        print(f"  FAIL  whosplit   these look like one person under two names: {', '.join(slugs)}")
        for s in slugs:
            rows = people[s].get("rows") or []
            print(f"          /who/{s} — {len(rows)} record line(s)")
            for r in rows[:2]:
                print(f"              {(r.get('says') or '')[:88]}")
    print("          Pick ONE name in tools/build_register.py so the lines collect on one")
    print("          page, or declare the pair in ALLOW here with the reason they differ.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

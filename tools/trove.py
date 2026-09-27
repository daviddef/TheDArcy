#!/usr/bin/env python3
"""Trove's newspaper and gazette TITLES — which paper covered which place, when.

WHAT THIS MAY AND MAY NOT ASK FOR. The key behind this script was issued by the
National Library on 27 September 2026 after four questions, and the answers are
in notes/letters/2026-09-17-trove-api-RSref189042.md. Three of them were about
scope, and this archive undertook in writing:

  · no Trove content used to train, fine-tune or evaluate any model;
  · NO FULL TEXT OF ANY ARTICLE RETRIEVED — «the request is metadata only,
    newspaper and gazette titles, their place coverage and their date ranges»;
  · nothing AI-written published as though it were a Trove record, and Trove
    cited as «the source of a title and a date range and nothing more»;
  · a build that refuses when a published claim loses its source.

SO THIS SCRIPT CALLS THE TITLES ENDPOINTS AND NOTHING ELSE. It does not search
articles, and it must not be extended to. If this archive ever wants article
search, that is a new conversation with the Library and not a quiet widening of
a promise already made — the undertaking was specific and was the reason the
key was granted.

WHY A TITLES TABLE IS WORTH HAVING ANYWAY. Question four of the Library's form
asked why the API rather than the website, and the answer was: «I am trying to
publish absences as well as findings, and the website cannot support that.»
A search box can tell you a name is not in the papers. It cannot tell you
whether any paper covering that town in that decade is digitised at all — and
those are different statements, one of which is evidence.

    python3 tools/trove.py                 # refresh site/public/trove-titles.json
    python3 tools/trove.py --place Brisbane --year 1902

The key is read from TROVE_API_KEY, never from the command line and never into
a URL: it goes in the X-API-KEY header so it cannot be logged by a proxy or
left in a shell history. .env holds it and .env is gitignored, because this
repository is public.
"""
import argparse, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "public", "trove-titles.json")
API = "https://api.trove.nla.gov.au/v3"
UA = "TheDArcy-archive/1.0 (+https://daviddef.github.io/TheDArcy/)"


def _key():
    k = os.environ.get("TROVE_API_KEY")
    if not k:
        env = os.path.join(ROOT, ".env")
        if os.path.exists(env):
            for line in open(env, encoding="utf-8"):
                if line.startswith("TROVE_API_KEY="):
                    k = line.split("=", 1)[1].strip()
                    break
    if not k:
        sys.exit("trove: no TROVE_API_KEY in the environment or .env")
    return k


def _get(path):
    req = urllib.request.Request(
        f"{API}/{path}?encoding=json",
        headers={"X-API-KEY": _key(), "Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


# The title string carries the place and the range in brackets — "The Brisbane
# Courier (Qld. : 1864 - 1933)". The dates are also separate fields and those
# are authoritative; the bracket is parsed only for the PLACE, which has no
# field of its own.
_BRACKET = re.compile(r"\(([^)]*)\)\s*$")
_RANGE = re.compile(r"(1[6-9]\d\d|20\d\d)\s*-\s*(1[6-9]\d\d|20\d\d)")
_STATE_TOKEN = re.compile(
    r"(?:^|,\s*)(ACT|NSW|NT|Qld|SA|Tas|Vic|WA)\.?\s*$", re.I)


def _split(title, state):
    """Place of publication and EVERY date range, from the title's bracket.

    Trove writes a title as «Clarion (Brisbane, Qld. : 1940 - 1943; 1945 -
    1956)». Two things there are traps for a coverage table.

    The bracket is sometimes «Brisbane, Qld.» and sometimes just «Qld.» — the
    state on its own, which is not a place and must not be recorded as one.

    And the range can be SEVERAL ranges. startDate and endDate flatten those to
    the outer envelope, so a paper that did not publish in 1944 reads as
    covering it. For a table whose only purpose is to let an absence be quoted,
    a false «yes, a paper covered that» is the worst answer it can give, so the
    ranges are parsed out and kept apart.
    """
    m = _BRACKET.search(title or "")
    inside = m.group(1) if m else ""
    if ":" in inside:
        where, _, when = inside.partition(":")
    else:
        # «(1933 - 1982)» — a bare range and no place at all. Without this the
        # whole bracket lands in `place` and the table grows towns named 1933.
        where, when = "", inside
    where = where.strip()
    if not re.search(r"[A-Za-z]", where):
        where = ""
    if _STATE_TOKEN.search(where) and "," not in where:
        where = ""                      # the state repeated, not a town
    else:
        where = _STATE_TOKEN.sub("", where).strip().rstrip(",").strip()
    ranges = [[int(a), int(b)] for a, b in _RANGE.findall(when)]
    return where, ranges


def fetch():
    """Both endpoints, with the count checked against what was parsed.

    THE GAZETTE LIST COMES BACK UNDER THE KEY "newspaper". Asking for a
    "gazette" key returns nothing, and nothing looks exactly like an empty
    archive: the first run of this script reported 0 gazettes and was one
    commit away from publishing that as an open file. So the endpoint's own
    `total` is compared with the number of rows parsed, and a disagreement
    REFUSES rather than writing a smaller table. A zero has to be the
    Library's zero, not this parser's.
    """
    rows = []
    for kind, path in (("newspaper", "newspaper/titles"),
                       ("gazette", "gazette/titles")):
        d = _get(path)
        got = d.get("newspaper") or []
        total = d.get("total")
        if total is not None and total != len(got):
            sys.exit(f"trove: {path} says total={total} and this parser found "
                     f"{len(got)}. The response shape has changed; fix the parser "
                     f"rather than publishing the smaller number.")
        for t in got:
            where, ranges = _split(t.get("title"), t.get("state"))
            f, to = (t.get("startDate") or "")[:4], (t.get("endDate") or "")[:4]
            if not ranges and f and to:
                ranges = [[int(f), int(to)]]
            rows.append({
                "kind": kind,
                "id": t.get("id"),
                "title": t.get("title"),
                "place": where,
                "state": t.get("state"),
                "from": f,
                "to": to,
                "ranges": ranges,
                "gap": len(ranges) > 1,
                "url": t.get("troveUrl"),
            })
        print(f"  {kind}: {len(got)} (endpoint total {total})")
    rows.sort(key=lambda r: (r["state"] or "", r["title"] or ""))
    return rows


def covering(rows, place=None, year=None):
    """Titles whose place matches and whose range contains the year."""
    out = []
    for r in rows:
        if place and place.lower() not in ((r["place"] or "") + " " + (r["title"] or "")).lower():
            continue
        if year:
            # the parsed ranges, never the flattened envelope
            if not any(a <= year <= b for a, b in (r.get("ranges") or [])):
                continue
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--place")
    ap.add_argument("--year", type=int)
    ap.add_argument("--refresh", action="store_true",
                    help="call the API even when the cached file exists")
    a = ap.parse_args()

    if a.refresh or not os.path.exists(OUT) or (a.place is None and a.year is None):
        rows = fetch()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({
                "_note": ("Trove newspaper and gazette TITLES — title, place, state and date "
                          "range, and nothing else. Published openly so that an absence in the "
                          "Australian papers can be quoted against what is digitised. Source: "
                          "Trove, National Library of Australia. Metadata only, by undertaking."),
                "source": "https://trove.nla.gov.au/",
                "titles": rows,
            }, f, ensure_ascii=False, indent=1)
        print(f"  wrote {os.path.relpath(OUT, ROOT)} — {len(rows)} title(s)")
    else:
        rows = json.load(open(OUT, encoding="utf-8"))["titles"]

    if a.place or a.year:
        hits = covering(rows, a.place, a.year)
        where = " ".join(x for x in [a.place, str(a.year) if a.year else ""] if x)
        print(f"  {len(hits)} title(s) covering {where}")
        for r in hits[:40]:
            print(f"    {r['from']}-{r['to']:<5} {r['state']:<4} {r['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

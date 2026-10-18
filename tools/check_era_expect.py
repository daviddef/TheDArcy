#!/usr/bin/env python3
"""Does every built person page carry exactly the "at the time" notes the page's own printed dates and places, and the snapshot, call for?

The kit's gate (checkera.py) holds each note it finds to the snapshot. It cannot know a note is MISSING, or that a note was put beside the
wrong date, because that depends on what THIS archive prints. This reads the BUILT pages, not the data: for each person page it takes the
three places the template prints a date and a place together (the Born row, the Died row and each marriage whose spouse is named), reads
the date and the place as printed, works out the note they call for (the kit's Python library on the committed snapshot; the same date
rule as site/src/lib/eraYear.js, written again here: a month-first date turned round, a plain year only, and before 1752 only where the year
either side lies in the same era) and compares it with the note actually beside them: the era id, the year, the boundary wording and the
marks the kit puts on a note. A note where none is called for, a missing note and a differing note each fail. A living or noindex page
that carries a note fails. It prints COUNTS ONLY: never a person, a place or a date. An archive with no person page, or no note at all, is
exit 2, not a pass.

    python3 tools/check_era_expect.py [--dist site/dist] [--report FILE]     (--report: counts of the events left silent, by reason and region)
"""
import argparse
import collections
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outdir  # noqa: E402

ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools")
sys.path.insert(0, KIT)
import eralib  # noqa: E402

CALENDAR_YEAR = 1752
MONTH_FIRST = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2})\s+(\d{4})$")
NOTE = re.compile(r'<span class="era-note"([^>]*)>')
NOTE_FULL = re.compile(r'<span\b[^>]*\bclass="era-note"[^>]*>(?:<span\b[^>]*>[^<]*</span>|<a\b[^>]*>[^<]*</a>|\s+)*</span>')
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
ROW = re.compile(r'<tr><td style="white-space:nowrap">(Born|Died)</td><td class="m">(.*?)</td><td>(.*?)</td></tr>', re.S)
SMALL = re.compile(r'<span class="small">(.*?)</span>', re.S)
MARKS = (("data-era-approx", "approx"), ("data-era-contested", "contested"), ("data-era-margin-unsourced", "unsourced"),
         ("data-era-edge-agree", "edgeAgree"), ("data-era-boundary", "boundary"))


def text(s):
    """The text of a fragment: any note (and the era <style> that the first note of a page draws) taken out whole, tags dropped, entities unescaped, white space folded."""
    s = NOTE_FULL.sub("", re.sub(r"<style\b[^>]*>.*?</style>", "", s, flags=re.S))
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def day_first(d):
    t = re.sub(r"\s+", " ", str(d or "").strip())
    m = MONTH_FIRST.match(t)
    return "%s %s %s" % (m.group(2), m.group(1), m.group(3)) if m else t


def era_id_at(snap, place, year):
    region = (snap.get("places") or {}).get(eralib.fold(place))
    eras = (snap.get("regions") or {}).get(region) if isinstance(region, str) else None
    if not isinstance(eras, list):
        return None
    hit = [e for e in eras if e["from"] <= year and (e.get("to") is None or year < e["to"])]
    return hit[0]["id"] if len(hit) == 1 else None


def expect(snap, place, date):
    """-> (reason, era or None). reason is 'ok' or why this place and date give no note."""
    if not place or not eralib.fold(place):
        return "no-place", None
    if not date or date == "—":
        return "no-date", None
    d = day_first(date)
    m = re.search(r"(\d{4})$", d)
    year = eralib.plain_year(d, int(m.group(1)) if m else None)
    if year is None:
        return "year", None
    why = eralib.why_not(snap, place, year)
    if why != "ok":
        return why, None
    era = eralib.era_at(snap, place, year)
    if year < CALENDAR_YEAR and (era_id_at(snap, place, year - 1) != era["id"] or era_id_at(snap, place, year + 1) != era["id"]):
        return "julian", None
    return "ok", era


def events(html_text):
    """[(kind, date, place, note attrs or None)] in page order: the Born and Died rows, then each marriage with a named spouse."""
    out = []
    for kind, date, place in ROW.findall(html_text):
        notes = [dict(ATTR.findall(a)) for a in NOTE.findall(place)]
        out.append((kind, text(date), text(place), notes))
    i = html_text.find('>Married</h3>')
    if i >= 0:
        j = html_text.find("<h3", i + 10)
        k = html_text.find("</div>", i)
        end = min(x for x in (j, k) if x >= 0) if (j >= 0 or k >= 0) else len(html_text)
        for p in re.findall(r"<p>(.*?)</p>", html_text[i:end], re.S):
            date = place = None
            for sm in SMALL.findall(p):
                t = text(sm)
                if t.startswith("· divorced") or t.startswith("(") :
                    continue
                if t.startswith("· "):
                    date = t[2:].strip()
                elif t.startswith("at "):
                    place = t[3:].strip()
            notes = [dict(ATTR.findall(a)) for a in NOTE.findall(p)]
            if date or place or notes:
                out.append(("Married", date, place, notes))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    dist = outdir.resolve(a.dist)
    snap = json.load(open(os.path.join(ROOT, "site", "src", "data", "era-snapshot.json"), encoding="utf-8"))
    base = os.path.join(dist, "people")
    if not os.path.isdir(base):
        print("  --    era-expect  not run: no person page found in %s" % os.path.relpath(dist, ROOT))
        return 2
    pages = bad = want = found = unchecked = unassessed = living_with_note = 0
    reasons = collections.Counter()
    by_region = collections.Counter()
    for slug in sorted(os.listdir(base)):
        f = os.path.join(base, slug, "index.html")
        if not os.path.isfile(f):
            continue
        h = open(f, encoding="utf-8", errors="ignore").read()
        pages += 1
        noindex = bool(re.search(r'<meta[^>]*name="robots"[^>]*noindex', h, re.I))
        evs = events(h)
        found_here = sum(len(e[3]) for e in evs)
        found += found_here
        if noindex:
            if found_here or NOTE.search(h):
                living_with_note += 1
                bad += 1
            continue
        page_bad = False
        for kind, date, place, notes in evs:
            reason, era = expect(snap, place, date)
            reasons[reason] += 1
            if era is None:
                if notes:
                    page_bad = True
                continue
            want += 1
            unchecked += 1 if era["unchecked"] else 0
            unassessed += 1 if era["unassessed"] else 0
            by_region[era["region"]] += 1
            if len(notes) != 1:
                page_bad = True
                continue
            n = notes[0]
            if n.get("data-era") != era["id"] or n.get("data-era-year") != str(era["year"]) \
                    or n.get("data-era-assessed") != ("0" if era["unassessed"] else "1") \
                    or any((n.get(attr) == "1") != (era.get(key) is True) for attr, key in MARKS):
                page_bad = True
        bad += 1 if page_bad else 0
    if pages == 0:
        print("  --    era-expect  not run: no person page found in %s" % os.path.relpath(dist, ROOT))
        return 2
    if want == 0 and found == 0:
        print("  --    era-expect  not run: the data calls for no note and the pages carry none; a gate that found nothing has not found that nothing is wrong")
        return 2
    ok = bad == 0 and want == found
    print("  %s  era-expect  %d pages; %d notes expected, %d found; %d page(s) differ (%d notes rest on a place with no coordinates, %d on an era the Atlas has not assessed); "
          "%d living or noindex page(s) carry a note" % ("ok  " if ok else "FAIL", pages, want, found, bad, unchecked, unassessed, living_with_note))
    if a.report:
        json.dump({"pages": pages, "reasons": dict(reasons), "notes_by_region": dict(by_region), "unchecked": unchecked, "unassessed": unassessed},
                  open(a.report, "w"), indent=1, sort_keys=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

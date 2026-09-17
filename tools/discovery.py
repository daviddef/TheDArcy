#!/usr/bin/env python3
"""The National Archives' Discovery catalogue, asked properly.

WHY THIS EXISTS. This archive has searched Discovery thirty-seven times and
graded its coverage `good`, and every one of those searches was made by hand in
a browser, one query at a time. That is fine for a question and useless for a
measurement: you cannot control-test a null you typed into a search box, and you
cannot say "this surname returns 71 hits and that one returns none" unless you
asked both the same way.

Discovery publishes a JSON API that needs no account, no key and no bot check:

    GET https://discovery.nationalarchives.gov.uk/API/search/records
        ?sps.searchQuery=<term>&sps.resultsPageSize=<n>

It returns `count` and a `records` array carrying reference, title, covering
dates, holding repository and catalogue context. `nextBatchMark` pages it.

So: one function, called the same way for every term, so that counts can be set
beside each other and a null can be quoted with the query that produced it.

    python3 tools/discovery.py "Saniger" "Sanigar" --out /tmp/sweep.json
    python3 tools/discovery.py --count-only "Swonhungre" "Swanhunger"

Findable records only; Discovery indexes other repositories as well as Kew, and
the `heldBy` field says which — that distinction matters here, because most of
this family's catalogue presence is Gloucestershire Archives rather than TNA.
"""
import json, sys, time, urllib.parse, urllib.request

API = "https://discovery.nationalarchives.gov.uk/API/search/records"
UA = {"Accept": "application/json", "User-Agent": "TheDArcy-archive/1.0 (family history research)"}


def search(term, page_size=100, max_records=1000, pause=0.4):
    """Every record Discovery returns for one term. Paged, and polite."""
    out, mark, total = [], None, None
    while True:
        q = {"sps.searchQuery": term, "sps.resultsPageSize": str(page_size)}
        if mark:
            q["sps.batchStartMark"] = mark
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        if total is None:
            total = d.get("count", 0)
        batch = d.get("records") or []
        out.extend(batch)
        mark = d.get("nextBatchMark")
        if not batch or not mark or len(out) >= min(total, max_records):
            break
        time.sleep(pause)
    return total, out


def slim(r):
    """The fields worth keeping. Discovery returns thirty-four per record and
    thirty of them are empty for catalogue-level entries."""
    return {
        "ref": r.get("reference", ""),
        "title": " ".join((r.get("title") or "").split()),
        "dates": r.get("coveringDates", ""),
        "held": "; ".join(r.get("heldBy") or []),
        "context": " ".join((r.get("context") or "").split())[:160],
        "desc": " ".join((r.get("description") or "").split())[:300],
        "id": r.get("id", ""),
    }


def main(argv):
    count_only = "--count-only" in argv
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        out_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    terms = [a for a in argv if not a.startswith("--")]
    if not terms:
        print(__doc__)
        return 2

    result = {}
    for t in terms:
        total, recs = search(t, max_records=0 if count_only else 1000)
        result[t] = {"count": total, "records": [slim(r) for r in recs]}
        print(f"{total:6d}  {t}")
    if out_path:
        json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

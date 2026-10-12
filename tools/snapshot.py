#!/usr/bin/env python3
"""Does a permanent copy exist of every source this archive cites?

check_cites.py asks whether a citation still resolves TODAY. This asks the
harder question: if it stops resolving tomorrow, can the reader still see what
this archive saw? A footnote to a page that has gone is a footnote to nothing,
and the reader cannot tell the difference from the page.

WHAT IT DOES AND DOES NOT TOUCH. Only the citations THIS ARCHIVE CHOSE — the
GEDCOM export's own myheritage links are somebody else's footnotes and are
left alone, as check_cites.py already argues. For each one it asks the Wayback
Machine's availability API whether a capture exists, and records the timestamp
and the permanent URL in tools/snapshots.json, which is committed so the build
and the deploy can both see it.

  python3 tools/snapshot.py            # report from the cache, instantly
  python3 tools/snapshot.py --check    # ask the Wayback Machine what exists
  python3 tools/snapshot.py --save     # ask it to capture what is missing

SAVING IS A REQUEST TO A PUBLIC ARCHIVE TO CRAWL A PUBLIC PAGE, nothing of
this family's goes anywhere, and it is rate-limited hard and capped per run so
that it stays a polite request rather than a flood.
"""
import os, re, sys, json, time, argparse, urllib.parse
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "snapshots.json")
AVAIL = "https://archive.org/wayback/available?url="
SAVE = "https://web.archive.org/save/"
UA = {
    "User-Agent": "darcy-archive-snapshot/1.0 (+https://darcy.defranceski.com/)",
    "Accept": "*/*",
    "Accept-Language": "en",
}

sys.path.insert(0, HERE)
import check_cites  # the URL scanner and the ours/inherited split live there


# A CITATION TO THE INTERNET ARCHIVE IS ALREADY A PERMANENT COPY, and the
# Wayback Machine rightly refuses to snapshot its own pages: the first run of
# this tool asked it to capture twelve archive.org URLs and got twelve 523s
# back. Counting those as "unprotected" made the archive look worse than it is
# and would have sent the next person chasing a capture that cannot exist.
PERMANENT = re.compile(r"^https?://(web\.)?archive\.org/", re.I)


def ours():
    found = check_cites.urls()
    return {u: sorted(w) for u, w in found.items() if not check_cites.inherited(sorted(w))}


def permanent_already(u):
    return bool(PERMANENT.match(u))


def available(u, timeout=25):
    q = AVAIL + urllib.parse.quote(u, safe="")
    with urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=timeout) as r:
        d = json.load(r)
    snap = (d.get("archived_snapshots") or {}).get("closest") or {}
    if snap.get("available"):
        return snap.get("timestamp"), snap.get("url")
    return None, None


def save(u, timeout=90):
    try:
        req = urllib.request.Request(SAVE + u, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)[:40]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="ask the Wayback Machine what exists")
    ap.add_argument("--save", action="store_true", help="request captures for what is missing")
    ap.add_argument("--max", type=int, default=20, help="most captures to request in one run")
    ap.add_argument("--pause", type=float, default=6.0, help="seconds between save requests")
    a = ap.parse_args(argv)

    cites = ours()
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    if a.check or a.save:
        for i, u in enumerate(sorted(cites), 1):
            if permanent_already(u):
                cache[u] = {"ts": "self", "url": u, "when": time.time()}
                continue
            if u in cache and cache[u].get("ts"):
                continue
            try:
                ts, snap = available(u)
            except Exception as e:
                sys.stderr.write(f"\r  snapshot: {i}/{len(cites)} (error {str(e)[:24]})   ")
                continue
            cache[u] = {"ts": ts, "url": snap, "when": time.time()}
            sys.stderr.write(f"\r  snapshot: asked {i}/{len(cites)}   ")
            sys.stderr.flush()
        sys.stderr.write("\n")

    if a.save:
        missing = [u for u in sorted(cites)
                   if not (cache.get(u) or {}).get("ts") and not permanent_already(u)]
        asked = 0
        for u in missing[: a.max]:
            st = save(u)
            print(f"  save  {st}  {u[:78]}")
            asked += 1
            time.sleep(a.pause)
        if asked:
            print(f"  asked the Wayback Machine to capture {asked} page(s); "
                  f"captures take a few minutes to become available")

    have = sum(1 for u in cites if (cache.get(u) or {}).get("ts"))
    selfarch = sum(1 for u in cites if permanent_already(u))
    json.dump({u: v for u, v in cache.items() if u in cites},
              open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

    pct = (100.0 * have / len(cites)) if cites else 0.0
    lead = "ok  " if pct >= 80 else "warn"

    # A FIGURE IN PROSE GOES STALE THE NEXT TIME THE TOOL RUNS. The first
    # version of this reported its coverage only in the build log and in a
    # sentence somebody typed, and within a week the sentence said 70 of 84
    # while the tool said 73 of 87. Write the number where the site can read
    # it, so the page cannot disagree with the instrument.
    import collections as _k
    _miss = [u for u in cites if not (cache.get(u) or {}).get("ts")]
    _hosts = _k.Counter(re.sub(r"^https?://([^/]+).*", r"\1", u) for u in _miss)
    with open(os.path.join(os.path.dirname(HERE), "site/src/data/snapshot-summary.json"),
              "w", encoding="utf-8") as f:
        json.dump({"have": have, "total": len(cites), "pct": round(pct),
                   "selfArchived": selfarch, "missing": len(_miss),
                   "missingHosts": _hosts.most_common(),
                   "checked": time.strftime("%d %b %Y")}, f, ensure_ascii=False, indent=1)
    print(f"  {lead}  snapshot   {have} of {len(cites)} citation(s) this archive chose have a "
          f"permanent copy ({pct:.0f}%) \u2014 {selfarch} of them because they ARE the "
          f"Internet Archive and need no capture")
    if have < len(cites):
        # NOT A TO-DO LIST. Every one of the fourteen left on 11 October 2026
        # resolves perfectly and simply declines to be archived: Trove, Find a
        # Grave, FamilySearch's tree, the Anubis-gated French archive, FIBIS.
        # Printing them by host says that, where a bare number would read as
        # work nobody had got round to.
        import collections as _c
        miss = [u for u in cites if not (cache.get(u) or {}).get("ts")]
        hosts = _c.Counter(re.sub(r"^https?://([^/]+).*", r"\1", u) for u in miss)
        top = ", ".join(f"{h} ({n})" for h, n in hosts.most_common(6))
        print(f"        {len(miss)} have none: {top}")
        print(f"        A HOST THAT DECLINES TO BE ARCHIVED IS NOT A JOB UNDONE. Check these "
              f"against check_cites.py: if they resolve, the capture is refused and not missing. "
              f"Run `--save` only for ones that are genuinely new.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Do the sources this archive cites still resolve?

check_links.py tests the links INSIDE the site. Nothing tested the links out of
it, and a dead citation looks exactly like a good one on the page: the reader
cannot tell, and neither could the build.

It REPORTS, it does not gate. An archive.org outage is not a reason to refuse a
build, and a citation that 404s today may be a move rather than a loss — the
judgement is a person's. What the build owes the reader is to notice.

TWO THINGS THIS TOOL GOT WRONG BEFORE IT EVER RAN PROPERLY, both recorded here
because the second is the dangerous kind.

1. IT WAS TOO SLOW TO KEEP. 581 distinct URLs, one at a time, 12s timeout, no
   output until the last returned. A run was stopped at eight minutes with
   nothing printed. A step people disable is worse than no step. It now runs
   in parallel, samples the big hosts, caches what it learns, and the build
   reads the cache rather than the network.

2. IT WOULD HAVE REPORTED 429 BLOCK PAGES AS HEALTHY CITATIONS. 429 of the 581
   are myheritage.com links carried in from the GEDCOM export. MyHeritage
   answers a robot with **HTTP 200 and an 843-byte body reading «Request
   unsuccessful. Incapsula incident ID: …»**. The old tool read the status code
   and nothing else, so its headline would have counted every one of them as
   resolving — a reassuring number that was wrong about three quarters of the
   archive's citations. A STATUS CODE IS NOT A PAGE. This version reads the
   first few kilobytes and calls that outcome `walled`, which is neither alive
   nor dead: it means nobody can tell from outside, and that is the honest
   answer rather than the comfortable one.

  python3 tools/check_cites.py              # report from the cache, instantly
  python3 tools/check_cites.py --refresh    # hit the network, update the cache
  python3 tools/check_cites.py --refresh --all   # do not sample the big hosts
"""
import os, re, sys, json, glob, time, argparse, threading, collections
import urllib.request, urllib.error, socket
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "src", "data")
# NOT under site/src/data: the URL scanner globs that directory, and a cache of
# URLs living inside the scanned tree would feed itself every run. It also
# would have to answer to the unpublished-prose gate, which is about writing
# meant for readers, which this is not.
CACHE = os.path.join(HERE, "cites-cache.json")

# THE THIRD THING THIS TOOL GOT WRONG. urllib sends no Accept header unless
# told to, and four FamilySearch collection pages answer a request without one
# with a flat 404. They are alive, they are this archive's own citations, and
# they were reported dead by a tool that simply was not asking properly. This
# is not a browser disguise and nothing here pretends to be Chrome: the agent
# string still says what this is. It is the header every ordinary client sends.
UA = {
    "User-Agent": "darcy-archive-citation-check/2.1 (+https://daviddef.github.io/TheDArcy/)",
    "Accept": "*/*",
    "Accept-Language": "en",
}
URL = re.compile(r"https?://[^\s\"'<>)\]]+")
SKIP = re.compile(r"example\.com|localhost|127\.0\.0\.1", re.I)

# Bodies that are a door, not a document. Each of these has been seen on a
# response this archive actually received; none is here on suspicion.
WALL = re.compile(
    r"Incapsula incident|Request unsuccessful|Just a moment\.\.\."
    r"|Attention Required!|Performing security verification"
    r"|Checking your browser before|not a bot|enable JavaScript and cookies",
    re.I)

# Above this many URLs on one host, check a sample and say so. The point is
# myheritage.com's 429, which are one wall answering 429 times.
SAMPLE_OVER = 25
SAMPLE_SIZE = 8

# A LINK THIS ARCHIVE CHOSE IS NOT THE SAME THING AS A LINK MYHERITAGE PUT IN
# THE EXPORT, and only the first is anybody's responsibility here. These three
# data files are built from the GEDCOM; a URL appearing ONLY in them was
# inherited. On 10 October every one of the nine dead links was inherited and
# NONE of the archive's own citations was dead — a distinction worth printing
# rather than working out by hand each time.
GEDCOM_FILES = {"families.json", "ancestors.json", "line.json"}


def inherited(where):
    return bool(where) and set(where) <= GEDCOM_FILES


def host_of(u):
    return re.sub(r"^https?://([^/@]*@)?([^/:]+).*", r"\2", u)


def urls():
    seen = collections.defaultdict(set)
    for p in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        raw = open(p, encoding="utf-8", errors="replace").read()
        for m in URL.finditer(raw):
            # A JSON file escapes its quotes and slashes, and the regex is
            # happy to swallow the backslash. Ten URLs came back 404 on the
            # first full run for no reason but a trailing «\\» — the tool
            # inventing dead citations, which is the one failure a report
            # like this cannot afford.
            u = m.group(0).rstrip(".,;\\").replace("\\/", "/")
            # …and a data file written as HTML swallows its entities into the
            # URL too: one citation 404'd only because «&nbsp» had been
            # captured onto the end of it.
            u = re.sub(r"&(nbsp|amp|quot|#\d+);?$", "", u).rstrip(".,;")
            if not SKIP.search(u):
                seen[u].add(os.path.basename(p))
    return seen


def fetch(u, timeout):
    """Return (status, verdict). Reads the body, because a 200 can be a wall."""
    try:
        r = urllib.request.Request(u, headers=UA, method="GET")
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            head = resp.read(4096).decode("utf-8", "replace")
            st = resp.status
            if WALL.search(head):
                return st, "walled"
            if 200 <= st < 300:
                return st, "ok"
            if 300 <= st < 400:
                return st, "moved"
            return st, "gone"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            return e.code, "walled"
        # A 3xx can arrive as an exception when urllib declines to follow it.
        # It is still a redirect. The first full run graded 436 MyHeritage 302s
        # as «refused» and put them under a heading that invited somebody to
        # read them as dead citations. They are a door, same as the rest.
        if 300 <= e.code < 400:
            return e.code, "moved"
        return e.code, "gone"
    except Exception as e:
        # urllib.error.URLError WRAPS the name-resolution failure rather than
        # letting socket.gaierror through, so catching gaierror by type never
        # fired and a host that does not exist was being filed beside a host
        # that was merely slow.
        reason = getattr(e, "reason", e)
        if isinstance(reason, socket.gaierror) or "nodename nor servname" in str(reason):
            return str(reason)[:48], "dns"
        # A timeout is this archive's failure to get an answer, not the
        # source's failure to exist. Graded apart so that a slow host and a
        # dead one never share a number.
        return str(e)[:48], "flaky"


def refresh(found, cache, workers, timeout, sample, max_age):
    by_host = collections.defaultdict(list)
    for u in found:
        by_host[host_of(u)].append(u)

    todo, inferred = [], {}
    now = time.time()
    for h, us in sorted(by_host.items()):
        us = sorted(us)
        fresh = [u for u in us
                 if u in cache and now - cache[u].get("when", 0) < max_age * 86400]
        if sample and len(us) > SAMPLE_OVER:
            pick = us[:: max(1, len(us) // SAMPLE_SIZE)][:SAMPLE_SIZE]
            todo += pick
            inferred[h] = [u for u in us if u not in pick]
        else:
            todo += [u for u in us if u not in fresh]

    done = [0]
    lock = threading.Lock()
    sem = collections.defaultdict(lambda: threading.Semaphore(4))

    def one(u):
        with sem[host_of(u)]:
            st, verdict = fetch(u, timeout)
        with lock:
            done[0] += 1
            cache[u] = {"status": st, "verdict": verdict, "when": time.time()}
            if done[0] % 10 == 0 or done[0] == len(todo):
                sys.stderr.write(f"\r  cites: checked {done[0]}/{len(todo)}   ")
                sys.stderr.flush()

    if todo:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one, todo))
        sys.stderr.write("\n")

    # A sampled host's verdict is carried to its other URLs, marked as sampled
    # so the report can never pass it off as a measurement of each one.
    for h, rest in inferred.items():
        got = [cache[u]["verdict"] for u in by_host[h] if u in cache and u not in rest]
        if not got:
            continue
        verdict = collections.Counter(got).most_common(1)[0][0]
        if len(set(got)) == 1:
            for u in rest:
                cache[u] = {"status": cache[[x for x in by_host[h] if x not in rest][0]]["status"],
                            "verdict": verdict, "when": time.time(), "sampled": h}
    return cache, inferred


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="hit the network")
    ap.add_argument("--all", action="store_true", help="do not sample big hosts")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--max-age", type=int, default=14, help="days before a cached result is re-checked")
    a = ap.parse_args(argv)

    found = urls()
    hosts = collections.Counter(host_of(u) for u in found)
    nfiles = len({f for s in found.values() for f in s})
    print(f"cites: {len(found)} distinct external URL(s) across {nfiles} data file(s), "
          f"{len(hosts)} host(s)")

    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    inferred = {}
    if a.refresh:
        cache, inferred = refresh(found, cache, a.workers, a.timeout,
                                  sample=not a.all, max_age=a.max_age)
        cache = {u: v for u, v in cache.items() if u in found}
        json.dump(cache, open(CACHE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)

    have = {u: cache[u] for u in found if u in cache}
    if not have:
        print("  warn  cites      no cache and --refresh not given; nothing has been checked")
        print("        run: python3 tools/check_cites.py --refresh")
        return 0

    buckets = collections.defaultdict(list)
    for u, v in sorted(have.items()):
        buckets[v["verdict"]].append((u, v))

    chosen_dead = 0
    for kind in ("dns", "gone"):
        for u, v in buckets[kind]:
            where = sorted(found[u])
            tag = "no such host" if kind == "dns" else v["status"]
            mark = "inherited" if inherited(where) else "OURS"
            if mark == "OURS":
                chosen_dead += 1
            print(f"  warn  cites      {tag}  [{mark}]  {u[:68]}")
            print(f"                   cited in {', '.join(where)[:78]}")

    walled_hosts = collections.Counter(host_of(u) for u, _ in buckets["walled"])
    age = (time.time() - max(v.get("when", 0) for v in have.values())) / 86400
    miss = len(found) - len(have)
    lead = "warn" if (buckets["gone"] or buckets["dns"]) else "ok  "
    print(f"  {lead}  cites      {len(buckets['ok'])} resolve, {len(buckets['moved'])} redirect, "
          f"{len(buckets['walled'])} walled, {len(buckets['flaky'])} did not answer in time, "
          f"{len(buckets['dns'])} host gone, {len(buckets['gone'])} refused"
          + (f", {miss} never checked" if miss else "")
          + f" · cache {age:.1f} day(s) old")

    # A cache is a measurement with a date on it, and a measurement with a
    # date on it goes stale without ever looking wrong. The age is printed
    # above on every run; past two months the build says so in its own voice.
    if age > 60:
        print(f"  warn  cites      THE CACHE IS {age:.0f} DAYS OLD and the numbers above are that "
              f"old too. Run: python3 tools/check_cites.py --refresh --all")

    if buckets["walled"]:
        top = ", ".join(f"{h} ({n})" for h, n in walled_hosts.most_common(3))
        nsam = sum(1 for _, v in buckets["walled"] if v.get("sampled"))
        print(f"        walled means a door, not a dead citation: mostly {top}."
              + (f" {nsam} of them carry a host verdict taken from a sample rather than"
                 f" their own request." if nsam else ""))
        print(f"        A STATUS CODE IS NOT A PAGE. MyHeritage answers a robot with 200 and an"
              f" Incapsula block body, so counting status alone would call these healthy.")
    if buckets["flaky"]:
        print(f"        {len(buckets['flaky'])} timed out. THAT IS THIS MACHINE FAILING TO GET AN "
              f"ANSWER, not a source failing to exist, and it is not a candidate for anything.")
    if buckets["dns"] or buckets["gone"]:
        n = len(buckets["dns"]) + len(buckets["gone"])
        print(f"        only the {n} above are candidates for a dead citation — "
              f"a redirect is a move. Read them, do not obey them.")
        print(f"        of those, {chosen_dead} are citations THIS ARCHIVE CHOSE and "
              f"{n - chosen_dead} were inherited from the GEDCOM export. Only the first "
              f"number is anybody's job here.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Do the sources this archive cites still resolve?

check_links.py tests the links INSIDE the site. Nothing tested the links out of
it, and a dead citation looks exactly like a good one on the page: the reader
cannot tell, and neither could the build. This archive now cites Internet
Archive identifiers, National Archives references, Gazette issue numbers and a
handful of ordinary URLs, none of which it had ever checked.

It REPORTS, it does not gate. An archive.org outage is not a reason to refuse a
build, and a citation that 404s today may be a move rather than a loss — the
judgement is a person's. What the build owes the reader is to notice.

  python3 tools/check_cites.py            # report
  python3 tools/check_cites.py --slow     # include the archive.org item checks
"""
import os, re, sys, json, glob, urllib.request, urllib.error, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "src", "data")
UA = {"User-Agent": "darcy-archive-citation-check/1.0 (+https://daviddef.github.io/TheDArcy/)"}
URL = re.compile(r"https?://[^\s\"'<>)\]]+")
SKIP = re.compile(r"example\.com|localhost|127\.0\.0\.1", re.I)


def urls():
    seen = collections.defaultdict(set)
    for p in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        raw = open(p, encoding="utf-8", errors="replace").read()
        for m in URL.finditer(raw):
            u = m.group(0).rstrip(".,;")
            if not SKIP.search(u):
                seen[u].add(os.path.basename(p))
    return seen


def head(u, timeout=12):
    for method in ("HEAD", "GET"):
        try:
            r = urllib.request.Request(u, headers=UA, method=method)
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            if e.code == 405 and method == "HEAD":
                continue
            return e.code
        except Exception as e:
            if method == "GET":
                return str(e)[:40]
    return "?"


def main(argv):
    found = urls()
    hosts = collections.Counter(re.sub(r"^https?://([^/]+).*", r"\1", u) for u in found)
    print(f"cites: {len(found)} distinct external URL(s) across "
          f"{len({f for s in found.values() for f in s})} data file(s), "
          f"{len(hosts)} host(s)")
    # A 3xx is a redirect, not a loss, and a 403 is a site refusing a robot
    # rather than a citation that has died. The first run of this tool reported
    # "457 of 566 did not return 200" by counting all three as failures, which
    # is exactly the cry-wolf shape that makes a report stop being read.
    gone, blocked, moved = [], [], []
    for u in sorted(found):
        st = head(u)
        w = sorted(found[u])
        if isinstance(st, int) and 200 <= st < 300:
            continue
        elif isinstance(st, int) and 300 <= st < 400:
            moved.append((u, st, w))
        elif st in (401, 403, 429):
            blocked.append((u, st, w))
        else:
            gone.append((u, st, w))

    for u, st, where in gone:
        print(f"  warn  cites      {st}  {u[:86]}")
        print(f"                   cited in {', '.join(where)[:78]}")
    ok = len(found) - len(gone) - len(blocked) - len(moved)
    print(f"  {'warn' if gone else 'ok  '}  cites      {ok} resolve, {len(moved)} redirect, "
          f"{len(blocked)} refuse a robot (401/403/429), {len(gone)} did not answer")
    if gone:
        print(f"        only the {len(gone)} above are candidates for a dead citation — "
              f"a redirect is a move and a 403 is a door policy. Read them, do not obey them.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

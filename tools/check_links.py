#!/usr/bin/env python3
"""Every internal href in the built site, resolved. Exits non-zero on a break."""
import os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "dist")
BASE = "/TheDArcy"

have = set()
for r, _, fs in os.walk(D):
    for f in fs:
        p = "/" + os.path.relpath(os.path.join(r, f), D).replace(os.sep, "/")
        have.add(p)
        if f == "index.html":
            have.add(p[:-len("index.html")].rstrip("/") or "/")

bad, pages = collections.Counter(), 0
where = collections.defaultdict(set)
for r, _, fs in os.walk(D):
    for f in fs:
        if not f.endswith(".html"):
            continue
        pages += 1
        src = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
        page = "/" + os.path.relpath(os.path.join(r, f), D).replace(os.sep, "/")
        for h in re.findall(r'href="([^"]+)"', src):
            if h.startswith(("http", "mailto:", "#", "data:")):
                continue
            h = h.split("#")[0].split("?")[0]
            if not h.startswith("/"):
                continue
            t = (h[len(BASE):] if h.startswith(BASE) else h).rstrip("/") or "/"
            if t not in have and t + "/index.html" not in have and t != "/":
                bad[h] += 1
                where[h].add(page)

print(f"{pages} pages · {sum(bad.values())} broken internal links")
for k, v in bad.most_common(20):
    print(f"   {v:3d}  {k}\n        from {sorted(where[k])[:3]}")
sys.exit(1 if bad else 0)

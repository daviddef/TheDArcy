#!/usr/bin/env python3
"""The name-linking pass of the build: names index, then the kit's autolink.py, over the built HTML.

    python3 tools/autolink_pass.py          # the build in ARCHIVE_OUT (default site/dist)
    python3 tools/autolink_pass.py --gate   # the ratchet gate (kit checklinks.py) over the same build
    python3 tools/autolink_pass.py --gate --write-floor

18 October 2026. It replaces the browser script site/public/wholink.js, which linked names after the page had
rendered. The order inside the site's `npm run build` is: astro build, THIS PASS, then everything that reads
the built HTML (sitemap, the living gates, nav, inline, rows, prose), so every gate sees the linked output;
the ratchet gate runs last.

  1. tools/build_names_index.py writes the index (dead people with a page, one bearer: the page; several: the
     search) and the living list (outside the repository).
  2. A person's own name on that person's own page is not linked to itself (wholink.js never did; the kit's tool
     has no such rule): the first mention of it in each section is wrapped in <span data-no-autolink>, which the
     kit leaves alone, until none is left. The span adds no style and no text.
  3. The kit's autolink.py runs with the index, the living list and the two public prefixes.

THE FLOOR is .linkfloor.json at the repository root; `--gate` is checklinks.py with that file. It may only go
down: `--write-floor` locks a gain in and refuses while anything rose.
"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import outdir
import build_names_index as bni

KIT = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools")
sys.path.insert(0, KIT)
import autolink as al  # noqa: E402

FLOOR = os.path.join(ROOT, ".linkfloor.json")
PREFIXES = ["--allow-prefix", "/people/", "--allow-prefix", "/who/"]


def protect_self(dist, idx_path, live_path):
    """Wrap a person's own name, on that person's own page, in <span data-no-autolink>. Returns (pages, wraps)."""
    ln, lu = al.load_living(live_path)
    idx = al.load_index(idx_path, ln, lu, ["/people/", "/who/"], 2)
    pages = wraps = 0
    for kind in ("people", "who"):
        base = os.path.join(dist, kind)
        for slug in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            path = os.path.join(base, slug, "index.html")
            own = "/%s/%s/" % (kind, slug)
            names = idx.names_by_url.get(own)
            if not names or not os.path.isfile(path):
                continue
            # the entries that can compete for the same words: this person's own, any longer name that holds
            # one of theirs (the longer one must win), and every living name (they block, as in the real run)
            sub = al.Index()
            sub.raw_url = idx.raw_url
            for first, lst in idx.by_first.items():
                keep = [e for e in lst if e.kind == "living" or e.url == own or any(n in e.key for n in names)]
                if keep:
                    sub.by_first[first] = keep
            html = al.read_page(path)
            before, hit = html, 0
            while True:
                sc = al.scan_html(html, sub, "main")
                mine = [t for t in sc.inserts if al.norm_url(t[2]) == own]
                if not mine:
                    break
                out, last = [], 0
                for (a, b, _u, _k) in mine:
                    out += [html[last:a], "<span data-no-autolink>", html[a:b], "</span>"]
                    last = b
                out.append(html[last:])
                html = "".join(out)
                hit += len(mine)
            if html != before:
                al.write_page(path, html)
                pages += 1
                wraps += hit
    return pages, wraps


def drop_person_pages(path):
    """Take the /people/ and /who/ addresses out of the written floor (see the docstring)."""
    d = json.load(open(path, encoding="utf-8"))
    keep = {u: n for u, n in d["pages"].items() if not u.startswith(("/people/", "/who/"))}
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{\n "version": %d,\n "note": %s,\n "pages": {\n' % (d["version"], json.dumps(d["note"] + " The /people/ and /who/ pages are left out on purpose: their addresses are names, and the gate holds a page the floor does not list to 0 (tools/autolink_pass.py).", ensure_ascii=False)))
        fh.write(",\n".join("  %s: %d" % (json.dumps(k, ensure_ascii=False), keep[k]) for k in sorted(keep)))
        fh.write("\n }\n}\n")
    print("  ..    floor: %d page(s) listed, %d under /people/ and /who/ left out (held to 0)" % (len(keep), len(d["pages"]) - len(keep)))


def run_kit(script, args):
    return subprocess.call([sys.executable, os.path.join(KIT, script)] + args, cwd=os.path.join(ROOT, "site"))


def main(argv):
    dist = outdir.out()
    idx_path, live_path = bni.paths(dist)
    if "--gate" in argv:
        extra = ["--write-floor"] if "--write-floor" in argv else []
        rc = run_kit("checklinks.py", ["--dist", dist, "--index", idx_path, "--living", live_path,
                                       "--floor", FLOOR, "--new-page-max", "0"] + PREFIXES + extra)
        if extra and rc == 0:
            drop_person_pages(FLOOR)
        return rc
    rc = bni.main_with(dist)
    if rc:
        return rc
    p, w = protect_self(dist, idx_path, live_path)
    print("  ..    a person's own name left unlinked on their own page: %d mention(s) on %d page(s)" % (w, p))
    return run_kit("autolink.py", ["--dist", dist, "--index", idx_path, "--living", live_path] + PREFIXES)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

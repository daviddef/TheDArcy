#!/usr/bin/env python3
"""Do the family LINES hold? A page for a name the direct line carries, and nobody it should not have.

site/src/data/family-lines.json names the surnames that get a page at /families/<slug>/ without being
one of the thirteen clusters. Each page lists ONLY people the archive already publishes. This reads the
committed data and the BUILT pages (never the GEDCOM, so it runs in the deploy), works out in Python who
should be on each page (tools/familylines.py, a second writing of the rule in src/lib/familyLines.js),
and refuses when the build disagrees.

WHAT IS CHECKED (each has a planted fault in `controls()`; run with --controls to see every one fail):

  config      the file declares lines; slugs are unique and do not collide with a cluster's address; no
              surname key belongs to two lines; a key is lowercase and has no apostrophe or bracket
  members     every line has at least one published person (an empty line is a page about nobody)
  page        the page is built, is indexable, has a title, a description of 30 to 200 characters and a
              canonical naming itself
  rows        the people drawn as ROWS on the page are exactly the people who belong to the line: nobody
              missing, nobody extra, nobody twice
  copy        a declared copy (same-person.json) is not a row
  living      a living person's row carries no year and no 'b.'/'d.', and the living person's name appears
              nowhere on the page outside their row (the lede, the direct-line table, the connections)
  index       /families/ links to every line
  nav         the navigation on /families/ links to every line
  sitemap     every line page is in the sitemap
  not-empty   a build with no line pages does not pass

    python3 tools/check_family_lines.py             # gate the build
    python3 tools/check_family_lines.py --controls  # plant every fault in a copy and show each is caught
"""
import os, re, sys, json, html, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import familylines as FL
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(ROOT, "site", _o) if _o else os.path.join(ROOT, "site", "dist")

ROW_OPEN = '<div class="dsc-gen"'
ROW_END = re.compile(r'<h3|</section>|<p class="small"')
NM = re.compile(r'<a class="dsc-nm" href="([^"]*)"')
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
CANON = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
DESC = re.compile(r'<meta name="description" content="([^"]*)"')
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
NOINDEX = re.compile(r'<meta[^>]*name=["\']robots["\'][^>]*noindex', re.I)


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read()


def slug_of_href(h):
    m = re.search(r"/people/([^/?#]+)", h)
    return m.group(1) if m else None


def rows_of(page):
    """The raw HTML of every Descent row, each cut where the Descent stops (a group heading, the end of the
    section, the closing paragraph)."""
    out = []
    for seg in page.split(ROW_OPEN)[1:]:
        m = ROW_END.search(seg)
        out.append(ROW_OPEN + (seg[:m.start()] if m else seg))
    return out


def text_outside_rows(page):
    """The page body with every Descent row removed, as plain text."""
    body = page[page.find("<main"):page.find("</main>")] if "<main" in page else page
    for r in rows_of(page):
        body = body.replace(r, " ")
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", body))


def check_page(page, line, want, copies_slugs, living, site=""):
    """Failures (a list of strings) for ONE built line page. `want` is {slug: record} for the people who
    belong; `living` is {slug: name}. Pure, so --controls can feed it a damaged page."""
    f = []
    label = f"/families/{line['slug']}/"
    t = TITLE.search(page)
    if not t or not t.group(1).strip():
        f.append(f"{label} has no <title>")
    d = DESC.search(page)
    if not d or not (30 <= len(html.unescape(d.group(1))) <= 200):
        f.append(f"{label} description is {'absent' if not d else str(len(html.unescape(d.group(1)))) + ' characters'}, not 30 to 200")
    if NOINDEX.search(page):
        f.append(f"{label} is noindex: a family page is about a name and should be in the sitemap")
    c = CANON.search(page)
    if not c or not c.group(1).rstrip("/").endswith(label.rstrip("/")):
        f.append(f"{label} canonical is {c.group(1) if c else 'absent'}, not its own address")

    blocks = rows_of(page)
    got = []
    block_of = {}
    for b in blocks:
        m = NM.search(b)
        s = slug_of_href(m.group(1)) if m else None
        if s:
            got.append(s)
            block_of.setdefault(s, b)
    seen = {}
    for s in got:
        seen[s] = seen.get(s, 0) + 1
    for s, n in seen.items():
        if n > 1:
            f.append(f"{label} lists /people/{s}/ as a row {n} times")
    for s in want:
        if s not in seen:
            f.append(f"{label} is missing a row for /people/{s}/")
    for s in seen:
        if s in copies_slugs:
            f.append(f"{label} lists /people/{s}/, a declared copy (same-person.json), as a row")
        elif s not in want:
            f.append(f"{label} lists /people/{s}/, who does not belong to the {line['surname']} line")

    for s, name in living.items():
        b = block_of.get(s, "")
        plain = html.unescape(re.sub(r"<[^>]+>", " ", b))
        if YEAR.search(plain) or re.search(r"\b[bd]\.\s", plain):
            f.append(f"{label} shows a year or a b./d. in the row of a living person (/people/{s}/)")
        if name and name in text_outside_rows(page):
            f.append(f"{label} names the living person /people/{s}/ outside their row")
    return f


def check_site(dist, lines, want_by_line, copies_slugs, living_by_line, site):
    fails = []
    if not lines:
        return ["family-lines.json declares no lines: a gate with nothing to check cannot fail"]
    fam_index = os.path.join(dist, "families", "index.html")
    idx = read(fam_index) if os.path.exists(fam_index) else ""
    sm_path = os.path.join(dist, "sitemap.xml")
    sitemaps = [sm_path] if os.path.exists(sm_path) else []
    locs = set()
    for p in sitemaps:
        locs |= {l.rstrip("/") for l in re.findall(r"<loc>([^<]*)</loc>", read(p))}
    if not idx:
        fails.append("/families/ is not built")
    built = 0
    for l in lines:
        p = os.path.join(dist, "families", l["slug"], "index.html")
        label = f"/families/{l['slug']}/"
        if not os.path.exists(p):
            fails.append(f"{label} is not built")
            continue
        built += 1
        fails += check_page(read(p), l, want_by_line[l["slug"]], copies_slugs, living_by_line[l["slug"]], site)
        if idx:
            n = len(re.findall(r'href="[^"]*/families/%s/?"' % re.escape(l["slug"]), idx))
            if n < 2:
                # once in the navigation, once in the index's own card
                fails.append(f"/families/ links to {label} {n} time(s); the index card and the navigation should each link it")
            nav = re.search(r'<nav class="topnav".*?</nav>', idx, re.S)
            if not nav or not re.search(r'href="[^"]*/families/%s/?"' % re.escape(l["slug"]), nav.group(0)):
                fails.append(f"the navigation on /families/ does not link {label}")
        if sitemaps and (site + label).rstrip("/") not in locs:
            fails.append(f"{label} is not in the sitemap")
    if not sitemaps:
        fails.append("no sitemap.xml in the build: the line pages cannot be shown to be in it")
    if built == 0:
        fails.append("no line page is built: nothing was examined")
    return fails


def check_config(cfg, cluster_slugs, populated):
    f = []
    lines = cfg.get("lines") or []
    if not lines:
        f.append("config: family-lines.json declares no lines")
    slugs_seen, keys_seen = {}, {}
    for l in lines:
        s = l.get("slug", "")
        if not s or s != re.sub(r"[^a-z0-9-]", "", s):
            f.append(f"config: slug {s!r} is not lowercase a-z, 0-9 and hyphens")
        if s in slugs_seen:
            f.append(f"config: slug {s} appears twice")
        slugs_seen[s] = 1
        if s in cluster_slugs:
            f.append(f"config: /families/{s}/ is already one of the thirteen clusters")
        if not l.get("keys"):
            f.append(f"config: line {s} has no keys")
        for k in l.get("keys", []):
            if k != FL.surname_key(k) or not k:
                f.append(f"config: key {k!r} of {s} is not in key form ({FL.surname_key(k)!r})")
            if k in keys_seen and keys_seen[k] != s:
                f.append(f"config: key {k!r} belongs to both {keys_seen[k]} and {s}")
            keys_seen[k] = s
        if not populated.get(s):
            f.append(f"members: line {s} has no published person: a page about nobody")
    return f


def gate():
    cfg = FL.config()
    lines = cfg.get("lines") or []
    by_line = FL.members()
    sl = FL.slugs()
    cp = {sl[i] for i in FL.copies() if i in sl}
    want = {s: {sl[r["id"]]: r for r in rs if r["id"] in sl} for s, rs in by_line.items()}
    living = {s: {k: r["name"] for k, r in w.items() if r.get("living")} for s, w in want.items()}
    import slugrule
    clusters = [slugrule.kebab(f["surname"]) for f in FL._j("families.json", [])]
    fails = check_config(cfg, set(clusters), {s: len(w) for s, w in want.items()})
    m = re.search(r"\bsite:\s*['\"]([^'\"]+)['\"]", read(os.path.join(ROOT, "site", "astro.config.mjs")))
    site = (m.group(1) if m else "").rstrip("/")
    fails += check_site(DIST, lines, want, cp, living, site)
    for x in fails:
        print("  FAIL  familylines " + x)
    if fails:
        print(f"  FAIL  familylines {len(fails)} problem(s) across {len(lines)} line(s)")
        return 1
    n = sum(len(w) for w in want.values())
    print(f"  ok    familylines {len(lines)} family lines built, {n} people drawn as rows, none of them a declared copy; "
          f"each is in the index, the navigation and the sitemap")
    return 0


# ── planted faults ─────────────────────────────────────────────────────────────────────────────

def controls():
    """Damage a copy and show the gate notices. Returns the number of faults that were NOT caught."""
    cfg = FL.config()
    lines = cfg["lines"]
    by_line = FL.members()
    sl = FL.slugs()
    want = {s: {sl[r["id"]]: r for r in rs if r["id"] in sl} for s, rs in by_line.items()}
    line = next(l for l in lines if len(want[l["slug"]]) >= 3)
    s = line["slug"]
    page_path = os.path.join(DIST, "families", s, "index.html")
    if not os.path.exists(page_path):
        print(f"  FAIL  familylines --controls needs a build with {page_path}")
        return 1
    good = read(page_path)
    w = want[s]
    cp = {"a-declared-copy"}
    missed = 0

    def expect(name, fails, needle):
        nonlocal missed
        hit = any(needle in x for x in fails)
        print(f"  {'caught' if hit else 'MISSED'}  {name}" + ("" if hit else f"   (got: {fails[:2]})"))
        if not hit:
            missed += 1

    base = check_page(good, line, w, cp, {})
    print(f"  {'ok    ' if not base else 'FAIL  '}  positive control: the real page of {s} passes" + ("" if not base else f" (got {base[:2]})"))
    missed += 1 if base else 0

    rows = rows_of(good)
    first_slug = slug_of_href(NM.search(rows[0]).group(1))
    # 1. a person who belongs is missing
    bad = good.replace(rows[0], "", 1)
    expect("a member's row removed", check_page(bad, line, w, cp, {}), "is missing a row")
    # 2. a stranger as a row
    stranger = '<div class="dsc-gen"><div class="dsc-card"><a class="dsc-nm" href="/people/not-a-member/">Not A Member</a></div></div>'
    bad = good.replace(rows[0], rows[0] + stranger, 1)
    expect("a stranger drawn as a row", check_page(bad, line, w, cp, {}), "does not belong")
    # 3. a declared copy as a row
    cprow = '<div class="dsc-gen"><div class="dsc-card"><a class="dsc-nm" href="/people/a-declared-copy/">A Copy</a></div></div>'
    bad = good.replace(rows[0], rows[0] + cprow, 1)
    expect("a declared copy drawn as a row", check_page(bad, line, w, cp, {}), "declared copy")
    # 4. a member twice
    bad = good.replace(rows[0], rows[0] + rows[0], 1)
    expect("a member drawn twice", check_page(bad, line, w, cp, {}), "times")
    # 5. a living member's row carrying a year (planted value no living person has: 1799)
    lw = {**w, "planted-living": {"name": "Planted Livingperson"}}
    liv_row = '<div class="dsc-gen"><div class="dsc-card"><a class="dsc-nm" href="/people/planted-living/">Planted Livingperson</a><div class="dsc-dt">b. 1799</div></div></div>'
    bad = good.replace(rows[0], rows[0] + liv_row, 1)
    expect("a living person's row with a year", check_page(bad, line, lw, cp, {"planted-living": "Planted Livingperson"}), "a year or a b./d.")
    clean_row = liv_row.replace('<div class="dsc-dt">b. 1799</div>', "")
    ok = check_page(good.replace(rows[0], rows[0] + clean_row, 1), line, lw, cp, {"planted-living": "Planted Livingperson"})
    print(f"  {'ok    ' if not ok else 'FAIL  '}  positive control: a living row with a name and nothing else passes" + ("" if not ok else f" (got {ok[:2]})"))
    missed += 1 if ok else 0
    # 6. a living name outside the row
    bad = good.replace("<main", "<main><p>Planted Livingperson was here</p><span hidden", 1)
    expect("a living name outside their row", check_page(bad.replace(rows[0], rows[0] + clean_row, 1), line, lw, cp, {"planted-living": "Planted Livingperson"}), "outside their row")
    # 7. noindex
    expect("the page made noindex", check_page(good.replace("</head>", '<meta name="robots" content="noindex"></head>', 1), line, w, cp, {}), "noindex")
    # 8. canonical elsewhere
    expect("canonical pointing elsewhere", check_page(re.sub(r'(<link[^>]*rel="canonical"[^>]*href=")[^"]*', r"\1https://example.invalid/x/", good, count=1), line, w, cp, {}), "canonical")
    # 9. description too short
    expect("a description of 5 characters", check_page(re.sub(r'(<meta name="description" content=")[^"]*', r"\1short", good, count=1), line, w, cp, {}), "description")

    # site-level, in a throwaway dist
    tmp = tempfile.mkdtemp(prefix="famlines-")
    try:
        def build_dist(drop=None):
            d = os.path.join(tmp, "dist" + str(abs(hash(drop))))
            shutil.rmtree(d, ignore_errors=True)
            for l in lines:
                os.makedirs(os.path.join(d, "families", l["slug"]), exist_ok=True)
                src = os.path.join(DIST, "families", l["slug"], "index.html")
                if drop != ("page", l["slug"]) and os.path.exists(src):
                    shutil.copy(src, os.path.join(d, "families", l["slug"], "index.html"))
            idx = read(os.path.join(DIST, "families", "index.html"))
            if drop and drop[0] == "index":
                idx = idx.replace(f"/families/{drop[1]}/", "/families/gone/")
            open(os.path.join(d, "families", "index.html"), "w", encoding="utf-8").write(idx)
            m = re.search(r"\bsite:\s*['\"]([^'\"]+)['\"]", read(os.path.join(ROOT, "site", "astro.config.mjs")))
            site = (m.group(1) if m else "").rstrip("/")
            locs = "".join(f"<url><loc>{site}/families/{l['slug']}/</loc></url>" for l in lines if drop != ("sitemap", l["slug"]))
            open(os.path.join(d, "sitemap.xml"), "w").write(f"<urlset>{locs}</urlset>")
            return d, site
        for name, drop, needle in [
            ("a line page not built", ("page", s), "is not built"),
            ("a line missing from the sitemap", ("sitemap", s), "not in the sitemap"),
            ("a line missing from the index and the navigation", ("index", s), "links to"),
        ]:
            d, site = build_dist(drop)
            living = {k: {} for k in want}
            expect(name, check_site(d, lines, want, cp, living, site), needle)
        d, site = build_dist(None)
        ok = check_site(d, lines, want, cp, {k: {} for k in want}, site)
        print(f"  {'ok    ' if not ok else 'FAIL  '}  positive control: an undamaged copy of the line pages passes" + ("" if not ok else f" (got {ok[:2]})"))
        missed += 1 if ok else 0
        empty = os.path.join(tmp, "empty")
        os.makedirs(os.path.join(empty, "families"), exist_ok=True)
        open(os.path.join(empty, "families", "index.html"), "w").write("<html></html>")
        expect("an empty build", check_site(empty, lines, want, cp, {k: {} for k in want}, site), "not built")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # config
    sample = json.loads(json.dumps(cfg))
    pop = {l["slug"]: 1 for l in lines}
    expect("two lines with one slug", check_config({"lines": sample["lines"] + [dict(sample["lines"][0])]}, set(), pop), "twice")
    dup = json.loads(json.dumps(sample)); dup["lines"][1]["keys"] = list(dup["lines"][0]["keys"])
    expect("one surname key in two lines", check_config(dup, set(), pop), "belongs to both")
    expect("a line colliding with a cluster", check_config(sample, {lines[0]["slug"]}, pop), "already one of the thirteen")
    expect("a line with nobody in it", check_config(sample, set(), {**pop, lines[0]["slug"]: 0}), "a page about nobody")
    expect("a key not in key form", check_config({"lines": [{"slug": "x", "keys": ["Von Y"]}]}, set(), {"x": 1}), "not in key form")
    expect("no lines at all", check_config({"lines": []}, set(), {}), "declares no lines")
    print(f"  {missed} planted fault(s) not caught" if missed else "  every planted fault was caught")
    return missed


if __name__ == "__main__":
    if "--controls" in sys.argv:
        sys.exit(1 if controls() else 0)
    sys.exit(gate())

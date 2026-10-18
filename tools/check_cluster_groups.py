#!/usr/bin/env python3
"""Do the thirteen family pages say how many groups they are, and does /families/ count everybody?

THE FAULTS THIS EXISTS FOR (lines audit, 18 October 2026):
  - /families/d-arcy/ said "All 81 people this archive publishes under D'Arcy" and drew one list, when the
    published people fall into two groups the archive does not join. The group test existed, but only on the
    twelve line pages. It now runs on all thirteen clusters (src/lib/familyLines.js, groupsFor).
  - 384 published people were on no surname page and the site did not say so. /families/ now counts every
    one of the 844 into exactly one place (src/lib/familyLines.js, unplacedData).
  - /trees/ typed 473, 67 and 112 for what the data held as 844, 81 and 108. Its figures are now filled in
    from the data (src/pages/trees.astro); this refuses a build in which a figure printed there differs from
    the data.

Like check_family_lines.py this reads the committed data and the BUILT pages, never the GEDCOM, and works the
answer out a second time in Python (tools/familylines.py), so the gate does not take the page's word for it.

    python3 tools/check_cluster_groups.py             # gate the build
    python3 tools/check_cluster_groups.py --controls  # plant every fault in a copy and show each is caught
"""
import os, re, sys, json, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import familylines as FL
import slugrule
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(ROOT, "site", _o) if _o else os.path.join(ROOT, "site", "dist")

GROUP = re.compile(r"<h3[^>]*>\s*Group (\d+)\s*(?:&mdash;|—)\s*(\d+) (?:person|people)\s*</h3>")
UNPLACED = re.compile(r'data-unplaced=\'([^\']*)\'|data-unplaced="([^"]*)"')


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read()


def check_cluster_page(page, label, want_sizes):
    """The groups a cluster page shows are the groups the data gives: none for one group, else every one."""
    f = []
    got = [(int(a), int(b)) for a, b in GROUP.findall(page)]
    if len(want_sizes) <= 1:
        if got:
            f.append(f"{label} shows {len(got)} group heading(s) but the published people are one group")
        return f
    if [n for _, n in got] != want_sizes:
        f.append(f"{label}: the data gives {len(want_sizes)} groups {want_sizes} and the page shows {[n for _, n in got]}")
    elif [i for i, _ in got] != list(range(1, len(got) + 1)):
        f.append(f"{label}: the group headings are not numbered 1 to {len(got)}")
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    if not re.search(r"fall into\s+%d groups" % len(want_sizes), re.sub(r"\s+", " ", text)):
        f.append(f"{label}: the page does not say the people fall into {len(want_sizes)} groups")
    return f


def check_unplaced(idx, want):
    f = []
    m = UNPLACED.search(idx)
    if not m:
        return ["/families/ carries no data-unplaced block: the people on no surname page are not counted there"]
    try:
        got = json.loads(html.unescape(m.group(1) or m.group(2)))
    except Exception as e:
        return [f"/families/ data-unplaced is not JSON ({e})"]
    for k, v in want.items():
        if got.get(k) != v:
            f.append(f"/families/ says {k} = {got.get(k)} and the data gives {v}")
    if sum(want[k] for k in ("cluster", "line", "copies", "falco", "elsewhere", "unnamed", "other")) != want["total"]:
        f.append("the data itself does not add up: every published person must be counted exactly once")
    return f


def check_trees(page, facts):
    """Every figure /trees/ prints that the data also holds."""
    f = []
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    for needle in facts:
        if needle not in text:
            f.append(f"/trees/ does not print \"{needle}\", which the data gives")
    for stale in ("473 of them", "67 published", "112 published"):
        if stale in text:
            f.append(f"/trees/ still prints the stale figure \"{stale}\"")
    return f


def expectations():
    ppl = FL.cluster_people()
    sizes = {s: FL.group_sizes(rs) for s, rs in ppl.items()}
    fams = {f["surname"]: f for f in FL._j("families.json", [])}
    un = FL.unplaced()
    prov = FL._j("provenance.json", {})
    by, _ = FL.published()
    hornby = sum(1 for v in prov.values() if v.get("graft") == "Hornby")
    keele = sum(1 for v in prov.values() if v.get("graft") == "Keele")
    da, sn = "D'Arcy", "Sneyd"
    facts = [f"{fams[da]['total']} people, {len(ppl[da])} published",
             f"{fams[sn]['total']} people, {len(ppl[sn])} published",
             f"{hornby} people reach this archive only through it",
             f"{keele} people, every one of them behind a single link",
             f"{len(by)} of them, each carrying the confidence it rests on"]
    return ppl, sizes, un, facts


def gate():
    ppl, sizes, un, facts = expectations()
    fails = []
    built = 0
    for s in ppl:
        slug = slugrule.kebab(s)
        p = os.path.join(DIST, "families", slug, "index.html")
        if not os.path.exists(p):
            fails.append(f"/families/{slug}/ is not built")
            continue
        built += 1
        fails += check_cluster_page(read(p), f"/families/{slug}/", sizes[s])
    idx = os.path.join(DIST, "families", "index.html")
    fails += check_unplaced(read(idx), un) if os.path.exists(idx) else ["/families/ is not built"]
    tp = os.path.join(DIST, "trees", "index.html")
    fails += check_trees(read(tp), facts) if os.path.exists(tp) else ["/trees/ is not built"]
    if built == 0:
        fails.append("no cluster page is built: nothing was examined")
    for x in fails:
        print("  FAIL  clustergroups " + x)
    if fails:
        print(f"  FAIL  clustergroups {len(fails)} problem(s)")
        return 1
    multi = {s: z for s, z in sizes.items() if len(z) > 1}
    print(f"  ok    clustergroups {built} cluster pages: {len(multi)} fall into more than one group "
          f"({', '.join(f'{s} {z}' for s, z in multi.items()) or 'none'}) and say so; "
          f"{un['total']} published people each counted once on /families/ ({un['cluster'] + un['line']} placed, "
          f"{un['copies']} copies, {un['total'] - un['cluster'] - un['line'] - un['copies']} on no surname page); /trees/ prints the data's figures")
    return 0


def controls():
    ppl, sizes, un, facts = expectations()
    missed = 0

    def expect(name, fails, needle):
        nonlocal missed
        hit = any(needle in x for x in fails)
        print(f"  {'caught' if hit else 'MISSED'}  {name}" + ("" if hit else f"   (got: {fails[:2]})"))
        if not hit:
            missed += 1

    multi = next((s for s, z in sizes.items() if len(z) > 1), None)
    single = next(s for s, z in sizes.items() if len(z) == 1)
    if multi is None:
        print("  FAIL  clustergroups --controls: no cluster falls into more than one group, so there is no page to damage")
        return 1
    good = read(os.path.join(DIST, "families", slugrule.kebab(multi), "index.html"))
    ok = check_cluster_page(good, "x", sizes[multi])
    print(f"  {'ok    ' if not ok else 'FAIL  '}  positive control: the real page of {multi} passes" + ("" if not ok else f" (got {ok[:2]})"))
    missed += 1 if ok else 0
    last = GROUP.findall(good)[-1]
    expect("a group heading removed", check_cluster_page(re.sub(r"<h3[^>]*>\s*Group %s\s*(?:&mdash;|—)[^<]*</h3>" % last[0], "", good), "x", sizes[multi]), "the data gives")
    expect("a page that says nothing of its groups", check_cluster_page(good.replace("fall into", "belong to"), "x", sizes[multi]), "does not say")
    one = read(os.path.join(DIST, "families", slugrule.kebab(single), "index.html"))
    expect("a single-group page given a group heading", check_cluster_page(one.replace("</main>", "<h3>Group 1 &mdash; 3 people</h3></main>"), "x", sizes[single]), "one group")
    idx = read(os.path.join(DIST, "families", "index.html"))
    ok = check_unplaced(idx, un)
    print(f"  {'ok    ' if not ok else 'FAIL  '}  positive control: the real /families/ passes" + ("" if not ok else f" (got {ok[:2]})"))
    missed += 1 if ok else 0
    expect("an unplaced total off by one", check_unplaced(idx, {**un, "other": un["other"] + 1}), "the data gives")
    expect("the unplaced block removed", check_unplaced(re.sub(r"data-unplaced=(['\"]).*?\1", "", idx, count=1, flags=re.S), un), "carries no data-unplaced")
    expect("people counted twice in the data", check_unplaced(idx, {**un, "total": un["total"] + 1}), "exactly once")
    tp = read(os.path.join(DIST, "trees", "index.html"))
    ok = check_trees(tp, facts)
    print(f"  {'ok    ' if not ok else 'FAIL  '}  positive control: the real /trees/ passes" + ("" if not ok else f" (got {ok[:2]})"))
    missed += 1 if ok else 0
    expect("a stale figure on /trees/", check_trees(tp.replace(" published", " published 67 published", 1), facts), "stale figure")
    expect("a figure the data does not give", check_trees(tp, facts + ["999 people, 999 published"]), "does not print")
    print(f"  {missed} planted fault(s) not caught" if missed else "  every planted fault was caught")
    return missed


if __name__ == "__main__":
    if "--controls" in sys.argv:
        sys.exit(1 if controls() else 0)
    sys.exit(gate())

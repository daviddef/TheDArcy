#!/usr/bin/env python3
"""Prose written into a data file that reaches no page.

Written 27 September 2026 after David asked whether the research of the last
few days was actually published. The commits were clean, the deploys were
green, and two things were still invisible: 46 of 66 errands carried a one-line
statement of stakes that the page never rendered, and hannah-baptism.json held
a whole block — four tested claims about Hannah's mother, including her death
registration — that no template referred to.

Neither was a research failure and neither was a build failure. The data was
committed, the gates passed, GitHub Pages served it. A FILE IN THE REPOSITORY
IS NOT A PUBLISHED CLAIM; only a page is.

This REPORTS and does not refuse. Some prose in these files is deliberately
internal — the reason a decision is watched, the wording of a rule a gate
applies — and a check that cannot tell those apart would be turned off within
a week. The list is meant to be read by a person, and ALLOW carries the files
whose prose is written for tools rather than readers.

AND A FINER DISTINCTION, 28 September. A neighbouring session put it better
than the version above: the question is not «does this reach a page» but «does
it reach a page a reader would browse, or only a log page that points at
itself». A finding that appears solely on /changes or /searched is RECORDED and
not published. Those pages are read by somebody auditing this archive, not by
somebody looking up an ancestor, and a record line whose only home is the day
log is evidence filed rather than evidence shown.

The log pages are not hardcoded here. retired.json already declares them, as
the pages permitted to restate a withdrawn reading BECAUSE THEIR SUBJECT IS THE
WITHDRAWAL — the same set, declared for the same reason, and using it twice
means the two checks cannot drift apart.

    python3 tools/check_unpublished.py            # the report
    python3 tools/check_unpublished.py --list     # every string, in full
"""
import argparse, collections, glob, html, json, os, re, sys

OWNERS, LOGS = {}, []

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import outdir

# Generated from the tree, or written for a tool to read rather than a reader.
ALLOW = {
    "families.json", "ancestors.json", "line.json", "mentions.json",
    "person-records.json", "register.json", "provenance.json", "dossiers.json",
    "namefold.json", "trees.json", "households.json", "marriages.json",
    "graves.json", "places.json", "confidence.json", "decisions.json",
    "place-same.json", "living-rule.json", "namefold-deny.json", "retired.json",
    "audit.json", "living.json", "crossread.json",
}
MIN = 90


def norm(s):
    """Both sides folded the same way, or the difference is the measurement.

    The first run of this compared data with its markdown stripped against
    pages with theirs left in, and reported 201 unpublished strings where
    there were 71. 130 of them were the comparison, not the archive.
    """
    s = html.unescape(s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)     # markdown link -> its text
    s = re.sub(r"[*«»“”‘’'\"`_]", "", s)
    # WHITESPACE REMOVED ENTIRELY, not collapsed. Stripping tags turns
    # «<strong>ASHLEWORTH</strong>,» into «ASHLEWORTH ,» and the data side has
    # no space before that comma, so a collapsed-space comparison reported a
    # passage as unpublished while it sat on its own page. Comparing without
    # whitespace at all removes the whole class.
    return re.sub(r"\s+", "", s).lower()


def owners():
    """Which built page imports which data file, read from the templates.

    A log page's OWN data file legitimately appears only on that page:
    searched.json IS /searched. Counting those as «filed, not shown» produced
    1,151 hits on the first run and measured nothing except the obvious. What
    the question is actually about is a SUBJECT file — thomas-sinegar.json,
    hannah-baptism.json — whose prose surfaces only in a log.
    """
    out = collections.defaultdict(set)
    pat = re.compile(r'from\s+"[^"]*data/([A-Za-z0-9._-]+\.json)"')
    for src in glob.glob(os.path.join(ROOT, "site/src/pages/**/*.astro"), recursive=True):
        slug = os.path.relpath(src, os.path.join(ROOT, "site/src/pages"))[:-len(".astro")]
        slug = "" if slug == "index" else slug.replace(os.sep, "/")
        for m in pat.finditer(open(src, encoding="utf-8").read()):
            out[m.group(1)].add(slug)
    return out


def log_paths():
    """The pages whose subject is this archive's own process, as IT declares them."""
    try:
        with open(os.path.join(ROOT, "site/src/data/retired.json"), encoding="utf-8") as f:
            return [p.strip("/") for p in json.load(f).get("allow", [])]
    except Exception:
        return []


def pages():
    """Built pages, split into the ones a reader browses and the logs."""
    logs = log_paths()
    reader, log = [], []
    root = outdir.out()
    for r, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(r, f), root).replace(os.sep, "/")
            t = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
            t = re.sub(r"<(script|style)\b.*?</\1>", "", t, flags=re.S | re.I)
            txt = norm(re.sub("<[^>]+>", " ", t))
            slug = rel[:-len("/index.html")] if rel.endswith("/index.html") else rel
            (log if slug in logs else reader).append(txt)
    return reader, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    global OWNERS, LOGS
    OWNERS, LOGS = owners(), log_paths()
    reader, log = pages()
    if len(reader) + len(log) < 100:
        print(f"  FAIL  unpublished  only {len(reader) + len(log)} page(s) in "
              f"{outdir.name()} — the site is not built, so every string would "
              f"report as missing")
        return 1
    big = " || ".join(reader)
    logbig = " || ".join(log)

    found = collections.defaultdict(list)
    logged_only = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "site/src/data/*.json"))):
        name = os.path.basename(path)
        if name in ALLOW:
            continue
        # A log page's own source is not "filed, not shown" — it is the page.
        # Whether a log page owns this file decides ONE of the two questions,
        # not both. If it does, prose appearing only on a log page is that page
        # doing its job and is not "filed, not shown". Prose appearing on NO
        # page is still a fault either way — coverage.json lives on /searched,
        # and a coverage note that renders nowhere is exactly as lost as one in
        # a subject file. Skipping the whole file would have hidden that.
        log_owned = bool(OWNERS.get(name, set()) & set(LOGS))

        def walk(o, where="", log_owned=log_owned):
            if isinstance(o, str):
                s = norm(o)
                if len(s) >= MIN and not s.startswith("http") and s[:70] not in big:
                    # Recorded on a log page, or nowhere at all: different faults.
                    if s[:70] in logbig:
                        if not log_owned:
                            logged_only[name].append((where, o))
                    else:
                        found[name].append((where, o))
            elif isinstance(o, dict):
                for k, v in o.items():
                    if not str(k).startswith("_"):
                        walk(v, f"{where}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{where}[{i}]")

        walk(json.load(open(path, encoding="utf-8")))

    n_log = sum(len(v) for v in logged_only.values())
    if n_log:
        print(f"  ..    recorded    {n_log} passage(s) reach ONLY a log page "
              f"({', '.join('/' + p for p in log_paths())}) — filed, not shown")
        for name, rows in sorted(logged_only.items(), key=lambda kv: -len(kv[1]))[:6]:
            print(f"          {len(rows):>3}  {name}")
            for where, t in (rows if a.list else rows[:1]):
                print(f"                {where}")
                print(f"                “{t[:110]}…”")

    total = sum(len(v) for v in found.values())
    if not total:
        print(f"  ok    unpublished  every written passage in the data reaches a page")
        return 0
    print(f"  ..    unpublished  {total} passage(s) of prose reach no page, in "
          f"{len(found)} file(s) — a report, not a refusal")
    for name, rows in sorted(found.items(), key=lambda kv: -len(kv[1])):
        print(f"          {len(rows):>3}  {name}")
        for where, s in (rows if a.list else rows[:1]):
            print(f"                {where}")
            print(f"                “{s[:110]}…”")
    return 0


if __name__ == "__main__":
    sys.exit(main())

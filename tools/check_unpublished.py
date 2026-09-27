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

    python3 tools/check_unpublished.py            # the report
    python3 tools/check_unpublished.py --list     # every string, in full
"""
import argparse, collections, glob, html, json, os, re, sys

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
    return re.sub(r"\s+", " ", s).strip().lower()


def pages():
    out = []
    for r, _, fs in os.walk(outdir.out()):
        for f in fs:
            if f.endswith(".html"):
                t = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
                t = re.sub(r"<(script|style)\b.*?</\1>", "", t, flags=re.S | re.I)
                out.append(norm(re.sub("<[^>]+>", " ", t)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    built = pages()
    if len(built) < 100:
        print(f"  FAIL  unpublished  only {len(built)} page(s) in {outdir.name()} — "
              f"the site is not built, so every string would report as missing")
        return 1
    big = " || ".join(built)

    found = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "site/src/data/*.json"))):
        name = os.path.basename(path)
        if name in ALLOW:
            continue

        def walk(o, where=""):
            if isinstance(o, str):
                s = norm(o)
                if len(s) >= MIN and not s.startswith("http") and s[:70] not in big:
                    found[name].append((where, o))
            elif isinstance(o, dict):
                for k, v in o.items():
                    if not str(k).startswith("_"):
                        walk(v, f"{where}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{where}[{i}]")

        walk(json.load(open(path, encoding="utf-8")))

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

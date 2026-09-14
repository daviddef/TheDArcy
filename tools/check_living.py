#!/usr/bin/env python3
"""Who is alive in this archive — the kit decides whether any of them got out.

This archive's rule is the strictest in the estate: LIVING PEOPLE ARE NOT
PUBLISHED AT ALL — not hidden, not gated, absent from the output.
build_site_data.py applies it once, at the boundary between the research data
and the site, so that nobody can be living on one page and dead on another.
This is the check that the rule held, and it reads the BUILT HTML, because
source can be correct and output wrong: a living person's name reaches a page
through a deceased relative's spouses, parents and children long after they
were filtered out of the person list.

WHY THE NAMES ARE NOT COMMITTED. This tree holds over two thousand living
people. A file listing them, in a PUBLIC repository, would be precisely the
disclosure the rule exists to prevent — a machine-readable directory of living
relatives, committed forever to a git history. And a hand-kept list goes
stale. The GEDCOM is the authority, it is regenerated whenever the tree is
exported, and it is gitignored. So the names are read at check time and never
written down. What IS committed is site/src/data/living.json: the policy, the
exceptions and the counts. Exceptions need human judgement and version
control. Names need neither.

WHAT THIS FILE IS NOW. The matching — name phrases, exact-namesake
subtraction, longer-published-name subtraction, the combined single-pass
regex — was written here and now lives in the kit, where the other six
archives get it too. This file is what only this archive can do: open its own
tree and say who is alive. That split is the whole of the convergence.

    python3 tools/check_living.py            # gate the build
    python3 tools/check_living.py --verbose  # show what matched and why
"""
import os, sys, json, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "site", "node_modules", "@daviddef",
                                "archive-kit", "kit", "tools"))
from gedcom import load, display, classify_living          # noqa: E402
import checkliving                                          # noqa: E402

DIST = os.path.join(ROOT, "site", "dist")
DECL = os.path.join(ROOT, "site", "src", "data", "living.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=DIST)
    ap.add_argument("--declared", default=DECL)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not glob.glob(os.path.join(ROOT, "sources", "*.ged")):
        # Gitignored on purpose — it carries every living person in full — so CI
        # can never have it. A guard that cannot read its source has not passed;
        # but it must not fail a deploy it was never able to run either. So it
        # says which of those two happened, and never pretends to have checked.
        if os.environ.get("CI"):
            print("check_living: NOT RUN. The GEDCOM is gitignored, so CI cannot read "
                  "it. This gates locally, where the tree exists; in CI the kit's "
                  "check:living runs against the committed data.")
            return 0
        print("check_living: no GEDCOM under sources/. This guard reads the tree to "
              "learn who is alive, so a missing tree is a FAILURE, not a pass. "
              "(In CI the absence is expected and this exits 0 with a notice.)")
        return 1

    if not os.path.exists(a.declared):
        print(f"check_living: no declaration at {a.declared}. The exceptions are the "
              f"part a human has to judge, so a missing declaration is a FAILURE.")
        return 1
    decl = json.load(open(a.declared, encoding="utf-8"))
    # Two kinds of exception, kept apart on purpose. A NAMESAKE is not a living
    # person at all — a historical Richard Smith, a middle name inside a longer
    # one. A NAMED entry IS a living person this archive has decided to name.
    allow = set(decl.get("allow", []))
    allow |= {e["phrase"] for e in decl.get("namesakes", []) if e.get("phrase")}
    allow |= {e["phrase"] for e in decl.get("named", []) if e.get("phrase")}

    people, families = load()
    living_ids = classify_living(people, families)
    living = {checkliving.norm(display(people[p]) or "") for p in people if living_ids.get(p)}
    publish = {checkliving.norm(display(people[p]) or "") for p in people if not living_ids.get(p)}
    living.discard(""); publish.discard("")

    return checkliving.feed(
        a.dist, living, publish,
        allow=allow, allow_files=decl.get("allowFiles", []), quiet=a.quiet,
        label=f"{len(people):,} in the tree, {len(publish):,} published")


if __name__ == "__main__":
    sys.exit(main())

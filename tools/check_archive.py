#!/usr/bin/env python3
"""Every gate this archive wrote, run where the DEPLOY can see them.

28 September 2026. A neighbouring session pointed out that check_links.py — the
evidence gate, the one in the Mazza lineage — was not wired into anything. It
was in build.sh, which runs on this machine. It was not in `npm run build`,
which is what GitHub Actions runs, and Actions is what builds the site the
public reads.

Measured rather than assumed, and it was not one gate. TEN OF TWELVE were in
that position: atlas, controls, decisions, links, living-rule, namefold,
published, retired, secrets, unpublished. Only check_living.py had been wired.
So the published site was protected by the kit's gates and by nothing this
archive had written for itself, including every gate written that same day.

WHY NOT JUST RUN build.sh IN CI. It starts by reading the GEDCOM, and the
GEDCOM is gitignored because it carries living people in full. CI has no copy
and must never have one. So the gates that need only the committed data and the
built HTML come here, and the ones that need the tree stay behind.

The archive's own words for this, from the day before: only a page is a
published claim, a file in the repository is not. A gate nothing runs is the
same thing — a check in the repository is not a check on the build.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Gates that read committed data and built HTML. None of them opens the GEDCOM.
GATES = [
    "check_secrets.py",       # no credential in a tracked file
    "check_decisions.py",     # the five values that are a decision
    "check_links.py",         # links, anchors, AND evidence reaching its person
    "check_published.py",     # a claim that lost its source
    "check_retired.py",       # a withdrawn reading restated
    "check_controls.py",      # a null that names no control
    "check_namefold.py",      # a denied fold reaching the map
    "check_living_rule.py",   # a page hand-rolling the living test
    "check_atlas.py",         # pins claiming a precision they do not have
    "check_whosplit.py",      # one human split across two dossiers
    "check_unpublished.py",   # prose that reaches no page (reports, never refuses)
]


def main():
    failed = []
    for g in GATES:
        path = os.path.join(ROOT, "tools", g)
        if not os.path.exists(path):
            print(f"  FAIL  archive    {g} is listed here and not on disk")
            failed.append(g)
            continue
        r = subprocess.run([sys.executable, path], cwd=ROOT)
        if r.returncode != 0:
            failed.append(g)
    if failed:
        print(f"  FAIL  archive    {len(failed)} of {len(GATES)} gate(s) refused: "
              f"{', '.join(failed)}")
        return 1
    print(f"  ok    archive    {len(GATES)} archive gate(s) passed, in the build "
          f"the deploy actually runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

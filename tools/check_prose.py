#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The prose gate for living people: the kit's checkprose.py, run over what this archive's authors TYPE.

    python3 ../tools/check_prose.py                  # from site/: what `npm run check:prose` and the build run
    python3 ../tools/check_prose.py --require-tree   # a run that could not say who is living FAILS, even in CI

checkprose.py (kit/tools) fails when a hand-written page, a hand-edited data file or a note puts a year,
a date, a life-event word or a DNA result beside a living person's name, or when a JSON record naming a
living person carries a field beyond the standard (name, relationships, full town and country).
check_living.py guards the BUILT pages and the generated data; this guards what somebody typed.

THE FEED. Who is living is answered by tools/build_checkprose_feed.py, which asks gedcom.classify_living()
(the kit's living_rule.py, with the child's year passed) and is rebuilt on every run so it is never stale.
It holds names, so it lives OUTSIDE the repository.

EXIT CODES. 0 passed. 1 failed. 2 NOT RUN: the GEDCOM is gitignored (it carries every living person), so a
machine that does not have it cannot say who is living, and "cannot say" is not "nobody is". Locally that
STOPS the build. In CI (the variable CI is set, as GitHub Actions does) the build goes on and the log says,
in capitals, that this gate did not run and that this is NOT a pass; --require-tree turns that into a
failure there too. The deploy therefore never depends on a file CI cannot read.

WHICH FILES. The kit reads by default site/src/pages, notes/, docs/ and the top-level markdown. This adds
the hand-EDITED data files (HAND_EDITED), the components and layout (a sentence can be typed there) and the
letters in requests/. EVERY tracked file in site/src/data must be in HAND_EDITED or GENERATED: a new one
FAILS the gate until somebody who knows whether a person edits it or a script writes it says which.
GENERATED means a script rewrites it on every build (verified by running the generators and watching
which files changed, not by reading code), so its generator's own scrub gate is the guard and a fix here
would be undone by the next run. The eight data/*.tsv extracts are generated from the tree and covered by
check_living.py, which searches every tracked file.
"""
import os, sys, json, argparse, subprocess, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
CHECKPROSE = os.path.join(KIT_TOOLS, "checkprose.py")
ALLOW = os.path.join(ROOT, "checkprose-allow.json")
DATA = "site/src/data"

# Data files a person (or a person's session) edits. Each is read by the gate.
HAND_EDITED = {
    "abbas-kooli.json",
    "berkeley-woman.json",
    "bristol-chapels.json",
    "changes.json",  # the changelog, written by hand
    "chatham.json",
    "chew-magna.json",
    "confidence.json",  # the grading vocabulary
    "constantine.json",
    "coverage.json",  # what the indexes hold
    "crossread.json",
    "decisions.json",  # decisions, declared by hand and recomputed by a gate
    "errands.json",  # the errands page
    "eulogy.json",  # the eulogy page
    "fmp.json",
    "general-hewitt.json",
    "george-pitt.json",
    "hannah-baptism.json",
    "indexes.json",
    "jean-ward.json",
    "joseph-darcy.json",
    "living-rule.json",  # the living-rule page
    "margaret-jones.json",
    "namefold-deny.json",  # refused name folds
    "new-generations.json",
    "obituary.json",  # the 1827 obituary page
    "place-same.json",  # declared place folds
    "portsea.json",
    "printed.json",
    "questions.json",  # open questions
    "retired.json",  # withdrawn readings
    "robert-family.json",
    "same-person.json",  # declared duplicates
    "saniger-1608.json",
    "saniger-line.json",
    "saniger-place.json",
    "sanigers.json",
    "searched.json",  # the searches run, appended by hand
    "sneyds.json",
    "sources.json",  # the source register, edited by hand
    "spellings.json",
    "sussex-sisters.json",
    "swonhungre.json",
    "the-corps.json",
    "thomas-sinegar.json",
    "timeline.json",
    "trees.json",
    "wakefields.json",
    "worklist.json",  # the work list, written by hand
}

# Data files a script rewrites on every build. Their generator's own gate is the guard.
GENERATED = {
    "ancestors.json", "families.json", "line.json", "relatives.json",    # build_site_data.py, from the tree
    "places.json",                                                       # build_site_data.py
    "register.json", "provenance.json",                                  # build_register.py
    "dossiers.json", "person-records.json",                              # build_dossiers.py, build_person_records.py
    "households.json", "marriages.json", "graves.json",                  # build_family_pages.py
    "dna.json",                                                          # build_dna.py
    "mentions.json",                                                     # build_mentions.py
    "audit.json",                                                        # audit.py
    "living.json",                                                       # build_site_data.py; holds living NAMES by design
    "snapshot-summary.json",                                             # snapshot.py
    "namefold.json",                                                     # kit namefold.py
}

# Prose typed outside site/src/pages and notes/: components, the layout, and the letters to record offices.
EXTRA_INCLUDE = ["site/src/components/**/*.astro", "site/src/layouts/**/*.astro", "requests/**/*.md"]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tracked_data_files():
    r = subprocess.run(["git", "-C", ROOT, "ls-files", "-z", DATA], capture_output=True, text=True)
    return sorted(os.path.basename(f) for f in r.stdout.split("\0") if f)


def classify():
    """Return (include list, problems)."""
    names = tracked_data_files()
    problems = []
    for n in names:
        if n not in HAND_EDITED and n not in GENERATED:
            problems.append("%s/%s is in neither HAND_EDITED nor GENERATED in tools/check_prose.py: say whether a "
                            "person edits it or a script writes it" % (DATA, n))
    for n in sorted((HAND_EDITED | GENERATED) - set(names)):
        problems.append("tools/check_prose.py lists %s/%s, which is not a tracked file" % (DATA, n))
    for n in sorted(HAND_EDITED & GENERATED):
        problems.append("%s is listed as both hand-edited and generated" % n)
    return ["%s/%s" % (DATA, n) for n in sorted(HAND_EDITED)], problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--require-tree", action="store_true", help="a run that could not say who is living fails even in CI")
    ap.add_argument("--feed", help="where to write the feed (default: $CHECKPROSE_FEED or ~/.local/state/darcy-archive/)")
    a = ap.parse_args(argv)

    if not os.path.exists(CHECKPROSE):
        print("checkprose: FAIL, the kit has no checkprose.py at %s (pin the kit at 26a4cba or later)" % CHECKPROSE)
        return 1
    include, problems = classify()
    if problems:
        print("checkprose: FAIL (%d)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1

    fb = load_module(os.path.join(HERE, "build_checkprose_feed.py"), "build_checkprose_feed")
    feed, stats = fb.build()
    if feed is None:
        in_ci = bool(os.environ.get("CI")) and not a.require_tree
        print("checkprose: NOT RUN (%s). The prose gate could not say who is living, so it checked nothing; "
              "this is NOT a pass." % stats)
        if in_ci:
            print("checkprose: NOT RUN IN CI, AND LABELLED SO. It runs wherever the archive's people can be read.")
            return 0
        return 2
    if not feed["living"] or not feed["deadNames"]:
        print("checkprose: FAIL, the feed has %d living and %d dead names; refusing to pass on nothing" % (
            len(feed["living"]), len(feed["deadNames"])))
        return 1

    out = fb.feed_path(a.feed)
    fb.write(feed, out)
    print("checkprose: feed has %d living people (%d names) and %d dead names" % (
        len(feed["living"]), sum(len(x["names"]) for x in feed["living"]), len(feed["deadNames"])), flush=True)
    cmd = [sys.executable, CHECKPROSE, "--root", ROOT, "--feed", out]
    for inc in include + EXTRA_INCLUDE:
        cmd += ["--include", inc]
    if os.path.exists(ALLOW):
        cmd += ["--allow", ALLOW]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())

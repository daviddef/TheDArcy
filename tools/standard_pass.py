#!/usr/bin/env python3
"""The linking standard's gate (kit checkstandard.py), run on the build with this archive's inputs.

    python3 tools/standard_pass.py                # the gate over the build in ARCHIVE_OUT (default site/dist)
    python3 tools/standard_pass.py --table        # also print every page's five counts
    python3 tools/standard_pass.py --write-floor  # lock a gain in (the kit refuses while anything rose)

18 October 2026. The standard (kit/docs/linking-standard.md) counts, per narrative page, five things: names the linker should have
linked (L1, which is autolink's own count), people read from a record who have no entry (L2), passages that cite a record and
carry no link to it (L3), scans held but not beside their passage (L4), and forms no machine can resolve (L5). A page's count
may only go down: site/.standardfloor.json holds the ceilings, counts only, never a name and never an address of a person
(the 12 pages in scope are narratives, and /people/ and /who/ pages are never in scope).

The config is site/standard.json: the 12 narrative pages, the citation patterns (WIDTH: locators plus named sources, not event
wording, see its _note), the names settings, every exemption with its reason. It runs LAST in `npm run build`, after tools/
autolink_pass.py (which writes the names index and the living list this reads, from the same build) and after every step
that reads the built HTML.

IN CI there is no GEDCOM and no private feed. This gate needs neither: the names index is built from the committed data (the
built /people/ and /who/ pages and site/src/data/names-aliases.json), the living list is the part of the living set the
build itself holds (the noindex pages), exactly what tools/autolink_pass.py --gate uses, and the floor is committed. The one
check that needs this machine's feed (an index name that a living person also bears) is made where the index is written,
tools/build_names_index.py, on every local build.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import outdir
import build_names_index as bni

SITE = os.path.join(ROOT, "site")
KIT = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")


def main(argv):
    dist = outdir.out()
    idx_path, live_path = bni.paths(dist)
    cmd = [sys.executable, os.path.join(KIT, "checkstandard.py"), "--dist", dist, "--index", idx_path,
           "--config", os.path.join(SITE, "standard.json"), "--living", live_path,
           "--floor", os.path.join(SITE, ".standardfloor.json"), "--strict-config"]
    for a in argv:
        if a in ("--write-floor", "--table"):
            cmd.append(a)
        else:
            print("standard_pass: unknown argument %s" % a)
            return 2
    return subprocess.call(cmd, cwd=SITE)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env bash
# The whole pipeline, in the only order that works.
#
# Two passes are unavoidable: build_mentions.py and build_search.py both read
# the BUILT HTML, so the site has to exist before they can run, and their output
# has to exist before the final build can use it.
set -euo pipefail
cd "$(dirname "$0")"

# A build that is KILLED and a build that REFUSES look the same in a log, and
# they are not the same thing at all. Several archives share this machine and
# every one of them runs `astro build`; a stray `pkill -f "astro build"` or
# `pkill -f build.sh` — this session ran the second of those twice on
# 21 September 2026 — reaps every one of them. The SIGTERM lands inside a gate
# chain, so the run exits non-zero AFTER several checks have already printed
# `ok`, and the log reads like a clean run that failed on data at the end.
# The Lerena session lost three verify runs to it and spent two rounds hunting
# a fault in their own data.
#
# So say which it was, in the log, where the next reader will see it.
# To stop this archive's build without touching anybody else's, use
# scripts/stop-my-build.sh, which matches the absolute project path.
# The first version of this trap read $? in an EXIT handler, and that is only
# the exit status of the last CHILD. When the SCRIPT ITSELF is signalled — which
# is what `pkill -f build.sh` does, the pattern this session actually ran twice
# — $? is the status of whatever finished last, usually 0, so the trap said
# "every gate passed" over a build that had been killed mid-run. An instrument
# built to tell a killed build from a refusing one, answering a question nobody
# asked. Found by testing the fourth branch instead of the three that worked.
_signal=0
on_signal() { _signal=$1; exit $((128 + $1)); }
on_exit() {
  local code=$?
  if [ "$_signal" -ne 0 ]; then
    # The two kill paths get different sentences because they have different
    # remedies, which is the whole value of telling them apart.
    echo "EXIT=$((128 + _signal))  KILLED by signal $_signal, sent to THIS SCRIPT."
    echo "         Nothing is wrong with the data. Somebody reaped the script"
    echo "         itself, and a bare \`pkill -f build.sh\` or \`pkill -f astro\`"
    echo "         on this machine matches EVERY archive here, not one. Scope it"
    echo "         to a path — scripts/stop-my-build.sh does. Then re-run."
  elif [ "$code" -gt 128 ]; then
    echo "EXIT=$code  KILLED by signal $((code - 128)) in a step below — a build"
    echo "         process was reaped, not a gate refusing. Nothing is wrong with"
    echo "         the data. Re-run it."
  elif [ "$code" -ne 0 ]; then
    # NOT "a gate refused". That was this trap's second wording and it was a
    # confident label on something adjacent, which is the fault /method exists
    # to name. The tests above separate KILLED from NOT KILLED and nothing else:
    # a missing file, a step run from the wrong directory, a typo in a tool and
    # a gate saying no all land here. The Booyzen session had this trap mislabel
    # an exit 2 within an hour of adopting it, and said so.
    echo "EXIT=$code  NOT killed. A gate may have refused — or a tool may have"
    echo "         failed to run at all: a missing file, a wrong directory, a"
    echo "         typo. READ THE OUTPUT ABOVE before believing either."
  else
    echo "EXIT=0  every gate passed."
  fi
}
trap 'on_signal 15' TERM
trap 'on_signal 2'  INT
trap 'on_signal 1'  HUP
trap on_exit EXIT

echo "── data from the GEDCOM"
python3 tools/build_site_data.py
python3 tools/build_register.py          # also writes provenance.json
python3 tools/build_dossiers.py          # needs register.json
python3 tools/build_person_records.py     # needs register.json; the records build_dossiers drops
python3 tools/build_family_pages.py
python3 tools/build_dna.py

echo "── first pass"
# THE BRACKETS ARE LOAD-BEARING, and this is not a style choice. Under
# `set -e` a failing command inside an `&&` LIST DOES NOT ABORT THE SCRIPT:
#     cd site && sh -c "exit 143" && cd ..
#     echo "reached"          # this runs, in the wrong directory, and the
#                             # script exits 0
# A subshell propagates instead. The Booyzen session had the list form, had a
# build process reaped inside it, walked past the failure, and failed two steps
# later in python — so the trap faithfully named the wrong step, and a luckier
# run would have printed "build complete" over a build that never finished.
# VERIFIED HERE ON 21 SEPTEMBER by killing only the astro child of a live
# build: this script stopped at once, exited 143, and named the right branch.
# Checked, not assumed — the whole of today says the difference matters.
( cd site && npm run build --silent )

# IF THE FIRST PASS REFUSES WITH "searchindex ... point at pages that were not
# built", the build has not broken — it has lagged. site/public/searchindex.json
# is a committed artefact, validated during the FIRST pass and regenerated below
# during the second, so any change that REMOVES a page fails once before the
# index catches up. Folding ten duplicate atlas places on 21 September 2026 did
# exactly that. The recovery is to regenerate FROM THE DIST THIS FAILING RUN
# JUST BUILT, then run again:
#     python3 tools/build_search.py && ./build.sh
# ORDER MATTERS AND IT IS NOT OBVIOUS. Running build_search.py BEFORE the first
# build of a change does nothing — it reads dist/, which still holds the pages
# the change removes. The failing run is what produces the dist the regeneration
# needs. Learned the hard way twice on 21 September: pre-running it, then
# failing anyway, then running it again on the same command and passing.
echo "── indexes that read the built HTML"
python3 tools/build_mentions.py
python3 tools/audit.py
python3 tools/build_search.py

echo "── second pass"
# Brackets load-bearing — see the first pass. A list form walks past a
# reaped build and exits 0.
( cd site && npm run build --silent )

# A null must name the test that could have disproved it. /method has promised
# this for weeks and nothing enforced it, which is how 59 uncontrolled nulls
# accumulated. The 62 that predate the rule are grandfathered by name; this
# refuses the sixty-third. Control-tested by adding a bad row: exit 1.
echo "── control check"
python3 tools/check_controls.py

echo "── link check"
python3 tools/check_links.py

# The code, the data and every built page. Not a unit-test suite — there is no
# unit-test framework in this project and saying otherwise would be a claim this
# archive could not support. It compiles every tool, refuses a duplicate key in
# any data file (json.load keeps the last and drops the rest, which is how a map
# in the person page lost half of Hannah Saniger's links), and refuses a page
# showing a reader "undefined", "[object Object]" or literal **markdown** — the
# fault the shared kit records in three other archives in this estate, and which
# stood at 307 pairs across ten pages here until 20 September 2026.
echo "── self-test"
python3 tools/selftest.py

# Has the research reached the site? Three ways it does not: a data file no page
# imports, a signpost pointing at a page that is not built, and a signpost
# pointing at a page that says nothing about its subject. The third is a warning
# because prose may say a thing in its own words; the first two are failures.
# Run for the first time on 20 September 2026 it found no orphans and no broken
# signposts — and three rows pointing at a REDIRECT instead of the page, and a
# whole body of tax-record research (E 179, the hearth tax, the 1381 poll tax)
# whose signposts pointed at a page that never mentioned any of it.
# A refusal that nothing reads is a refusal the next session will overturn.
# namefold-deny.json sat as an ORPHAN until 21 September 2026 — two folds this
# archive had read and refused, with the reasons written out, and nothing on
# earth consulting them. This is the reader.
# The map's own claim about itself. A gazetteer that has not heard of a place
# answers with the smallest thing it did recognise and the confidence field
# records that the LOOKUP succeeded — so Berkeley spent weeks on the geocode
# for the word ENGLAND, with six people on it, stamped exact. atlas_pins.mark()
# re-stamps those `parent`; this refuses the build if one slips back.
# The living rule, as a value rather than as a filter copied into each page.
# On 22 September a page written in this repository rendered every member of
# families.json and published forty-four living people. It was not careless:
# the rule existed only as a line of presentation code, written out again in
# every page that needed it, and the new page inherited none of them. This
# refuses a page that goes back to deciding for itself.
echo "── living rule"
python3 tools/check_living_rule.py

echo "── atlas check"
python3 tools/check_atlas.py

echo "── namefold check"
python3 tools/check_namefold.py

echo "── published check"
python3 tools/check_published.py

# A reading this archive has WITHDRAWN, stated again as fact. The hazard is
# peculiar to an archive that publishes its own errors: the retracted wording is
# still in the building, on /corrections and in every dated log that recorded
# it, and gets copied into new prose by somebody who read it without the
# retraction around it. Quoted is not asserted — this archive's rule is that an
# error stays on the page where it was made, so a retired phrase inside
# guillemets is the rule working. Dated logs are exempt outright: they record
# what was believed on a day and must never be edited when the belief changes.
echo "── retired readings"
python3 tools/check_retired.py

# Reports, never gates. agree.py reads the archive against itself and prints
# every (person, event) pair carrying more than one year or more than one
# place. Most of what it prints is noise — repeated forenames, adjacent
# events, a birth and a late baptism — which is why it does not fail a build.
# It is here because the one real thing it found, a commission date printed
# two ways on six files, had sat unnoticed for weeks with nothing able to see
# it, and because the second thing it found was a place split three ways in
# the gazetteer. Read it; do not obey it.
echo "── agreement report (informational)"
python3 tools/agree.py --min 2 || true

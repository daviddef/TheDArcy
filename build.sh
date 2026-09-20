#!/usr/bin/env bash
# The whole pipeline, in the only order that works.
#
# Two passes are unavoidable: build_mentions.py and build_search.py both read
# the BUILT HTML, so the site has to exist before they can run, and their output
# has to exist before the final build can use it.
set -euo pipefail
cd "$(dirname "$0")"

echo "── data from the GEDCOM"
python3 tools/build_site_data.py
python3 tools/build_register.py          # also writes provenance.json
python3 tools/build_dossiers.py          # needs register.json
python3 tools/build_person_records.py     # needs register.json; the records build_dossiers drops
python3 tools/build_family_pages.py
python3 tools/build_dna.py

echo "── first pass"
( cd site && npm run build --silent )

echo "── indexes that read the built HTML"
python3 tools/build_mentions.py
python3 tools/audit.py
python3 tools/build_search.py

echo "── second pass"
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

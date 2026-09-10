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
python3 tools/build_family_pages.py
python3 tools/build_dna.py

echo "── first pass"
( cd site && npm run build --silent )

echo "── indexes that read the built HTML"
python3 tools/build_mentions.py
python3 tools/build_search.py

echo "── second pass"
( cd site && npm run build --silent )

echo "── link check"
python3 tools/check_links.py

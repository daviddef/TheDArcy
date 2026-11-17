#!/usr/bin/env python3
"""The places the corrections page may link, and the flag table it draws beside them (kit eb8ce42, 17 November 2026).

    python3 tools/build_correction_places.py     # writes site/src/data/correction-places.json and correction-place-flags.json

Rows are the places the Atlas map data (site/public/atlas-data.json, made by tools/atlas.py just before) gives a page /places/<slug>/; a place
without a page is never linked. The flags are the kit's placeflags.py over this archive's committed era snapshot (site/src/data/era-snapshot.json),
with the archive's two hand-made tables that the ribbon flags already use: site/src/data/flag-places.json (--alias: a name -> the place as the
era table prints it) and site/src/data/flag-countries.json (--countries: today's country where the pages settle it). Where the snapshot is silent
a place has its link and no flag; nothing is guessed here. Both outputs are generated at build (gitignored); `npm run build` runs this after
`npm run atlas` and before `astro build`, because the corrections page reads them.

LEFT OUT of the link list, each because in the corrections' prose the word is not the place:
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")

NOT_A_PLACE_HERE = {
    "Saniger": "the SURNAME in the prose (\"Elizabeth Saniger\", \"holds no English Saniger\"); the hamlet it came from is on its own page",
    "Hornby": "the family and the graft (\"the Hornby graft\", \"six were Hornby\"); Hornby Castle is the place and stays",
    "England": "a country: linking it six times would add noise, and every town beside it already carries the same flags",
    "Italy": "a country, as England",
}
__doc__ += "".join("  %-8s %s\n" % (k, v) for k, v in NOT_A_PLACE_HERE.items())

atlas = json.load(open(os.path.join(SITE, "public", "atlas-data.json"), encoding="utf-8"))
rows = [{"name": p["name"], "href": "/places/%s/" % p["slug"]}
        for p in atlas["places"] if p.get("slug") and p["name"] not in NOT_A_PLACE_HERE]
rows_path = os.path.join(DATA, "correction-places.json")
with open(rows_path, "w", encoding="utf-8") as fh:
    fh.write(json.dumps(rows, ensure_ascii=False, indent=1) + "\n")
out = os.path.join(DATA, "correction-place-flags.json")
r = subprocess.run([sys.executable, os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools", "placeflags.py"),
                    "--snapshot", os.path.join(DATA, "era-snapshot.json"), "--places", rows_path, "--out", out,
                    "--alias", os.path.join(DATA, "flag-places.json"), "--countries", os.path.join(DATA, "flag-countries.json")])
sys.exit(r.returncode)

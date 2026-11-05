# Roots & Routes (the tree page)

Ten views of every person this archive publishes who has died: hourglass, fan, whole-tree and close-family maps, Atlas map, movements, kinship, place lanes, eras,
lifespans, surnames, an Orphans tab, and the five animated views (Night sky, Ink ledger, Household, Generations, Where they lived). It is served at `/roots/`, and
bare at `/roots/view.html` for the frames of the kit's `PersonRootsViews` (not yet drawn on a person's page here: see below).

| File | What it is | Edit by hand? |
|---|---|---|
| `tree.json` | people, parent links, years, places | no, generated |
| `place_map.json` | each place string with coordinates, country and Record Atlas id | no, generated (see below) |
| `place-additions.json` | region-level place strings decided by hand, each with its reason | yes, with a reason |
| `atlas-data.json` | the Record Atlas slice: outlines, regimes, flags, events, collections | no, generated |
| `roots.html`, `roots.embed.html` | the page, whole and as a fragment for the site layout | no, generated |
| `tree.report.json` | counts, the four lives that are not one life, how many were left out as possibly living | read it |
| `people.export.json`, `people.ged`, `slugs.json` | intermediates, not committed | no |

## Rebuild

```bash
python3 tools/build-tree-page.py --accept-unique   # rebuild everything and run the page's own checks
python3 tools/build-tree-page.py --check           # exit 1 if the page is older than the data it was built from
```

Needs the Record Atlas checkout (`RECORD_ATLAS`, default `~/Projects/Family Projects/Record Atlas`), read only, and node (the people are read through
`site/src/lib/people.js`, so a slug, a name and a year are the ones the person pages print). The skill's scripts are vendored in `tools/tree-page/` (the
family-tree-page skill, template 1.7.0), so CI and other sessions do not depend on `~/.claude`. CI does not rebuild this page: it serves the committed output.

## What is and is not on the page

- **No living person.** Everyone `people.js` marks living is left out before the export (39 people). The converter adds its floor (no death recorded and born in the last
  110 years: 34), and this archive adds a stricter one: a person with no death recorded whose birth, recorded or estimated from a relative, falls after 1900 is not
  drawn (19, counted in `tree.report.json`, never listed).
- **Corrections apply.** Where `lib/corrections.js` overturns the tree's birth or death (11 years), the page draws the corrected year. A corrected place replaces the
  tree's only when it is a plain place name; a correction that says the place is unknown withdraws the tree's place (2).
- **Declared copies are drawn once.** The 8 people `data/same-person.json` declares to be a second entry of someone are not drawn; every relation to them goes to the primary.
- **Colour is the archive's own family** (`family` in people.js: the surname of its thirteen clusters in families.json; the seven largest have a colour, the rest share
  one), not a surname spelling. Which spellings are one name is the Record Atlas catalogue's to say; nothing here lists them.
- **Places are never guessed.** A place string gets a point from `data/era-ground.tsv` (the town decided for it) and `data/era-towns.tsv` (the town's point); the
  country is the Atlas's own `geo.country_of` on that point. A string the era table leaves without a town is taken from the Atlas only where the Atlas names it
  uniquely in the country the string names. Thirteen region-level strings (Queensland and its abbreviations, England, Scotland, New South Wales) are in
  `place-additions.json`, each at the Atlas's own marker for the region, which is not a town (said in `place_map.json`).
- **A person with no place of their own is drawn at a relative's birth place, and the card says so** (an asterisk, "place taken from a relative, not recorded").
  This archive's own findings are not applied to that fallback: George Pitt D'Arcy's birth place is "unknown" on his page, and he is drawn at his father's tree place.
- **Unknown sex stays unknown.** A person the tree records no sex for is drawn as `u` (Kinship says parent, child, spouse, sibling, uncle or aunt); the sex is never inferred from a name.
- **Estimated years are flagged**: "c. 1809" is a birth estimated from a parent, child or spouse; "1809–?" is a death not recorded. A tree date written
  "BEF", "ABT" or "BET" is drawn at its first year, as the converter reads it.
- **Two lives that cannot be one** (died before born, or over 110 years) are not drawn and are listed in `tree.report.json` under `conflicts`.
- **The page opens on Kenneth Lindsay D'Arcy** (`FOCUS_SLUG` in the builder), not on the best-connected person, who is a man of the Hornby descent this archive does not accept.
- **A person's page does not yet embed "Where they lived".** The kit draws that section only in story mode, and this archive's person pages are in chart mode;
  `site/public/roots-links.json` and `/roots/view.html` are ready for the day it does.

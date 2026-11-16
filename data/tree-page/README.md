# Roots & Routes (the tree page)

Ten views of every person this archive publishes who has died: hourglass, fan, whole-tree and close-family maps, Atlas map, movements, kinship, place lanes, eras,
lifespans, surnames, an Orphans tab, and the five animated views (Night sky, Ink ledger, Household, Generations, Where they lived). It is served at `/roots/`, and
bare at `/roots/view.html` for the frames of the kit's `PersonRootsViews` (drawn in the "Where they lived" section of a person's page, see below).

| File | What it is | Edit by hand? |
|---|---|---|
| `tree.json` | people, parent links, years, places; `bd`/`dd` full dates and `cx` corrections count; `undrawn` cards (see below) | no, generated |
| `place_map.json` | each place string with coordinates, country and Record Atlas id | no, generated (see below) |
| `place-additions.json` | region-level place strings decided by hand, each with its reason | yes, with a reason |
| `atlas-data.json` | the Record Atlas slice: outlines, regimes, flags, events, collections | no, generated |
| `roots.html`, `roots.embed.html` | the page, whole and as a fragment for the site layout | no, generated |
| `tree.report.json` | counts, the four lives that are not one life, how many were left out as possibly living | read it |
| `people.export.json`, `people.ged`, `slugs.json` | intermediates, not committed | no |

## Full dates (`bd`, `dd`), for the Atlas Tree Canvas (16 November 2026)

`tree.json` carries, per person and only where a day is known, `bd` (full birth date) and `dd` (full death date): `people.js`'s own `born` / `died` string, byte for byte,
in this archive's GEDCOM form **`4 APR 1460`** or **`17 AUG 1927`** (day not padded, upper-case English month abbreviation); the person page prints the same date as
"4 April 1460". Not reformatted. A year alone, a month and year, an approximate or ranged date (`ABT`, `BET`, `BEF`, `AFT`, `EST`, `TO`) and a year the archive's
`corrections.js` has overturned (exported as a bare year) get no field; `by` / `dy` and the `bye` / `dye` flags carry those. Only people the page draws, so never a living
person (everyone `people.js` marks living is left out before the export, and `drop_possibly_living` drops the rest). Made by `FULLDATE` and two lines in the per-person
loop of `tools/build-tree-page.py`. At the first build: 315 people have `bd`, 324 have `dd`.

## Corrections count (`cx`), for the Atlas Tree Canvas (16 November 2026)

`tree.json` carries, per person and only where there is one, `cx`: an integer of 1 or more, **how many corrections this archive records about that person**. It is the number
of lines the person page prints under "Corrected against the family tree", which is one per entry of `site/src/lib/corrections.js` for the slug (`tools/export_tree_people.mjs`
counts them; a living person is never exported, and the page prints none for one). A count only, never what a correction says; omitted when 0; derived at every build, never typed.
The canvas shows a pencil and the count and links to `/corrections/`. At the first build: 13 people have `cx`, 22 corrections in all.

## Everyone published is on the canvas: `undrawn` (17 November 2026)

David, 17 November 2026: "if it's in the archive it must be shown in the canvas". The ten views draw only the dead who can be placed and dated (726); the other 118
people the archive publishes are in `tree.json`'s `undrawn`, which the page's views ignore and the Atlas Tree Canvas draws as unplaced cards (726 + 118 = the 844 people with a page).
Made by `undrawn_cards()` in `tools/build-tree-page.py`; links follow the register's own and only to people who are in `tree.json`; the drawn people's own lists are untouched.

- **43 dead cards** (`unplaced: true`): undated, unplaced, the 4 conflicts, and 8 declared copies (a copy has no links: its relations go to its primary). Given, sur, `by` / `dy`
  where a year is recorded, parents / spouse / children, `page`, `cx`.
- **36 possibly-living cards**: no death recorded and a birth (recorded or estimated from kin) of 1900 or later, the same floor as `drop_possibly_living`.
- **39 living cards**: every living person the pages name.
- **The 75 living-style cards** are `living: true` with a name and family links ONLY: no sex (`u`), no date, no place, no page link, no `cx`. The names are the ones their pages already print.
  A living person whose name the pages withhold (no name, or the dash) is not in `tree.json`. The living rows come from `export_tree_people.mjs` into the intermediate `people.export.json`
  (never committed) and are never written to `tree.report.json`.
- **Placeholders**: 3 names in the archive read as stand-ins ("Unknown", "UNKNOWN Falco", "'Aelar' Unknown Georgian Lady"); all 3 are drawn people and none is undrawn. Nothing is flagged.

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
- **A person's page embeds "Where they lived"** (kit `PersonRootsViews`, in the `where` slot) for every person drawn on /roots/, listed in
  `site/public/roots-links.json`; the frame is `/roots/view.html`. The kit draws that section only in story mode, so these pages are story pages,
  with chapters cut from the archive's own notes (`site/src/pages/people/[slug].astro`). A person not drawn on /roots/ has no such section.

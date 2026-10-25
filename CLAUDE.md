# D'Arcy Family

## Record Atlas

The shared map lives at `../Record Atlas`. Research done here is only
useful to the next person if it gets there.

Invoke the `record-atlas-feedback` skill whenever you finish a search,
open a register, write to an archive, or find a source the atlas does
not list — as you do it, not in a sweep at the end. Record the
FamilySearch waypoint, not just the film number; the skill explains why.

## The linking standard (18 October 2026)

The twelve research narratives (`site/standard.json` lists them) are held to the kit's linking standard
(`site/node_modules/@daviddef/archive-kit/kit/docs/linking-standard.md`): L1 a name that resolves is linked (the autolink pass), L2 a
person read from a record has an entry, L3 a passage that cites a record links to it, L4 a held scan sits beside its passage, L5 the forms
no machine can resolve are counted. `tools/standard_pass.py` runs the kit's `checkstandard.py` last in `npm run build`; its ratchet is
`site/.standardfloor.json` (counts only). A count may only go down; an exemption (`data-cite-exempt`, `data-name-exempt`, each with its
reason) raises EX, which is ratcheted too, and a floor goes up only by a person's hand in a commit that says why.

- **Width.** A citation is a locator (an archive reference, a Trove id, a Queensland item) or a named record set (FamilySearch, FindMyPast,
  Discovery, the Internet Archive...). Event wording (baptised, buried, married) is NOT a citation here: that was measured (363 passages
  against 144) and left for the author. `record_links.hosts` is empty on purpose: only the archive's own entries and the links its `Rec`
  marks (`data-cite`) count, so a front-door link to a paid index cannot pass for a record.
- **Records table.** `site/src/data/records.json` is made by `tools/build_records.py` from `register.json` (deep addresses only) and the
  references the pages print; `tools/check_records.py` (first in the build, and in CI) holds it to the data and every `<Rec>` and
  `[words](rec:ID)` to the table and to the words it wraps. A Trove locator links to its permalink; a National Archives reference links to
  Discovery's search FOR THAT REFERENCE (the address carries the reference; it is labelled a catalogue search, not the record's page).
  Gloucestershire and Hertfordshire Archives, the Berkeley Castle Muniments, local registers, the Queensland BDM index and NAA items have
  no public address in the data: their passages stay plain and counted, or carry a reasoned exemption. Never invent an address.
- **Writing a link.** In an `.astro` page: `<Rec id="tna-wo-12-8483">WO 12/8483</Rec>` (the same words become the link, nothing reworded).
  In a data file rendered through `src/lib/md.js`: `[WO 12/8483](rec:tna-wo-12-8483)`. A table cell that may or may not have a record uses
  `hasRecord(ref)` from `src/lib/records.js`.
- **Names read from records.** A person a narrative names from a record gets a `rec(...)` line in `tools/build_register.py` (with the page
  they are read on), which makes the `/who/` page and the index entry. Only people the living rule shows dead (the record is dated 1900 or
  earlier); a name two men could bear on one page, a name another page already bears, and the twentieth-century people on /great-war/ are
  held out. `site/src/data/names-aliases.json` lists the spellings the data itself STATES for a page's person; the generator checks each.
- **Scans.** L4 is 0 and stays 0: the 1902 inquest scan is link-only (`.gitignore`: images of a sensitive original), and the one Trove crop
  on /great-war/ is shown beside its passage. FamilySearch, NAA, TNA, FindMyPast images are link-only until David rules.
- **CI** builds from committed data only (no GEDCOM, no feed): the names index comes from the built pages and `names-aliases.json`, the
  living list from the noindex pages, the records table is checked against `register.json`, and the kit's self-test of the gate runs first.

## "At the time" notes (18 October 2026)

Beside a dated place on a **non-living** person's page (the Born and Died rows and each marriage whose spouse is named) the kit draws a muted line,
"At the time: Britain and its colonies per the Record Atlas": who held that ground in that year, from the Atlas's region eras. Text only, context about
the ground and never a claim about the family; where the data does not support a note there is nothing. The rules are
`site/node_modules/@daviddef/archive-kit/kit/docs/era-notes.md`.

- **The place table is the decision.** `data/era-ground.tsv` has one row per place string as the pages print it (born, died and marriage places of the
  non-living), with an Atlas region or `-` and the reason; `data/era-towns.tsv` gives the point of each town so the kit can refuse a place within 15 km of
  a ring edge. A region is given only where it CLEARLY covers the place (England and Wales, Queensland, Scotland, Ireland, Campania and a few continental
  regions). New South Wales, Baden, Wurttemberg and the rest have no region and are `-`. A new place string fails `npm run check:era-ground` until it has a row.
- **The snapshot is committed** (`site/src/data/era-snapshot.json`, version 4, with the contract's version and sha256 in it) and refreshed on purpose:
  `python3 tools/build_era.py --snapshot <Record Atlas>/site/public/context.json [--report drops.json]` (from a copy of the contract; never edit the Atlas).
  A build never reads the Atlas. Policy is recorded in the snapshot: `--unassessed allow` (today it lets nothing through: an unassessed era also has null margins
  and is refused as unknowable), `--approx margin`, `--contested scope`, N = 5.
- **The date.** `site/src/lib/eraYear.js` turns the printed date into a plain year (`27 OCT 1406`, `MAR 1600` and `June 24 1497` count; `AFT`, `BET`, `ABT`, `TO`,
  `1621/22` and the archive's own prose do not) and, before 1752 (a British year began in March), draws a note only where the year either side lies in the same era.
- **Gates**, last in `npm run build`: `check:era-ground` (first), `check:era` (the kit's gate on the built pages: every note names a contract era, the year lies
  inside it, no note on a living or noindex page; the living list is written outside the repository, `tools/build_era.py --living-path`), `check:era-expect`
  (`tools/check_era_expect.py`: re-derives from the printed dates and places the notes each page should carry, and fails a missing, extra or differing one) and the
  kit's self-test. `tools/autolink_strip.py` takes the notes and their `<style>` off whole, so `mentions.json`, `whoindex.json` and the search text do not change because of them.
- **The 215 `/who/` pages** print one free-text record sentence and its source, with no date or place field: no notes there.

## The living rule and the printed-year gate (kit 341af33, 25 October 2026)

A person born in the last eighty years (1946 or later in 2026: the kit's single derived `cutoff_year()`) with no death RECORD is living, whatever a
public-source citation or a bare death flag says. `tools/gedcom.py` therefore passes the two apart: `recorded_dead()` is a death or burial event with a
date, place, cause or note; a bare `DEAT Y` is a FLAG (`undated_dead()`), which for a person born inside the window frees nobody and for anyone else
means dead. 26 people in the tree are flag-only and born 1946 or later; none was published. `tools/check_living.py` restates it independently.

`npm run check:living` also runs the kit's `--years` gate (`standard.json` `living_years`): no year on or after the line may print for a person with no
death. Exceptions are in `site/living-year-allow.json`, each with its reason, and a stale one fails (`--strict-allow`). A withheld sentence is
`NOTE_WITHHOLDS` in `tools/gedcom.py` (the eulogy speaker's own birth year); never record a death that no source gives, mask the person instead.

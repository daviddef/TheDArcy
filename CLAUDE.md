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

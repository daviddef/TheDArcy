# The D'Arcy Archive

An evidence-first family archive for the **D'Arcy** family of **Brisbane, Queensland** — and of
Parramatta, Chatham, Portsmouth, Limerick, Monaghan, Ayrshire, Somerset and Bristol.

> *D'Arcy* was coined twice over, and the two have nothing to do with each other: in Normandy as
> *d'Arcy*, "of Arcy", the name of a place; and in Ireland as *Ó Dorchaidhe*, from *dorcha*, "dark",
> the name of a complexion. **There is no single founding D'Arcy family.** The work of this archive is
> to establish which D'Arcys are actually connected, and to say plainly where the evidence stops.

## What is here

- **Six documented generations in Australia**, from **Major George Pitt D'Arcy of the 39th
  (Dorsetshire) Regiment of Foot**, who came out as a convict guard in 1826, down to Brisbane today.
- **The arrival, proved from two independent directions.** His children were born at **Chatham in
  1825** and at **Parramatta in 1827 and 1829**. In July 1825 the 39th marched to Chatham to embark
  for New South Wales as guards over convicts, and from 1826 it held a detachment at Parramatta. The
  regimental record was not written about this family and gains nothing from agreeing with it.
- **A pedigree that contradicts itself, set out in full.** Above Major-General Robert D'Arcy C.B.
  (1751–1827), Commander of the Royal Engineers at Chatham, the tree climbs to the **Earls of
  Holderness** and to **Hornby Castle** in the North Riding. Its own note says Robert was
  "*thought to be the illegitim[ate]*" son of the **4th** Earl — and then the structure descends him
  from the **3rd**, through a man given two birth years sixty-nine years apart. At most one of these
  can be right; neither carries a document.
- **A surveyor who helped map Melbourne.** **Frederick Robert D'Arcy** (1811–1875), half-brother of
  the direct ancestor, was withdrawn from Sandhurst, sailed on the *Albion* in 1828, and in 1836 was
  one of three surveyors sent by Governor Bourke to chart Port Phillip Bay and the Yarra. He died at
  Spring Hill and lies at Toowong.
- **A four-thousand-word eulogy**, delivered in three parts by the three children of **Kenneth
  Lindsay D'Arcy** in March 2010 — the African Grey parrot that called "Come in", the mango tree, the
  cigarettes at nine, Cyclone Althea, and twenty melanomas. Reproduced whole.
- **Pozières, 20 August 1916.** **Arthur Hartley Sneyd**, brother of the woman who married into this
  line five months earlier, killed in action aged twenty-two.
- **The families they married**: Sneyd, Atkinson, Murdoch, Atwell, Blum, Keeling, Creech, Matson,
  Wakefield, Wright, Rossiter, Watt — an organist from Limerick Cathedral, a merchant seaman who
  deserted his ship, an engineer from St Quivox, and three generations of Murdoch men who died of
  their hearts.
- **The name**: *Darcy*, 17,796 bearers worldwide; Ireland the homeland by density at 1:1,519;
  Australia a serious presence at 1:9,319.

## Method

| | |
|---|---|
| **Documented** | A named source with a reference, and where possible the scan. |
| **Inferred** | A reasoned conclusion from documented facts, with the reasoning written out so it can be overturned. |
| **Superseded** | Asserted in the family record, and now displaced by a document that says otherwise. |
| **Disputed** | Asserted in the family record but unsupported, or contradicted, by what can be seen. |
| **Family lore** | Told, remembered, not corroborated. Kept because it is precious; labelled because pretending otherwise is how family myths become family history. |

**A living person (80 or younger, with no death recorded) is named with their relationships and
their town and country, and nothing more** — a name, a relationship, a town and a country; no date,
record, source, note, photograph or structured data, and their page is `noindex`. The rule is
applied once, in `living_json()` in `tools/build_site_data.py`, at the boundary between the research
data and the published site. Who is living is not decided in this repository: it is the shared kit's
one definition (`kit/tools/living_rule.py` and `kit/data/public-sources.json`), applied to facts
`tools/gedcom.py` prepares. A person is living if born 80 years ago or less (by year) with no death
or burial recorded; a recorded death or burial, dated or not, means dead; a citation from a public
record source (FamilySearch, a MyHeritage record collection, Findmypast and the others on the
shared list) means not living; a private family-tree entry does not count; and a person with no
birth year cannot be shown to be 80 or younger, so is not living. The tree is not inferred from:
the old upper bound on birth years through the family graph, with its hundred-year horizon, is gone.

**Every person the archive names has a page.** The numbered ancestors and the thirteen families have
pages, and so do the parents, brothers and sisters and spouses they are shown with
(`site/src/data/relatives.json`); a relative's own relatives are listed on their page only where
they already have one. The tree's other people are never published.

Two groups are left out altogether, with no page and no name as anybody's relative: the person whose
DNA result `/dna/` describes (held by id, in `decisions.json`) and every undated person with a
living parent who might be a child (not recorded dead, no public source, no birth year, a living
parent; `held_out()` in `tools/gedcom.py`, through the kit). A child with a known birth year is
not held out: they follow the standard like anyone living. The counts are in `living.json`. A removal
request is honoured within days, without argument and without requiring a reason.

The raw GEDCOM is **not committed** — it contains every living person in full. `sources/*.ged` is
gitignored; regenerate it with a fresh MyHeritage export and re-run the tools.

**An online family tree is a witness, not a source.** The spine here is a MyHeritage tree of 15,643
people. Where it carries a citation the citation is shown and marked as *attached in the tree*; where
this archive has gone to the original, the page says so.

## Running it

```bash
cd site
npm install
npm run dev      # http://localhost:4323/TheDArcy
npm run build    # static output in site/dist
```

Deploys to GitHub Pages on every push to `main`.

## Layout

```
sources/                         myheritage-tree4-2026-09-09.ged (15,643 people, 4,777 families)
sources/biographies/             kenneth-lindsay-darcy-eulogy-2010.md
data/                            ancestors.tsv, darcy-spine.tsv, surname-*.tsv
notes/                           baseline-surname.md
tools/                           gedcom.py, ancestry.py, build_site_data.py
site/src/data/                   line, ancestors, families, places, eulogy
site/src/pages/                  the archive itself
```

## Sources

Queensland and New South Wales civil registration · St James's Church, Sydney · Australian
newspapers (Trove) · National Archives of Australia, First World War service records · Australian
War Memorial, Roll of Honour and unit diaries · Brisbane City Council cemetery registers (Toowong,
Dutton Park, South Brisbane, Nundah, Lutwyche, Mt Thompson) · Roots Ireland, Limerick diocesan
registers · Scotland's People · Forebears · MyHeritage, FamilySearch and FindMyPast.

The line reaches 1826 in Australia with a regiment behind it, and 1751 in England with a General.
Above the General it is tradition. Closing that gap — or closing it off — is the work.

# Menu PR D (D'Arcy): a family page is linked from the menu OR the /families/ index

13 November 2026, on origin/main at a5f714c (after the What's-new wiring, kit 0521bf1). Asked for by the estate session on David's word in chat (13 Nov): the
one rule all eight archives share is "a family page must be linked from the menu OR from the /families/ index, which the menu links". Menu and gate only:
the one page change is the four links added to `/families/` that the order of work required (step 2 below).

## What changed (1: the gate; 2: the index; 3: the menu)

1. **`tools/check_family_lines.py`**: the `index` and `nav` checks (each line linked twice: the index card AND the menu) became one `reach` check: each of the
   twelve lines is linked from the menu (the topnav) or from the `/families/` index's own body (card or "all N published" link), and the menu links
   `/families/` itself (without that, a line reached only through the index would be reached through nothing). Planted faults in `--controls`: a line linked from
   neither (caught), the menu no longer linking `/families/` (caught); positive controls: a line linked from the index card only passes, a line linked from the
   menu only passes. All 26 controls came out as expected (`every planted fault was caught`).
2. **`/families/`** (`site/src/pages/families.astro`): a new block, "Pages of their own", links The Sneyds, Sergeant Sneyd, The Murdochs and The Women, which were
   reached only from the menu (docs/menu-a-reach.md, point 2). Atkinson is already on the index. Nothing is removed or reworded (declared in docs/menu-text-changes.json).
3. **The Families dropdown** (`site/src/lib/site-menu.js`): the index (the heading), the own line (Sneyd), the other surname pages A to Z (Atkinson, Murdoch),
   then the pages that are not a surname in their existing order (The Women, Sergeant Sneyd). The twelve lineage pages (Cotton, Sutton, von der Pfalz, Howard,
   von Degenfeld, Schomberg, Kent, Stuart, Jones, Noel, Ward, Blackbourne) left it; the sort and the bare-surname labels are the family-menu rule's, unchanged.
   (The estate's note said eleven lineage pages; `family-lines.json` has twelve, all of them removed.)

## Counts (built home page; before = a5f714c, after = this branch)

| | before | after |
|---|---:|---:|
| links in the header menu (topnav), incl. the pulse and duplicates | 98 | 86 |
| menu entries, all menus (the PR A / PR B count) | 92 | 80 |
| entries outside Research | 72 | 60 |
| The families group, entries under its heading | 17 | 5 |

## Nothing lost

- `tools/menu-moves.py` (docs/menu-d-moves.md): the twelve lineage pages are the only addresses that left the menu, each declared in `DROPPED` with its reason; **0**
  were in the menu and are in none now without a stated reason.
- Reach: on the built `/families/`, **12 of 12** lineage pages are linked from the index body (outside the menu); the four added pages and Atkinson are on the index and still in the menu.
  The menu still links `/families/`.
- Kit `compare` (docs/menu-d-compare.txt): **NOTHING LOST** over the 92 pages in scope (docs/menu-scope.json, unchanged).
- `sitediff`: 1,301 pages before and after, none gone, none new; the only page whose main text differs is `/families/` (+6 words in one new block), declared.

## Build

Clean clones of a5f714c (before) and of ac95883 (this branch before the proof files), isolated parent, `CI=true GITHUB_ACTIONS=true`: `npm ci` then `npm run build`, both exit 0;
`check_family_lines` passes inside the build ("each is linked from the menu or the /families/ index ... and is in the sitemap"). The head of the PR adds only these docs and
`DROPPED` in `tools/menu-moves.py` on top of ac95883.

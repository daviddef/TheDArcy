# Menu regroup, PR A (D'Arcy): counts, reach proof, and what was kept

12 November 2026. MENU ONLY: no page content edited, no page merged, no redirect, no address deleted, no page added, no index page edited.
The files changed are `site/src/lib/site-menu.js` (new: the whole menu in one list), `site/src/layouts/Base.astro` (reads it; a group heading
without an address is a plain label), `site/src/lib/research-menu.js` (one entry added: The DNA, under Deep dives) and the proof files in
`docs/` and `tools/` (the kit's inventory wrapper and the menu-moves checker, copied from Defranceski's PR #6).

## Counts (header menu of the built home page, before = origin/main at fe1aabd, after = this branch)

| | before | after |
|---|---:|---:|
| menus | 9 | 6 |
| entries in all menus | 93 | 92 |
| entries outside Research | 74 | 72 |
| Start | 13 | 5 |
| Our line | 6 | 6 |
| People (was People & places, 8) | 8 | 11 |
| Places & families | – | 26 |
| The studies (was The D'Arcys 10, The Sanigers 10, Bristol and the Potteries 4) | 24 over 3 menus | 24 in 1 menu, 3 sub-heads |
| The families (18) and Australia (5) | 23 over 2 menus | inside Places & families |
| Research | 19 | 20 (The DNA added under Deep dives) |

The saving the review hoped for (74 to about 42 entries) is NOT reached, for two reasons stated below: the twelve lineage pages stay in the
menu because a standing gate requires them there, and Atkinson was asked to stay. The nine menus became six, and Start fell from 13 to 5.

## Nothing lost

- Every address that was in a menu is in a menu now: `tools/menu-moves.py` (docs/menu-a-moves.md): "0 address(es) were in the menu and are
  in none now". Only `/whats-new/` appears in fewer places (it left Start; it is the "What's new" group of Research and the pulse button).
- The kit's inventory `compare` (docs/menu-a-compare.txt): **NOTHING LOST** over the 92 pages in scope (docs/menu-scope.json): every old URL
  answers, every text block that stood on one of them stands somewhere on the new site. `/people/` and `/who/` are outside that scope because
  the kit tool does not read them as destinations; their main text is byte-identical before and after (sha1 of `<main>`, `/people/` 6bdff37e9423,
  `/who/` 6f5f9a71773f).
- `sitediff` (every page of the site, old build against new): 1,301 pages before, 1,301 after, none gone, none new; the only pages whose main text
  differs are `/research/`, `/research/sources-and-method/` and `/sources/`, each by one added line (The DNA in the Deep dives list), declared in
  docs/menu-text-changes.json. No block is reworded.

## Reach proof for what was trimmed

Nothing was trimmed out of every menu. Each address kept a place in a menu, so no address depends on an index page for its reach. The one move
that touches a page that also sits in Research: `/whats-new/` left Start and stays in Research (group "What's new") and in the pulse button.

## Kept in the menu on purpose, and why

1. **The twelve lineage pages** (Cotton, Sutton, von der Pfalz, Howard, von Degenfeld, Schomberg, Kent, Stuart, Jones, Noel, Ward, Blackbourne).
   The `/families/` index DOES link all twelve (checked on the built page: 12 of 12, plus Atkinson), so they could leave the menu on reach
   alone. But `tools/check_family_lines.py` holds that "the navigation on /families/ links to every line" and that each is linked twice (the menu
   and the index card); a first build that left them out failed it (`the navigation on /families/ does not link /families/cotton/`, 12 times).
   Trimming them means changing that gate, which a menu-only PR does not do. `LINEAGE` in `site-menu.js` is the one switch.
2. **Needs index fix: The Women, Sneyd, Sergeant Sneyd, Murdoch.** The built `/families/` index does not link `/the-women/`, `/sneyd/`,
   `/sergeant-sneyd/` or `/murdoch/` (checked: all four absent; `/atkinson/` is present). They stay in the menu until the index links them.
   (The three Sneyd pages are not touched: that is PR B.)
3. **Atkinson** stays, as asked, although the index links it.
4. **What the Indexes Hold** (`/coverage/`) stays beside Sources in Research; it is a measurement, not a deep dive, and it carries an Atlas note.
   The five deep dives (The Papers, The Inquest 1902, The Search for Arthur, Behind the Paywall, Reading the Archive Against Itself) were already
   under Deep dives from the earlier Research PR; The DNA joins them.

## Decisions I made that the peer's note left open

- **The Name** stays in Our line (where it was).
- **The Atlas** went to Places & families, with The Lines and Places (the review's placement).
- **No page was renamed**: every label is the one it had, except the group heads.
- `check:nav` is still advisory (it prints "departs from the canon" for the local Research pages, as on main).

# Menu, PR B (D'Arcy): the families in the menu, own line first then A to Z

12 November 2026. MENU ONLY: no page edited, no `/families/` index edited, no address added or removed, no redirect. One source file changed:
`site/src/lib/site-menu.js`. Applies `Research Menu Rollout/family-menu-rule.md` (David, 12 Nov 2026: "items 1 and 2, own line first then A to Z")
to Places & families > The families, on top of PR A (merged as 5971c95).

## What changed

Before (18 entries): The Families, The Women, Sneyd, Sergeant Sneyd, Murdoch, Atkinson, Cotton, Sutton, von der Pfalz, Howard, von Degenfeld,
Schomberg, Kent, Stuart, Jones, Noel, Ward, Blackbourne (the last twelve in the order `data/family-lines.json` ranks them, which is no rule).

After (18 entries; the index is the group heading):
1. **The families** (the sub-head, now the link to `/families/`: the old first item "The Families" repeated the heading and is gone as a separate
   line, not as an address)
2. **Sneyd**: the own line (David chose Sneyd as the own line; Sergeant Sneyd stays with the pages that are not a surname)
3. the other surnames A to Z, accents folded and a leading particle ignored: Atkinson, Blackbourne, Cotton, von Degenfeld (D), Howard, Jones,
   Kent, Murdoch, Noel, von der Pfalz (P), Schomberg, Stuart, Sutton, Ward
4. the pages that are not a surname, in their existing order: The Women, Sergeant Sneyd

The same duplicate in **Places**: the sub-head "Places" over a link "Places" became the sub-head as the link to `/places/`; The Atlas and The Lines
follow. "Australia" has no link under it and is unchanged. Labels are already bare surnames (the lineage entries use `surname` from the data file, and
Sneyd, Murdoch and Atkinson were bare), so no label was reworded. The sort is code (`sortKey` in site-menu.js), not a typed order.

## Counts (header menu of the built home page; before = 12b4fde)

| | before | after |
|---|---:|---:|
| menus | 6 | 6 |
| entries, all menus | 92 | 92 |
| Places & families (links, counting a heading link) | 26 | 26 |
| The families group | 18 | 18 (heading link + 17) |
| Places group | 3 | 3 (heading link + 2) |

## Nothing lost (clean clones of 12b4fde and of the PR head, CI=true)

- `tools/menu-moves.py` (docs/menu-b-moves.md): **0** addresses were in the menu and are in none now. Two addresses changed place in the menu:
  `/families/` and `/places/` went from first item to the heading link of their own group.
- Kit `compare` (docs/menu-b-compare.txt): **NOTHING LOST** over the 92 pages in scope (docs/menu-scope.json, unchanged; `/people/` and `/who/` are
  outside it as in PR A, and neither page is touched).
- `sitediff`: 1,301 pages before and after, none gone, none new, every changed page declared (none changed).
- `check_family_lines` passes inside `npm run build`: the navigation on `/families/` still links the index and each of the twelve lineage pages.
  No gate was changed.

## Build

Clean clone of the PR head, an isolated parent directory with no siblings, `CI=true GITHUB_ACTIONS=true`: `npm ci`, then `npm run build` exit 0.
`check:standard` L3 80, L5 216, EX 216 unchanged; `check:nav` advisory "departs from the canon" as on main; `check:prose` not run in CI as on main.

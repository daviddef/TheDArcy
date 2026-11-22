# Menu clean-up (D'Arcy, 23 November 2026): nothing lost from reach

David's word in chat (23 Nov 2026, after the estate audit): "roots and routes, remove it", "github links, no", "menus, do all". This file is the menu part (the
brief's Task C), with the proof the brief asks for. Built from origin/main at 621c2d3 (before) and the branch `estate-cleanup-2026-11-23` (after), both with
`CI=true` (no GEDCOM), the kit's `menu_inventory.py` run through `tools/menu-inventory-kit.py`.

## What the menu is now

| Group | Before | After |
|---|---:|---:|
| Start | 5 | 5 |
| Our line | 6 | 5 (The Name moved to its own group) |
| People | 11 | 7 (Lists: 6; Drawn: one link to `/drawn/`) |
| Places & families | 14 | 13 (All the families + Sneyd, Atkinson, Murdoch, The Women; Places, The Atlas, The Lines; five Australia pages) |
| The studies | 24 | gone as a menu: one entry "The studies" in Research |
| The name | (none) | 3 (restored: The Name, Every Spelling of One Name, The Name in Its Own Century) |
| Research | 20 | 15 (three group headings, the eight core pages, Gallery, Documents, What the Indexes Hold, The studies) |
| **All menus** | **80** | **48** |

Counts are the links in the built home page's `<nav class="topnav">`, group headings that are links included (as docs/menu-d-reach.md counted).

## What moved, and where each address is reached from

`docs/menu-e-moves.md` (made by `tools/menu-moves.py`, which fails if an address left the menu without a reason in its `DROPPED` table) lists every entry before and after.
**0 addresses were in the menu and are in none now without a stated reason.**

- **People / Drawn**: `/tree/`, `/trees/`, `/timeline/`, `/bloodline/` left the menu; the new hub **`/drawn/`** lists them with `/direct-line/` (The Spine, still in Our line) and
  `/lines/` (The Lines, still in Places), each with its blurb from the book. No drawn page was renamed, moved or deleted. Built-page check: 4 of 4 linked from `/drawn/`.
- **The studies**: the 22 studies that left the menu, and the two (`/spellings/`, `/swonhungre/`) that moved to The name, are all on the new hub **`/studies/`** (3 groups with the
  menu's own labels, then the 6 deep dives), read from `lib/studies-menu.js` and `lib/research-menu.js`. Built-page check: 30 of 30 linked from `/studies/`.
- **Deep dives** (`/papers/`, `/inquest-1902/`, `/finding-arthur/`, `/behind-the-paywall/`, `/crossread/`, `/dna/`): left the Research menu; on `/studies/`, on `/sources/` and on `/research/`, as before.
- **Sergeant Sneyd** left the families list (the brief's cap is four named families); it is on the `/families/` index under "Pages of their own", and the menu links that index as "All the families".
- **The Name** moved from Our line to the restored The name group.
- **Roots & Routes** (`/roots/`): retired (see the PR); the address redirects to `/tree/`.

## The kit's check

`docs/menu-e-compare.txt` (the kit's `compare` against the old build, 92 in-scope pages) reads 86 problems, and all 86 are intended and are listed here, not hidden:
71 text blocks of the retired `/roots/` viewer (the address answers: `redirect->/tree/`); 14 on `/contents/` (the book's chapter numbers: VII.6 is now Drawn, and the new
`/studies/` chapter VIII.4 renumbers VIII.4 to VIII.16 as VIII.5 to VIII.17; verified by comparing the two lists: same titles and blurbs); 1 on `/about/` (the GitHub
repository link). Every old URL still answers. `sitediff` (docs/menu-e-sitediff.txt): 1,301 pages before, 1,303 after, none gone, new: `/drawn/`, `/studies/`; the only pages whose
main text differs are `/roots/`, `/contents/`, `/part/how-we-know/`, `/part/everyone/` and `/about/`, each declared in docs/menu-text-changes.json.

## Not done, on purpose

- No `/namesakes/` (forenames) page exists in this archive, so The name has no "The forenames" entry; it would need a decision (a page about the forenames), not an assumption.
- The search index (`site/public/searchindex.json`) got the two hub rows and lost the `/roots/` row by hand. A full regeneration (`build_search.py`, `build_mentions.py`) from a CI-only
  build reshuffles 235 search rows, 63 names-index rows and 282 `mentions.json` lines and cannot apply the private living-names feed, so it was not committed; the search text of
  other pages still carries the old menu's words ("Roots & Routes") until the next full local build.

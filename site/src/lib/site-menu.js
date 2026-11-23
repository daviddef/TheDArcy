/* THE WHOLE MENU, one list. 12 November 2026 (the menu regroup, PR A, after Defranceski's): the nine groups other than Research became
   five, and Research (lib/research-menu.js, unchanged in shape) is the sixth. The header menu, the drawer and anything else that needs
   "where is this page in the menu" read THIS list (layouts/Base.astro does), so there is one place to change a label or move a page.
   No page was renamed and no address changed: every href below is a page that was already built and already in a menu; only its group
   moved. Nothing was dropped.
     a menu is  [label, items]
     items     either a flat list of [href, label]            (a short menu: one column)
               or a list of groups { head, href?, items }   (a group is a column; `href` makes its heading a link; an item is [href, label])
   Where an address went:
     /whats-new/       left Start (it is the "What's new" group of Research and the pulse button)
     /dna/             left Start (a deep dive under Sources, in Research)
     /trees/ /tree/ /timeline/   left Start (People, under "Drawn"; /bloodline/ left People & places for the same place)
     /roots/           (Roots & Routes) was retired on 23 Nov 2026: it left the menu and the address redirects to /tree/ (astro.config.mjs)
     /lines/ /atlas/   left Start (Places & families)
     /places/          moved from People & places (Places & families)
     /emigrations/ /general-hewitt/ /australia/ /brisbane/ /great-war/   the "Australia" menu became a group of Places & families
     the twenty-four pages of "The D'Arcys", "The Sanigers" and "Bristol and the Potteries" became the three groups of one new menu,
     "The studies", each moved as it was.
   23 November 2026 (the estate clean-up, David: "menus, do all"): the menu took the shape every archive converges on.
     "The studies" is no longer a menu of 24 links: it is ONE entry in Research (lib/research-menu.js) that opens the hub /studies/, which
       lists every study and deep dive with its blurb (lib/studies-menu.js, the same list). No study moved.
     "The name" is restored as its own group, as in every other archive: /name/ left Our line for it, with the two pages about the name itself.
     People: Lists, then ONE link "Drawn" to the hub /drawn/ (lib/drawn-pages.js), which lists the drawn pages with a line on what each shows.
     The families: one hub link "All the families" and four named (own line first, then A to Z); Sergeant Sneyd left the menu and is on
       the /families/ index ("Pages of their own").
   The twelve lineage pages (/families/<slug>/, from data/family-lines.json) LEFT the menu on 13 November 2026 (PR D): they are reached from
   the /families/ index, which the menu links (its card and its "all N published" link, on the built page), and tools/check_family_lines.py
   now holds that a family page is linked from the menu OR from that index, the one rule the eight archives share. The Families menu is the
   index, the own line, and the larger pages: Sneyd, Atkinson, Murdoch, The Women, Sergeant Sneyd (the four that were menu-only are now
   also on the index, in "Pages of their own"). */
import { navGroups } from "./research-menu.js";

/* The surname pages after the own line, A to Z: accents folded, a leading particle or article ignored (von der Pfalz under P, von Degenfeld
   under D), case-insensitive. Atkinson and Murdoch are the two surnames with pages of their own in the menu; the twelve lineage pages are
   reached through the /families/ index (see the note at the top). */
const sortKey = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/^(the|von der|von|van der|van|de)\s+/, "");
const SURNAMES = [
  ["/atkinson/", "Atkinson"], ["/murdoch/", "Murdoch"],
].sort((a, b) => sortKey(a[1]).localeCompare(sortKey(b[1])));

export const MENU = [
  ["Start", [
    ["/", "Home"], ["/story/", "The story"], ["/about/", "About"], ["/how-far-back/", "How Far Back"],
    ["/the-other-archives/", "The Other Archives"],
  ]],
  ["Our line", [
    ["/direct-line/", "The Spine"], ["/saniger-line/", "Six Generations at Berkeley"], ["/jean-ward/", "South Leith"],
    ["/new-generations/", "Not in the Tree"], ["/hornby/", "The Hornby Claim"],
  ]],
  ["People", [
    { head: "Lists", items: [
      ["/people/", "The People"], ["/who/", "Every Name"], ["/register/", "The Register"], ["/households/", "Households"],
      ["/marriages/", "The Marriages"], ["/graves/", "Graves"],
    ] },
    /* the drawn pages (the tree, the trees, blood relatives, the timeline...) are listed on the hub, with what each shows */
    { head: "Drawn", href: "/drawn/", items: [] },
  ]],
  ["Places & families", [
    /* The group heading is the link to the index (/families/, /places/): it used to repeat as the first item under a heading of the same
       words ("The families" over "The Families", "Places" over "Places"). Order of "The families" (family-menu-rule.md, David, 12 Nov
       2026): the index (the heading), the own line (Sneyd), the other surnames A to Z, then the pages that are not a surname. */
    /* 23 Nov 2026: the estate shape (Booyzen's, 12 Nov): "All the families" (the /families/ index) and at most four named, the own line first
       (Sneyd), then A to Z (Atkinson, Murdoch), then The Women. Sergeant Sneyd is reached from the /families/ index, "Pages of their own". */
    { head: "The families", items: [
      ["/families/", "All the families"],
      ["/sneyd/", "Sneyd"],
      ...SURNAMES,
      ["/the-women/", "The Women"],
    ] },
    { head: "Places", href: "/places/", items: [
      ["/atlas/", "The Atlas"], ["/lines/", "The Lines"],
    ] },
    { head: "Australia", items: [
      ["/emigrations/", "How They Got Here"], ["/general-hewitt/", "The General Hewitt, 1854"], ["/australia/", "Arrival, 1826"],
      ["/brisbane/", "Brisbane"], ["/great-war/", "The Great War"],
    ] },
  ]],
  /* THE NAME IS ITS OWN GROUP again, as in every other archive (23 Nov 2026). The Name, and the two studies that are about the name itself
     (the measured table of its spellings; the printed pedigree of the name in its own century); both stay in /studies/ too. The forenames
     (/your-name/, the Say-your-name page, read from the Record Atlas's given-name catalogue) joined it on 23 Nov 2026. */
  ["The name", [
    ["/name/", "The Name"], ["/your-name/", "The forenames"], ["/spellings/", "Every Spelling of One Name"], ["/swonhungre/", "The Name in Its Own Century"],
  ]],
  ["Research", navGroups],
];

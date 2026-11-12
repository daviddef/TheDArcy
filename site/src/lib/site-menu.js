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
     /trees/ /tree/ /roots/ /timeline/   left Start (People, under "Drawn"; /bloodline/ left People & places for the same place)
     /lines/ /atlas/   left Start (Places & families)
     /places/          moved from People & places (Places & families)
     /emigrations/ /general-hewitt/ /australia/ /brisbane/ /great-war/   the "Australia" menu became a group of Places & families
     the twenty-four pages of "The D'Arcys", "The Sanigers" and "Bristol and the Potteries" became the three groups of one new menu,
     "The studies", each moved as it was.
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
    ["/new-generations/", "Not in the Tree"], ["/hornby/", "The Hornby Claim"], ["/name/", "The Name"],
  ]],
  ["People", [
    { head: "Lists", items: [
      ["/people/", "The People"], ["/who/", "Every Name"], ["/register/", "The Register"], ["/households/", "Households"],
      ["/marriages/", "The Marriages"], ["/graves/", "Graves"],
    ] },
    { head: "Drawn", items: [
      ["/tree/", "Our line, drawn"], ["/trees/", "The trees"], ["/roots/", "Roots & Routes"], ["/timeline/", "The Timeline"],
      ["/bloodline/", "Blood relatives, drawn"],
    ] },
  ]],
  ["Places & families", [
    /* The group heading is the link to the index (/families/, /places/): it used to repeat as the first item under a heading of the same
       words ("The families" over "The Families", "Places" over "Places"). Order of "The families" (family-menu-rule.md, David, 12 Nov
       2026): the index (the heading), the own line (Sneyd), the other surnames A to Z, then the pages that are not a surname. */
    { head: "The families", href: "/families/", items: [
      ["/sneyd/", "Sneyd"],
      ...SURNAMES,
      ["/the-women/", "The Women"], ["/sergeant-sneyd/", "Sergeant Sneyd"],
    ] },
    { head: "Places", href: "/places/", items: [
      ["/atlas/", "The Atlas"], ["/lines/", "The Lines"],
    ] },
    { head: "Australia", items: [
      ["/emigrations/", "How They Got Here"], ["/general-hewitt/", "The General Hewitt, 1854"], ["/australia/", "Arrival, 1826"],
      ["/brisbane/", "Brisbane"], ["/great-war/", "The Great War"],
    ] },
  ]],
  ["The studies", [
    { head: "The D'Arcys", items: [
      ["/robert-family/", "Robert and Jean's Family"], ["/the-corps/", "The Corps — Robert's Career"], ["/obituary/", "The Obituary, 1827"],
      ["/joseph-darcy/", "Joseph D'Arcy, R.A."], ["/margaret-jones/", "Daughter of the Major-General"], ["/constantine/", "Constantine, Nineteen"],
      ["/sussex-sisters/", "The Sussex Sisters"], ["/george-pitt/", "Miss Ludlam of Guernsey"], ["/chatham/", "Chatham — the Corps' Parish"],
      ["/portsea/", "Two Years of Portsea"],
    ] },
    { head: "The Sanigers", items: [
      ["/hannah-baptism/", "One Vowel — Hannah's Baptism"], ["/berkeley-woman/", "Hannah Was a Berkeley Woman"],
      ["/thomas-sinegar/", "Thomas Sinegar — Her Brother"], ["/berkeley/", "Berkeley, Gloucestershire"], ["/sanigers/", "The Sanigers of the Vale"],
      ["/saniger-place/", "Saniger Is a Place"], ["/spellings/", "Every Spelling of One Name"], ["/swonhungre/", "The Name in Its Own Century"],
      ["/saniger-1608/", "The Muster of 1608"], ["/chew-magna/", "Chew Magna — Wrong, and a Family"],
    ] },
    { head: "Bristol and the Potteries", items: [
      ["/wakefields/", "The Wakefields"], ["/drivers-fields/", "Drivers Fields, 1841"], ["/bristol-chapels/", "The Bristol Chapels"],
      ["/sneyds/", "The Sneyds of the Potteries"],
    ] },
  ]],
  ["Research", navGroups],
];

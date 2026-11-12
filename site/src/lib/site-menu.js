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
   The twelve lineage pages (/families/<slug>/, from data/family-lines.json) STAY in the menu: the /families/ index does link every one
   (docs/menu-a-reach.md), but tools/check_family_lines.py holds that the navigation on /families/ links each of them as well as the
   index card, and trimming them would mean changing that gate, which this menu-only PR does not do. */
import { navGroups } from "./research-menu.js";
import familyLines from "../data/family-lines.json";

/* LINEAGE: true = listed, as before (the family-lines gate requires it); false would leave them to the /families/ index. */
const LINEAGE = true;

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
    { head: "The families", items: [
      ["/families/", "The Families"], ["/the-women/", "The Women"], ["/sneyd/", "Sneyd"], ["/sergeant-sneyd/", "Sergeant Sneyd"],
      ["/murdoch/", "Murdoch"], ["/atkinson/", "Atkinson"],
      /* the names the direct line carries that have no page of their own elsewhere (src/data/family-lines.json), in the order the
         file ranks them; see LINEAGE */
      ...(LINEAGE ? familyLines.lines.map((l) => [`/families/${l.slug}/`, l.surname]) : []),
    ] },
    { head: "Places", items: [
      ["/places/", "Places"], ["/atlas/", "The Atlas"], ["/lines/", "The Lines"],
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

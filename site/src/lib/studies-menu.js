/* THE STUDIES, one list: the twenty-four long pages (and the six deep dives) that stood in the header menu as "The studies" until
   23 November 2026. The menu now carries ONE entry, "The studies" (lib/research-menu.js, Research / Sources & method), which opens the hub
   /studies/ (pages/studies.astro); the hub reads THIS list, so the menu and the hub cannot disagree. No study was renamed, moved or
   deleted: every href is the address it always had, and every label is the one the menu gave it.
   The three groups are the three the menu had. The deep dives are the group the Research menu used to list (lib/research-menu.js: the
   Sources page lists them too); the hub shows them last. */
import { RESEARCH } from "./research-menu.js";

export const STUDIES = [
  { id: "darcys", head: "The D'Arcys",
    dek: "One page each for the people and parishes around Robert D'Arcy, the engineer at Chatham.",
    items: [
      ["/robert-family/", "Robert and Jean's Family"], ["/the-corps/", "The Corps — Robert's Career"], ["/obituary/", "The Obituary, 1827"],
      ["/joseph-darcy/", "Joseph D'Arcy, R.A."], ["/margaret-jones/", "Daughter of the Major-General"], ["/constantine/", "Constantine, Nineteen"],
      ["/sussex-sisters/", "The Sussex Sisters"], ["/george-pitt/", "Miss Ludlam of Guernsey"], ["/chatham/", "Chatham — the Corps' Parish"],
      ["/portsea/", "Two Years of Portsea"],
    ] },
  { id: "sanigers", head: "The Sanigers",
    dek: "One page each for the Saniger name and the Berkeley records: a baptism, a muster, a place and the spellings.",
    items: [
      ["/hannah-baptism/", "One Vowel — Hannah's Baptism"], ["/berkeley-woman/", "Hannah Was a Berkeley Woman"],
      ["/thomas-sinegar/", "Thomas Sinegar — Her Brother"], ["/berkeley/", "Berkeley, Gloucestershire"], ["/sanigers/", "The Sanigers of the Vale"],
      ["/saniger-place/", "Saniger Is a Place"], ["/spellings/", "Every Spelling of One Name"], ["/swonhungre/", "The Name in Its Own Century"],
      ["/saniger-1608/", "The Muster of 1608"], ["/chew-magna/", "Chew Magna — Wrong, and a Family"],
    ] },
  { id: "bristol", head: "Bristol and the Potteries",
    dek: "Pages on the Wakefields, the Bristol records and the Sneyds of the Potteries.",
    items: [
      ["/wakefields/", "The Wakefields"], ["/drivers-fields/", "Drivers Fields, 1841"], ["/bristol-chapels/", "The Bristol Chapels"],
      ["/sneyds/", "The Sneyds of the Potteries"],
    ] },
];

/* the deep dives, as the Research menu's list holds them (a sub-group of Sources & method): { href, label } */
export const DEEP_DIVES = RESEARCH.flatMap((g) => g.items).find((x) => x.sub).items;

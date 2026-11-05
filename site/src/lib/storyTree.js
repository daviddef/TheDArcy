/* THE TREE SHAPE THE KIT'S STORY FUNCTIONS READ (kit/lib/personstory.js: familyOf, famNode), made from the people the person pages draw (lib/people.js)
 * and from nothing else: the same people, slugs, names and corrections, so a card in a story and the page it links to cannot disagree.
 *
 *   byId[id] = { id, given, sur, sex, by, bye, dy, dye, bp, line, href, father, mother, kids[], spouse[], saidLiving, dead }
 *
 * EVERY person is here, the living included, because the kit's own living rule (lib/person.js, through famNode) decides what a card may say: a living
 * relative is a NAME and a RELATIONSHIP and nothing else (no year, no place), and the name still links to their page, which is itself only a name,
 * relationships and a town and country. This is why the story does not read Roots & Routes' tree.json: that omits the living, so a living child or
 * sister would silently vanish from the story that the family chart draws today. `saidLiving` is people.js's own judgement (tools/build_site_data.py);
 * the kit's rule is asked as well, and the page refuses to build where the two disagree (src/pages/people/[slug].astro, KLIVE).
 *
 * A year is the year the page prints: the archive's corrected one where lib/corrections.js has overturned the tree's, else the first year in the tree's
 * date; `bye` / `dye` mark an estimate ("c."): a tree date written ABT, EST, CAL, BEF, AFT or BET..AND, or a correction the archive words as
 * "about", "by" or "probably". The given name is the whole name as printed (the tree's split into given and surname is not carried here) and the surname is empty.
 */
import { people } from "./people.js";
import { CORRECTIONS } from "./corrections.js";

const firstYear = (v) => { const m = /\b(1[0-9]\d\d|20\d\d|[5-9]\d\d)\b/.exec(String(v ?? "")); return m ? Number(m[1]) : null; };
const estimated = (v) => /^\s*(ABT|EST|CAL|BEF|AFT|BET)\b/i.test(String(v ?? "")) || /\bor\b/i.test(String(v ?? ""));
const said = (slug, field, raw) => {
  const c = CORRECTIONS[slug] && CORRECTIONS[slug][field];
  if (c) return { y: firstYear(c[0]), est: /^(about|by|probably)\b/i.test(c[0]) || /\bor\b|unresolved/i.test(c[0]) };
  return { y: firstYear(raw), est: estimated(raw) };
};

const ids = new Set(people.map((p) => p.id));
const byPerson = new Map(people.map((p) => [p.id, p]));

export const TREE_BY = {};
for (const p of people) {
  const b = said(p.slug, "born", p.born), d = said(p.slug, "died", p.died);
  const par = (p.parents || []).map((x) => x.id).filter((i) => ids.has(i) && i !== p.id);
  /* the father is the parent recorded male, the mother the one recorded female; a parent of unrecorded sex is read in the order the tree lists them */
  let father = par.find((i) => byPerson.get(i).sex === "M") || null;
  let mother = par.find((i) => byPerson.get(i).sex === "F" && i !== father) || null;
  const rest = par.filter((i) => i !== father && i !== mother);
  if (!father && rest.length) father = rest.shift();
  if (!mother && rest.length) mother = rest.shift();
  const kids = [...new Set((p.spouses || []).flatMap((s) => (s.children || []).filter((c) => ids.has(c))))];
  const spouse = [...new Set((p.spouses || []).map((s) => s.id).filter((i) => ids.has(i)))];
  TREE_BY[p.id] = {
    id: p.id, given: p.name, sur: "", sex: (p.sex || "").toLowerCase() || "u",
    by: p.living ? null : b.y, bye: !p.living && b.est, dy: p.living ? null : d.y, dye: !p.living && d.est,
    bp: p.living ? "" : p.bornPlace || "", line: 1, href: `/people/${p.slug}/`,
    father, mother, kids, spouse,
    saidLiving: p.living === true,
    /* a recorded death, dated or not (the same test the page's own chart uses, diedRecorded) */
    dead: !p.living && !!(CORRECTIONS[p.slug]?.died || p.died || p.diedPlace || p.burial),
  };
}

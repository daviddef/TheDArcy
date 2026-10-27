#!/usr/bin/env node
/* THE FAMILY RIBBONS: site/src/data/family-ribbons.json (the kit's contract, kit/docs/family-ribbon.md) and
 * site/src/data/family-no-ribbon.json, made from this archive's own data. Nothing in either file is typed.
 *
 *     node --import ./tools/jsonhooks.mjs tools/build_family_ribbons.mjs            write both files
 *     node --import ./tools/jsonhooks.mjs tools/build_family_ribbons.mjs --check    refuse (exit 1) a stale file
 *
 * (The file is called family-ribbons.json because family-lines.json already names this archive's twelve extra surname
 * pages; the kit's gate is given the path.)
 *
 * WHICH PAGES. A family page here is one surname's page: the thirteen clusters of families.json and the twelve names of
 * family-lines.json, each at /families/<slug>/, and the Sanigers (the spellings family-lines.json pagesElsewhere sends to
 * /sanigers/; their ribbon is on their lane's page, /saniger-line/, "Six generations at Berkeley"). Their people are the
 * people those pages list (site/src/lib/familyLines.js), read here through the same modules the pages use, so a slug, a
 * year or a name cannot differ between the ribbon and the page under it. The same ribbon is drawn again on the narrative
 * pages of three of them (/murdoch/, /atkinson/, /wakefields/; see src/components/FamilyLine.astro).
 *
 * THE CARDS: ONE CHAIN, OFF THE NUMBERED PEDIGREE. ancestors.json numbers our ancestors (1 is the youngest generation, 2n
 * a person's father, 2n+1 the mother). A family's cards are its nearest numbered ancestor who is dead and not above a
 * graft, then that person's father, his father, and so on while the father is of the same family, is dead and is not
 * above a graft (provenance.json `graft`: Hornby, the unevidenced descent above Robert D'Arcy; Keele, the descent this
 * archive tested and found wrong). Earliest first. A family with no such person gets NO ribbon (family-no-ribbon.json),
 * and the page says only how it stands to our line. Nothing is added: a generation the pedigree does not number is not
 * drawn, and the living are never drawn on a family ribbon (they stay on the story's own ribbon, by relationship).
 *
 *   name, years   the person's page's own (site/src/lib/people.js: the corrections already applied)
 *   origin        where the archive says they were born or baptised, and its grade (the outline):
 *                   a story card's own origin and grade, for the six people the story draws;
 *                   else a lines.json node for the person that is a birth or a baptism: its place, its evidence word;
 *                   else a correction of the birthplace (lib/corrections.js): documented when it rests on a record;
 *                   else the tree's birthplace: documented only when provenance.json holds a baptism, christening or
 *                   birth record of theirs that names the same town, and otherwise the family's tree (dotted).
 *   spouse        the other parent at the same number on the pedigree (2n+1 beside 2n); "not named in the tree" when
 *                 the pedigree has the slot and no name; nothing when it has no slot.
 *   at            where they died, when the tree gives a town and it is not the town they came from.
 *
 * HOW OUR LINE CONNECTS. "Our line" is src/data/direct-line.json (made from the story by the kit's directline.py): the
 * story's six people and their six wives, each a numbered ancestor. For every one of them, X:
 *   - X married S, when S is of this family and X is one of the six people (not of this family themselves);
 *   - X son of / daughter of P, when P is X's parent on the pedigree and is of this family, and X is not of this family
 *     (or X and P are both among the story's six people: the D'Arcy family's own steps).
 * The grade of a connection is the archive's: documented when provenance.json holds a record that writes the pair down;
 * else the grade of the story paragraph that tells it (STORY_SAYS below: the quoted words must be in that paragraph of
 * story.json, with that grade, or this tool stops); else the family's tree. A family that touches none says why, from
 * the pedigree: who of the name stands nearest the line, and how far from it.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SITE = join(ROOT, "site");
const DATA = join(SITE, "src", "data");
const OUT = join(DATA, "family-ribbons.json");
const OUT_NONE = join(DATA, "family-no-ribbon.json");

const J = (f) => JSON.parse(readFileSync(join(DATA, f), "utf8"));
const P = await import(join(SITE, "src", "lib", "people.js"));
const FL = await import(join(SITE, "src", "lib", "familyLines.js"));
const { CORRECTIONS } = await import(join(SITE, "src", "lib", "corrections.js"));
const { tidyPlace } = await import(join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "lib", "place.js"));

const ancestors = J("ancestors.json");
const families = J("families.json");
const flCfg = J("family-lines.json");
const prov = J("provenance.json");
const lines = J("lines.json");
const story = J("story.json");
const direct = J("direct-line.json");

const die = (msg) => { console.error("build_family_ribbons: " + msg); process.exit(1); };

/* ---------------------------------------------------------------- who is on our line */
const DL = new Map();
for (const p of direct.people) DL.set(p.slug, { ...p, role: "line" });
for (const p of direct.partners) if (!DL.has(p.slug)) DL.set(p.slug, { ...p, role: "partner" });
const LINE_PEOPLE = new Set(direct.people.map((p) => p.slug));
const STORY_CARD = new Map(story.ribbon.cards.filter((c) => c.person).map((c) => [c.person, c]));

/* ---------------------------------------------------------------- the pedigree */
const byAhn = new Map(ancestors.map((a) => [a.ahn, a]));
const ahnOfId = new Map(ancestors.map((a) => [a.id, a.ahn]));
const person = (id) => P.byId.get(id) || null;
const slugOfId = (id) => (P.byId.get(id) || {}).slug || null;
const graftOf = (slug) => (prov[slug] && prov[slug].graft) || null;
const isLiving = (id) => !!(person(id) && person(id).living);

/* ---------------------------------------------------------------- the families and their people */
/* the lines.json lane of a family, where its page's lane exists */
const LANE_OF = { "d-arcy": "darcy", sneyd: "sneyd", atkinson: "atkinson", murdoch: "murdoch", wakefield: "wakefield", saniger: "saniger" };
const laneOf = (fid) => (LANE_OF[fid] ? lines.lanes.find((l) => l.key === LANE_OF[fid]) || die(`no lane ${LANE_OF[fid]} in lines.json`) : null);

const fams = [];
for (const f of families) {
  const id = P.kebab(f.surname);
  fams.push({ id, title: f.surname, page: `/families/${id}/`, ids: new Set(FL.clusterMembers(f).filter((m) => !P.duplicateOf(m)).map((m) => m.id)) });
}
for (const l of FL.allLines()) fams.push({ id: l.slug, title: l.surname, page: `/families/${l.slug}/`, ids: new Set(l.members.map((m) => m.id)) });
{
  const keys = new Set(Object.entries(flCfg.pagesElsewhere).filter(([k, v]) => k !== "_note" && v.href === "/sanigers/").map(([k]) => k));
  const ids = new Set(P.people.filter((p) => !P.duplicateOf(p) && keys.has(FL.surnameKey(p.surname))).map((p) => p.id));
  /* the Saniger lane's own page (lines.json), "Six generations at Berkeley"; /sanigers/ is the county reconstitution */
  fams.push({ id: "saniger", title: "Saniger", page: laneOf("saniger").href, ids });
}
const famOfId = (id) => fams.filter((f) => f.ids.has(id)).map((f) => f.id);
for (const a of ancestors) if (famOfId(a.id).length > 1) die(`${a.name} is on two family pages (${famOfId(a.id).join(", ")})`);

/* ---------------------------------------------------------------- places */
const STREET = /\d|\b(street|road|rd|terrace|quay|avenue|lane)\b|\bst\.?$|^no\b/i;   /* "St Quivox" is a saint, "Well St" a street */
const ENT = { "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&amp;": "&" };
const clean = (s) => String(s || "").replace(/&(?:lt|gt|quot|#39|amp);/g, (m) => ENT[m]).replace(/[<>]/g, "")
  .replace(/^\s*(?:christened|baptised|baptized)\s+(?:in|at)\s+/i, "").replace(/^\s*of\s+/i, "").replace(/\s+/g, " ").trim();
/* a place as a card can carry it: the tree's own words, its street levels dropped, the general levels cut to fit */
function placeText(raw, max = 28) {
  const segs = clean(raw).split(",").map((s) => s.trim()).filter((s) => s && !STREET.test(s) && s !== "?");
  return segs.length ? tidyPlace(segs.join(", "), max) : "";
}
const town = (s) => String(s || "").split(",")[0].trim().toLowerCase();
const yearsOf = (life) => (String(life || "").match(/\b1[0-9]{3}\b|\b20[0-9]{2}\b/g) || []);

/* ---------------------------------------------------------------- a card's origin and its grade */
const EVIDENCE_GRADE = { read: "doc", indexed: "inf", scanned: "inf", inferred: "inf", tree: "lore", disputed: "lore", none: "lore" };
const LANE_NODE = new Map();
for (const l of lines.lanes) for (const n of l.nodes || []) if (n.person && /\b(baptised|baptized|christened|born)\b/i.test(n.why || "")) LANE_NODE.set(n.person, n);
const BIRTH_CITE = /\b(baptism|baptised|christening|christened|birth reg)/i;

function originOf(p) {
  const slug = p.slug;
  const sc = STORY_CARD.get(slug);
  if (sc) return { origin: sc.origin, originGrade: sc.originGrade, how: "the story's card" };
  const n = LANE_NODE.get(slug);
  if (n) return { origin: n.place, originGrade: EVIDENCE_GRADE[n.evidence] || "lore", how: `lines.json node (${n.evidence})` };
  const c = CORRECTIONS[slug] && CORRECTIONS[slug].bornPlace;
  if (c) return { origin: placeText(c[0]), originGrade: /\b(baptism|census|register|form)\b/i.test(c[1]) ? "doc" : "inf", how: "lib/corrections.js" };
  const o = placeText(p.bornPlace);
  if (!o) return { origin: "place not known", originGrade: "lore", how: "no birthplace" };
  const rel = (prov[slug] && prov[slug].rel) || {};
  const parents = new Set(((byAhn.get(ahnOfId.get(p.id)) || {}).parents || []).map((x) => slugOfId(x.id)).filter(Boolean));
  const cites = Object.entries(rel).filter(([k]) => parents.has(k)).flatMap(([, v]) => v).filter((x) => BIRTH_CITE.test(x));
  if (cites.some((x) => x.toLowerCase().includes(town(o)))) return { origin: o, originGrade: "doc", how: `provenance: ${cites[0]}` };
  return { origin: o, originGrade: "lore", how: "the tree's birthplace" };
}

/* ---------------------------------------------------------------- the cards */
function cardFor(a) {
  const p = person(a.id);
  const sc = STORY_CARD.get(p.slug);
  if (sc) {
    return { name: sc.name, years: sc.years, origin: sc.origin, originGrade: sc.originGrade, spouse: sc.spouse, spouseOrigin: sc.spouseOrigin,
             atPlace: sc.atPlace, atYear: sc.atYear, living: false, person: p.slug, ...(sc.spousePerson ? { spousePerson: sc.spousePerson } : {}),
             title: sc.title || "" };
  }
  const o = originOf(p);
  const mate = byAhn.get(a.ahn ^ 1);
  let spouse = "", spouseOrigin = "", spousePerson = null;
  if (mate) {
    const mp = person(mate.id);
    if (!mate.name || /^\(unnamed\)$/.test(mate.name) || !mp) spouse = "not named in the tree";
    else if (mp.living) die(`${p.name}'s spouse is living; a family ribbon draws the dead`);
    else {
      spouse = mp.name;
      const so = originOf(mp);
      spouseOrigin = so.how === "no birthplace" ? "place not known" : `of ${so.origin}`;
      spousePerson = mp.slug;
    }
  }
  const died = placeText(p.diedPlace);
  const dy = yearsOf(p.life)[1] || "";
  const at = died && dy && town(died) !== town(o.origin) ? { atPlace: died.split(",")[0], atYear: dy } : { atPlace: "", atYear: "" };
  const lane = LANE_NODE.get(p.slug);
  return { name: p.name, years: p.life || "", origin: o.origin, originGrade: o.originGrade, spouse, spouseOrigin, ...at, living: false,
           person: p.slug, ...(spousePerson ? { spousePerson } : {}), title: lane ? lane.why : "", _how: o.how };
}

function chainOf(f) {
  const eligible = (a) => a && f.ids.has(a.id) && !isLiving(a.id) && person(a.id) && !graftOf(person(a.id).slug);
  const on = ancestors.filter(eligible).sort((x, y) => x.ahn - y.ahn);
  if (!on.length) return [];
  const chain = [on[0]];
  for (let n = on[0].ahn * 2; eligible(byAhn.get(n)); n *= 2) chain.push(byAhn.get(n));
  return chain.reverse();
}

/* ---------------------------------------------------------------- the connections */
/* What the story says of a link, in its own graded paragraph. The words must be found there or the tool stops. */
const STORY_SAYS = {
  "george-pitt-d-arcy-1783|robert-d-arcy|son of": { chapter: "major", quote: "He was almost certainly Robert's son, though no paper names his father." },
  "george-pitt-d-arcy-1783|jean-ward|son of": { chapter: "engineer", quote: "That George Pitt was one of these sons is the archive's reasoning from a newspaper, set out in the next chapter." },
  "george-lindsay-d-arcy|george-pitt-d-arcy-1783|son of": { chapter: "major", quote: "He was christened at St James's, Sydney, on 5 November, «father George Pitt Darcy, mother Maria»." },
  "george-pitt-d-arcy-1864|george-lindsay-d-arcy|son of": { chapter: "railway", quote: "His death registration names his parents, Eliza Keeling and George Lindesay D'Arcy" },
  "george-pitt-d-arcy-1864|eliza-keeling|son of": { chapter: "railway", quote: "His death registration names his parents, Eliza Keeling and George Lindesay D'Arcy" },
  "lindesay-atkinson-d-arcy|george-pitt-d-arcy-1864|son of": { chapter: "sergeant", quote: "Lindesay Atkinson D'Arcy was born in Brisbane on 15 July 1892, the only son of the railway clerk" },
  "kenneth-lindsay-d-arcy|lindesay-atkinson-d-arcy|son of": { chapter: "ken", quote: "No record the archive has read names his parents." },
  "kenneth-lindsay-d-arcy|ivy-miriam-sneyd|son of": { chapter: "ken", quote: "No record the archive has read names his parents." },
  "robert-d-arcy|jean-ward|married": { chapter: "engineer", quote: "On 21 June 1779 he married Jean Ward at St Mary's, Portsea." },
  "george-lindsay-d-arcy|eliza-keeling|married": { chapter: "scholar", quote: "That same year, on 7 June 1863, he married Eliza Keeling." },
  "george-pitt-d-arcy-1864|ida-kathleen-atkinson|married": { chapter: "railway", quote: "On 10 October 1888 he married Ida Kathleen Atkinson at Trinity Church, Fortitude Valley." },
  "lindesay-atkinson-d-arcy|ida-kathleen-atkinson|son of": { chapter: "railway", quote: "The tree gives her birth at Brisbane in 1869 and four children: Hilda Georgina in 1890, Lindesay Atkinson in 1892" },
  "ida-kathleen-atkinson|jane-creech|daughter of": { chapter: "railway", quote: "Ida's mother, Jane Creech, was of Limerick too, by the family's tree." },
  "lindesay-atkinson-d-arcy|ivy-miriam-sneyd|married": { chapter: "sergeant", quote: "On 18 March 1916 he married Ivy Miriam Sneyd at Albion Church." },
  "ivy-miriam-sneyd|martha-blum|daughter of": { chapter: "sergeant", quote: "The tree has her born at Boulia on 31 October 1891, to Arthur William Hartley Sneyd and Martha Blum" },
  "kenneth-lindsay-d-arcy|audrey-dell-murdoch|married": { chapter: "ken", quote: "on 5 April 1952 they were married, at Toowoomba by the tree's account." },
};
const plain = (t) => String(t || "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/\*/g, "");
function storySays(key) {
  const s = STORY_SAYS[key];
  if (!s) return null;
  const ch = story.chapters.find((c) => c.id === s.chapter) || die(`STORY_SAYS ${key}: no chapter ${s.chapter}`);
  const para = (ch.paragraphs || []).find((p) => plain(p.text).includes(s.quote));
  if (!para) die(`STORY_SAYS ${key}: the words «${s.quote}» are not in the chapter ${s.chapter}`);
  if (!["doc", "inf", "lore"].includes(para.grade)) die(`STORY_SAYS ${key}: the paragraph has no grade`);
  return { ...s, grade: para.grade };
}
const disagreements = [];
const used = new Set();

function connection(x, their, relation, fam) {
  const ours = DL.get(x.slug);
  const key = `${x.slug}|${their.slug}|${relation}`;
  const recs = [...new Set([...(((prov[x.slug] || {}).rel || {})[their.slug] || []), ...(((prov[their.slug] || {}).rel || {})[x.slug] || [])])];
  const said = storySays(key);
  if (said) used.add(key);
  let grade, note, chapter = ours.storyChapter;
  if (recs.length) {
    grade = "doc";
    note = `Read: ${recs.join("; ")}.`;
    if (said) chapter = said.chapter;
    if (said && said.grade !== "doc") disagreements.push(`${key}: a record is read (${recs.join("; ")}), the story's paragraph is graded ${said.grade}`);
  } else if (said) {
    grade = said.grade; chapter = said.chapter;
    note = said.quote.replace(/^[a-z]/, (m) => m.toUpperCase()) + (/[.»]$/.test(said.quote) ? "" : " \u2026");
  } else {
    grade = "lore";
    note = "The family's tree; no record of it is read here, and the story does not tell it.";
  }
  const o = originOf(their);
  return { ourSlug: x.slug, ourGeneration: ours.generation, theirSlug: their.slug, theirName: their.name,
           ...(o.how !== "no birthplace" && o.origin ? { theirOrigin: `of ${o.origin}` } : {}), relation, grade, storyHref: `/story/#${chapter}`, note };
}

function connectionsOf(f) {
  const out = [];
  for (const [slug, e] of DL) {
    const x = P.bySlug.get(slug) || die(`direct-line.json names ${slug}, who has no page`);
    const xa = byAhn.get(ahnOfId.get(x.id)) || die(`${slug} is not on the numbered pedigree`);
    const xIn = f.ids.has(x.id);
    if (e.role === "line" && !xIn) {
      for (const s of xa.spouses || []) {
        const sp = s.id && person(s.id);
        if (sp && f.ids.has(sp.id)) out.push(connection(x, sp, "married", f));
      }
    }
    for (const par of xa.parents || []) {
      const pp = par.id && person(par.id);
      if (!pp || !f.ids.has(pp.id)) continue;
      if (xIn && !(LINE_PEOPLE.has(slug) && LINE_PEOPLE.has(pp.slug))) continue;
      out.push(connection(x, pp, x.sex === "F" ? "daughter of" : x.sex === "M" ? "son of" : "child of", f));
    }
  }
  return out.sort((a, b) => a.ourGeneration - b.ourGeneration || a.relation.localeCompare(b.relation));
}

const KIN = (k, sex) => {
  const w = sex === "F" ? ["mother", "grandmother"] : ["father", "grandfather"];
  return k === 1 ? w[0] : k === 2 ? w[1] : "great-".repeat(k - 2) + w[1];
};
const GRAFT_WHY = {
  Hornby: "the Hornby join, the descent the family's tree claims above Robert D'Arcy, a single link this archive has looked for and not found",
  Keele: "the Keele join, a link this archive has looked for in the right registers and found to be wrong",
};
function whyNot(f) {
  const on = ancestors.filter((a) => f.ids.has(a.id) && person(a.id)).sort((x, y) => x.ahn - y.ahn);
  if (!on.length) return `No one of the name stands on this archive's numbered pedigree, and none is a parent or a spouse of anyone on our line.`;
  const free = on.filter((a) => !isLiving(a.id) && !graftOf(person(a.id).slug));
  if (!free.length) {
    const g = [...new Set(on.map((a) => graftOf(person(a.id).slug)).filter(Boolean))];
    const first = on[0];
    return `Everyone of the name on this archive's numbered pedigree stands above ${g.map((x) => GRAFT_WHY[x] || x).join(", and above ")}; the nearest is ${first.name} (number ${first.ahn}).`;
  }
  const a = free[0];
  let n = a.ahn, k = 0, hit = null;
  while (n > 1) {
    n = Math.floor(n / 2); k += 1;
    const b = byAhn.get(n);
    if (b && person(b.id) && DL.has(person(b.id).slug)) { hit = { b, e: DL.get(person(b.id).slug) }; break; }
  }
  if (!hit) die(`${f.id}: the pedigree number ${a.ahn} reaches nobody on the line`);
  return `No one of the name is a parent or a spouse of anyone on our line. The nearest on this archive's numbered pedigree is ${a.name} (number ${a.ahn}), ${KIN(k, a.sex)} of ${hit.b.name}, who is on our line at generation ${hit.e.generation}.`;
}

/* ---------------------------------------------------------------- status */
function statusOf(f, cards) {
  const lane = laneOf(f.id);
  if (lane) return { status: lane.status, ...(lane.statusNote ? { statusNote: lane.statusNote } : {}), ...(lane.span ? { span: lane.span } : {}) };
  const docs = cards.filter((c) => c.originGrade === "doc");
  if (!docs.length) return { status: "family-lore", statusNote: "no lane on the lines page; every card here rests on the family's tree" };
  const y = +yearsOf(docs[0].years)[0] || null;
  return { status: "origin-unknown", statusNote: "no lane on the lines page; read from the cards' own grades", ...(y ? { span: [y, null] } : {}) };
}

/* ---------------------------------------------------------------- build */
const withCards = [], without = [], report = [];
for (const f of fams) {
  const chain = chainOf(f);
  const conns = connectionsOf(f);
  const cards = chain.map(cardFor);
  const base = { id: f.id, title: f.title, page: f.page };
  const link = conns.length ? { connections: conns } : { notConnected: { why: whyNot(f) } };
  if (cards.length) {
    withCards.push({ ...base, ...statusOf(f, cards), cards: cards.map(({ _how, ...c }) => c), ...link });
  } else {
    if (conns.length) die(`${f.id}: connected and no card to draw`);
    without.push({ ...base, ...link });
  }
  report.push({ id: f.id, cards: cards.map((c) => `${c.name} [${c.years}] from ${c.origin} (${c.originGrade}; ${c._how || ""})${c.spouse ? " m. " + c.spouse + " " + c.spouseOrigin : ""}${c.atPlace ? " at " + c.atPlace + " " + c.atYear : ""}`),
                conns: conns.map((c) => `${c.ourSlug} ${c.relation} ${c.theirSlug} [${c.grade}] ${c.storyHref}`), why: link.notConnected && link.notConnected.why });
}
for (const k of Object.keys(STORY_SAYS)) if (!used.has(k)) die(`STORY_SAYS ${k} is not a connection any more`);

const NOTE = "Made by tools/build_family_ribbons.mjs from ancestors.json, families.json, family-lines.json, provenance.json, lines.json, story.json and direct-line.json; do not edit by hand. The rule is in the tool's header.";
const out = JSON.stringify({ _note: NOTE, families: withCards }, null, 1) + "\n";
const outNone = JSON.stringify({ _note: NOTE + " These families have no ribbon: nobody of the name on the numbered pedigree is dead and below a graft.", families: without }, null, 1) + "\n";

const args = process.argv.slice(2);
if (args.includes("--report")) {
  for (const r of report) { console.log("== " + r.id); r.cards.forEach((c) => console.log("   card " + c)); r.conns.forEach((c) => console.log("   conn " + c)); if (r.why) console.log("   why  " + r.why); }
  for (const d of disagreements) console.log("DISAGREES " + d);
}
if (args.includes("--check")) {
  const stale = [[OUT, out], [OUT_NONE, outNone]].filter(([p, s]) => { try { return readFileSync(p, "utf8") !== s; } catch { return true; } });
  if (stale.length) die(`${stale.map(([p]) => p.slice(ROOT.length + 1)).join(", ")} is not what the data makes: run node --import ./tools/jsonhooks.mjs tools/build_family_ribbons.mjs`);
  console.log(`  ok    family ribbons  ${withCards.length} families with a ribbon, ${without.length} without; ${withCards.reduce((n, f) => n + (f.connections || []).length, 0)} connections; both files are what the data makes`);
} else if (!args.includes("--report")) {
  writeFileSync(OUT, out);
  writeFileSync(OUT_NONE, outNone);
  console.log(`build_family_ribbons: wrote ${withCards.length} families with a ribbon and ${without.length} without`);
}

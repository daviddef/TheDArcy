/* THE FAMILY LINES: a page for a NAME that the direct line carries, drawn only
 * from people this archive already publishes.
 *
 * Written 17 October 2026, after David asked, of every archive, "do we have the
 * right family pages?" The answer here was: thirteen surnames have a page
 * (families.json, built by tools/build_site_data.py), and the direct line
 * carries a hundred and more names that have none. Making a page for each by
 * adding it to that list would have PUBLISHED EVERY PERSON OF THE NAME IN THE
 * TREE, which for Howard or Stuart is a decision about people nobody has made.
 * So a line is different on purpose:
 *
 *   - it is read from src/data/family-lines.json, which names the surname
 *     spellings and nothing else;
 *   - its people are the ones the archive ALREADY names (the numbered
 *     ancestors, the thirteen clusters, the relatives named beside them), so
 *     adding a line adds a page and publishes nobody;
 *   - and every sentence on its page is a count, a range or a link worked out
 *     here from that data. Nothing is typed. A line cannot say what the
 *     archive does not hold, because it has nowhere to put it.
 *
 * DECLARED COPIES ARE NEVER LISTED (same-person.json). A copy is one person
 * entered twice; counting it would count him twice.
 *
 * THE LIVING ARE A NAME, A RELATIONSHIP, A TOWN AND A COUNTRY (David's ruling,
 * 16 October 2026). This file reads no date for a living person, takes their
 * place only from `place`, and never uses `grade()` on them.
 */
import cfg from "../data/family-lines.json";
import clusters from "../data/families.json";
import ancestors from "../data/ancestors.json";
import { tidyPlace } from "@daviddef/archive-kit/lib/place.js";
import { people, byId, duplicateOf, kebab } from "./people.js";
import { grade } from "./grade.js";
import prov from "../data/provenance.json";

/** The key the config is written in: lowercased, apostrophes and quotes out,
 *  cut at the first comma, bracket or parenthesis (the tree writes a title or
 *  a gloss after the name). tools/audit_family_lines.py does the same. */
export const surnameKey = (s) =>
  String(s || "").toLowerCase().replace(/['"’*]/g, "").split(/[,(\[]/)[0].replace(/\s+/g, " ").trim();

const clusterSlug = new Map(clusters.map((f) => [surnameKey(f.surname), kebab(f.surname)]));
const clusterName = new Map(clusters.map((f) => [surnameKey(f.surname), f.surname]));

const KEY_TO_LINE = new Map();
for (const l of cfg.lines) for (const k of l.keys) KEY_TO_LINE.set(k, l);

/** The line a person belongs to, or null. */
export function lineOf(p) {
  if (!p || p.family) return null;                 // already in one of the thirteen
  const k = surnameKey(p.surname);
  const hit = KEY_TO_LINE.get(k);
  if (hit) return hit;
  for (const l of cfg.lines) {
    const w = l.alsoWhenNameHas && l.alsoWhenNameHas[k];
    if (w && String(p.name || "").toLowerCase().includes(w)) return l;
  }
  return null;
}

const born = (p) => +((p.born || p.life || "").match(/\d{4}/) || [9999])[0];
const yearsOf = (p) => (String(p.life || "").match(/\b\d{4}\b/g) || []).map(Number);

const aByAhn = new Map(ancestors.filter((a) => a.ahn).map((a) => [a.ahn, a]));

/** Where a name is written about, for a family another page mentions. */
export function pageForKey(k) {
  if (KEY_TO_LINE.has(k)) {
    const l = KEY_TO_LINE.get(k);
    return { label: l.surname, href: `/families/${l.slug}/` };
  }
  if (clusterSlug.has(k)) return { label: clusterName.get(k), href: `/families/${clusterSlug.get(k)}/` };
  const e = cfg.pagesElsewhere && cfg.pagesElsewhere[k];
  if (e && e.href) return { label: e.label, href: e.href };
  return null;
}

/** One town to a line however the tree spells what follows it. */
const townOf = (raw) => tidyPlace(raw, 40).split(",")[0].trim();
const townKey = (t) => t.toLowerCase().replace(/[^a-z0-9]/g, "");
const cache = new Map();

export function lineData(slug) {
  if (cache.has(slug)) return cache.get(slug);
  const line = cfg.lines.find((l) => l.slug === slug);
  const members = people
    .filter((p) => lineOf(p) === line && !duplicateOf(p))
    .sort((a, b) => born(a) - born(b) || String(a.name).localeCompare(b.name));
  const ids = new Set(members.map((m) => m.id));
  const dead = members.filter((m) => !m.living);
  const living = members.filter((m) => m.living);

  /* The spellings the tree uses, as written (cut as the key is cut). */
  const sp = new Map();
  for (const m of members) {
    const k = surnameKey(m.surname);
    const w = String(m.surname || "").split(/[,(\[]/)[0].trim() || k;
    const e = sp.get(k) || { written: w, n: 0 };
    e.n += 1; sp.set(k, e);
  }
  const spellings = [...sp.values()].sort((a, b) => b.n - a.n || a.written.localeCompare(b.written));

  /* Years of the dead only. */
  const ys = dead.flatMap(yearsOf);
  const span = ys.length ? [Math.min(...ys), Math.max(...ys)] : null;

  /* Where the dead were born, one town to a line however the tree spells the
     county after it. The living contribute no place here (a living person's
     town is on their own row). */
  const pl = new Map();
  for (const m of dead) {
    if (!m.bornPlace) continue;
    const t = townOf(m.bornPlace);
    const k = townKey(t);
    if (!k) continue;
    const e = pl.get(k) || { name: t, n: 0 };
    e.n += 1; pl.set(k, e);
  }
  const places = [...pl.values()].sort((a, b) => b.n - a.n || a.name.localeCompare(b.name));

  /* The direct line: who, which generation, and whose parent on the spine. */
  const direct = members.filter((m) => m.ahn).sort((a, b) => a.ahn - b.ahn).map((m) => {
    const child = aByAhn.get(Math.floor(m.ahn / 2));
    const kid = child ? byId.get(child.id) : null;
    const hide = !kid || kid.living;                // a living child is not named here
    return {
      name: m.living ? null : m.name, slug: m.living ? null : m.slug, ahn: m.ahn, gen: m.gen,
      sex: m.sex,
      childName: hide ? null : kid.name, childSlug: hide ? null : kid.slug, childAhn: child ? child.ahn : null,
      spelled: surnameKey(m.surname),
      spelledAs: String(m.surname || "").split(/[,(\[]/)[0].trim(),
      childSpelled: kid ? surnameKey(kid.surname) : null,
      childSpelledAs: kid ? String(kid.surname || "").split(/[,(\[]/)[0].trim() : null,
      childInLine: !!(kid && ids.has(kid.id)),
    };
  });

  /* The archive's own grading (grade.js, read off provenance.json): documented,
     disputed, or the family tree alone. Only for the dead; the living have no
     grade because they have no record here. */
  const tally = { documented: 0, disputed: 0, family: 0 };
  const grafts = {};                                // which graft, for the disputed
  let records = 0;
  for (const m of dead) {
    const g = grade(m.slug);
    tally[g.level] += 1;
    records += g.nRec || 0;
    if (g.level === "disputed") {
      const name = (prov[m.slug] || {}).graft || "a graft";
      grafts[name] = (grafts[name] || 0) + 1;
    }
  }

  /* THE SAME PERSON ENTERED TWICE AND NOT DECLARED. same-person.json holds the
     pairs the archive has ruled on; a copy in it is never listed. A pair it has
     NOT ruled on still shows: the same name, the same years of life, and the
     same parents (or, where neither has parents, the same birthplace) is the
     strong kind of evidence the declarations themselves require, and a page that
     counted both would count one man twice. They are listed as the tree lists
     them, joined into one group, and SAID, so the research owner can declare
     them. This page declares nothing. */
  const dk = new Map();
  for (const m of dead) {
    if (!m.life) continue;
    const par = (m.parents || []).map((r) => r.id).sort().join("+");
    const k = [String(m.name).toLowerCase(), m.life, par || String(m.bornPlace || "").toLowerCase()].join("|");
    if (!par && !m.bornPlace) continue;
    (dk.get(k) || dk.set(k, []).get(k)).push(m);
  }
  const twice = [...dk.values()].filter((v) => v.length > 1);

  /* GROUPS THE PUBLISHED PEOPLE DO NOT JOIN. A surname is not a family. Union
     the members through the people the archive names beside them (a parent, a
     brother or sister, a spouse, a child): two members who share any such
     person, or are one, are in one group. What is left is what the published
     tree actually ties together, and a name that is really two families shows
     as two groups. */
  const root = new Map(members.map((m) => [m.id, m.id]));
  const find = (x) => { while (root.get(x) !== x) { root.set(x, root.get(root.get(x))); x = root.get(x); } return x; };
  const union = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) root.set(ra, rb); };
  const via = new Map();                            // outside id -> members that touch it
  const touch = (m, id) => {
    if (!id) return;
    if (ids.has(id)) union(m.id, id);
    else { const a = via.get(id) || []; a.push(m.id); via.set(id, a); }
  };
  for (const m of members) {
    for (const r of m.parents || []) touch(m, r.id);
    for (const r of m.siblings || []) touch(m, r.id);
    for (const s of m.spouses || []) { touch(m, s.id); for (const c of s.children || []) touch(m, c); }
  }
  for (const list of via.values()) for (let i = 1; i < list.length; i++) union(list[0], list[i]);
  for (const v of twice) for (let i = 1; i < v.length; i++) union(v[0].id, v[i].id);
  const gmap = new Map();
  for (const m of members) { const r = find(m.id); (gmap.get(r) || gmap.set(r, []).get(r)).push(m); }
  const groups = [...gmap.values()].sort((a, b) => b.length - a.length || born(a[0]) - born(b[0])).map((g) => {
    const gd = g.filter((m) => !m.living);
    const gy = gd.flatMap(yearsOf);
    const gp = new Map();
    for (const m of gd) {
      if (!m.bornPlace) continue;
      const t = townOf(m.bornPlace);
      const k = townKey(t);
      if (!k) continue;
      const e = gp.get(k) || { name: t, n: 0 }; e.n += 1; gp.set(k, e);
    }
    return {
      members: g, n: g.length,
      span: gy.length ? [Math.min(...gy), Math.max(...gy)] : null,
      places: [...gp.values()].sort((a, b) => b.n - a.n || a.name.localeCompare(b.name)).slice(0, 3).map((x) => x.name),
      direct: g.filter((m) => m.ahn).length,
    };
  });

  /* THE FAMILIES IT IS JOINED TO: the surnames of the (dead) spouses of the
     members, and of the parents of a member who carry another name (a
     mother's, usually). A count of people involved, and a link where the
     archive has a page for the name. */
  const join = new Map();
  const note = (id, how) => {
    const o = byId.get(id);
    if (!o || o.living || lineOf(o) === line) return;
    const k = surnameKey(o.surname);
    if (!k || k === "unnamed") return;
    const e = join.get(k) || { key: k, written: String(o.surname).split(/[,(\[]/)[0].trim(), spouse: new Set(), parent: new Set() };
    e[how].add(o.id); join.set(k, e);
  };
  for (const m of members) {
    for (const s of m.spouses || []) if (s.id) note(s.id, "spouse");
    for (const r of m.parents || []) {
      const o = byId.get(r.id);
      if (o && surnameKey(o.surname) !== surnameKey(m.surname)) note(r.id, "parent");
    }
  }
  const joined = [...join.values()].map((e) => {
    const pg = pageForKey(e.key);
    return { label: pg ? pg.label : e.written, href: pg ? pg.href : null,
             spouses: e.spouse.size, parents: e.parent.size, n: e.spouse.size + e.parent.size };
  }).sort((a, b) => (b.href ? 1 : 0) - (a.href ? 1 : 0) || b.n - a.n || a.label.localeCompare(b.label));

  /* A key the tree uses for a TITLE in place of the surname (config:
     alsoWhenNameHas). It is not a spelling and is not reported as one. */
  const titledKeys = new Set(Object.keys(line.alsoWhenNameHas || {}));
  const titled = spellings.filter((x) => titledKeys.has(surnameKey(x.written)));

  /* Where the spelling changes inside the direct line: a father who writes the
     name one way and a son who writes it another, both in this line. */
  const shifts = direct.filter((d) => d.childInLine && d.childSpelled && d.childSpelled !== d.spelled
    && !titledKeys.has(d.spelled) && !titledKeys.has(d.childSpelled));

  const out = {
    line, slug, surname: line.surname, members, dead, living, spellings, span, places, direct,
    tally, grafts, records, groups, joined, shifts, twice, titled,
  };
  cache.set(slug, out);
  return out;
}

export const allLines = () => cfg.lines.map((l) => lineData(l.slug));
export const lineSlugs = cfg.lines.map((l) => l.slug);
export const lineCfg = cfg;

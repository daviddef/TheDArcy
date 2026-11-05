#!/usr/bin/env node
/* The people Roots & Routes may draw, read through the SAME module the person pages use (site/src/lib/people.js), so a slug, a name, a year and a
 * place are the ones the pages print, with the archive's own corrections (lib/corrections.js) applied.
 *
 *     node --import ./tools/jsonhooks.mjs tools/export_tree_people.mjs <out.json>
 *
 * Called by tools/build-tree-page.py. Nobody living is exported (people.js marks them; a living person is a name, a relationship and a town here, and
 * never a date), and the exported file is an intermediate that is not committed.
 *
 * CORRECTIONS. Where the archive has overturned the tree's birth or death (CORRECTIONS[slug].born / .died), the year the page prints is the corrected one
 * (the same yr() lib/corrections.js uses). A corrected birth or death PLACE replaces the tree's: used only when the correction is a plain place name
 * («Windsor, Brisbane»), and otherwise the tree's place is withdrawn and nothing is put in its place («unknown — Portsmouth or the West Indies»,
 * «In the field, France»). Declared duplicates (data/same-person.json) are exported as `copyOf` so the builder can draw the primary once.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SITE = join(ROOT, "site");
const out = process.argv[2];
if (!out) { console.error("usage: export_tree_people.mjs <out.json>"); process.exit(2); }

const { people } = await import(join(SITE, "src", "lib", "people.js"));
const { CORRECTIONS } = await import(join(SITE, "src", "lib", "corrections.js"));
const same = JSON.parse(readFileSync(join(SITE, "src", "data", "same-person.json"), "utf8"));
const COPY = new Map((same.pairs || []).map((x) => [x.copy, x.primary]));

const yr = (v) => (String(v || "").match(/\d{4}/) || [""])[0];
const PLAIN = /^[A-Z][A-Za-z.' ,-]{2,60}$/;   // a place name and nothing else: no dash of prose, no quotation marks, no digits
const plainPlace = (c) => (c && PLAIN.test(c[0]) && !/unknown|\bor\b|field/i.test(c[0]) ? c[0] : null);

const rows = [];
let correctedYears = 0, correctedPlaces = 0, withdrawnPlaces = 0;
for (const p of people) {
  if (p.living) continue;
  const c = CORRECTIONS[p.slug] || {};
  const row = {
    id: p.id, slug: p.slug, name: p.name, surname: p.surname || "", sex: p.sex || "", family: p.family || null,
    born: p.born || "", died: p.died || "", bornPlace: p.bornPlace || "", diedPlace: p.diedPlace || "",
    burial: p.burial || "", cause: p.cause || "", occupation: p.occupation || "",
    parents: (p.parents || []).map((x) => x.id), spouses: (p.spouses || []).map((s) => ({ id: s.id, children: s.children || [] })),
    copyOf: COPY.get(p.id) || null,
  };
  if (c.born) { row.born = yr(c.born[0]); correctedYears++; }
  if (c.died) { row.died = yr(c.died[0]); correctedYears++; }
  if (c.bornPlace) { const pl = plainPlace(c.bornPlace); row.bornPlace = pl || ""; pl ? correctedPlaces++ : withdrawnPlaces++; }
  if (c.diedPlace) { const pl = plainPlace(c.diedPlace); row.diedPlace = pl || ""; pl ? correctedPlaces++ : withdrawnPlaces++; }
  if (c.burial) row.burial = "";   // a corrected burial is prose about where the ground is not established; the burial place is not used as a place anyway
  rows.push(row);
}
writeFileSync(out, JSON.stringify({ people: rows, corrected_years: correctedYears, corrected_places: correctedPlaces, withdrawn_places: withdrawnPlaces }));
console.log(`export_tree_people: ${rows.length} people who are not living; corrections applied: ${correctedYears} years, ${correctedPlaces} places, ${withdrawnPlaces} places withdrawn`);

import ancestors from "../data/ancestors.json";
import families from "../data/families.json";

export const kebab = (s) =>
  String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

/* One person = one GEDCOM record. The tree is the authority on identity here;
   this archive's job is to say how well each record is evidenced, not to merge
   or split people behind the reader's back. */
function build() {
  const byId = new Map();

  const add = (rec, extra = {}) => {
    if (!rec || rec.living) return;            // living people never enter the build
    const prev = byId.get(rec.id);
    byId.set(rec.id, { ...(prev || {}), ...rec, ...extra });
  };

  for (const a of ancestors) add(a, { ancestor: true });
  for (const f of families) for (const m of f.members) add(m, { family: f.surname });

  const people = [...byId.values()];

  // slugs, disambiguated when a name repeats — and names repeat constantly:
  // there are two George Pitt D'Arcys and three Conyers.
  const counts = {};
  for (const p of people) counts[kebab(p.name)] = (counts[kebab(p.name)] || 0) + 1;
  const used = new Set();
  for (const p of people) {
    const base = kebab(p.name) || "unnamed";
    let slug = base;
    if (counts[base] > 1) {
      const yr = (p.born || p.died || "").match(/\d{4}/);
      slug = yr ? `${base}-${yr[0]}` : base;
    }
    while (used.has(slug)) slug += "-2";
    used.add(slug);
    p.slug = slug;
  }

  people.sort((a, b) => {
    const ya = +((a.born || "").match(/\d{4}/) || [9999])[0];
    const yb = +((b.born || "").match(/\d{4}/) || [9999])[0];
    return ya - yb || a.name.localeCompare(b.name);
  });
  return people;
}

export const people = build();
export const bySlug = new Map(people.map((p) => [p.slug, p]));
export const byId = new Map(people.map((p) => [p.id, p]));

export const nameOf = (id) => byId.get(id)?.name || "";
export const slugOf = (id) => byId.get(id)?.slug || "";

import ancestors from "../data/ancestors.json";
import families from "../data/families.json";
import living from "../data/living.json";

export const kebab = (s) =>
  String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");


/* THE LIVING RULE, AS A VALUE RATHER THAN AS SEVEN COPIES OF A FILTER.
 *
 * `build()` below has enforced it since this file was written — a living
 * person never enters `people` — but pages that read families.json DIRECTLY
 * bypass it, and every one of them wrote the rule out again for itself:
 *
 *     const shown = f.members.filter((m) => !m.living);
 *
 * Seven pages, seven copies, and on 22 September an eighth page was written
 * that did not inherit any of them. It published FORTY-FOUR living people —
 * caught by the gate, removed within the hour, and a gate is a net rather
 * than a guard. A rule that exists only as a line of presentation code in
 * one template is a rule the next template cannot know about.
 *
 * So it is a function, and it names the policy it is applying. living.json
 * already declares `policy`, and the archive's is `named-bare`: nobody is
 * published as a tree record, and the six named on purpose are named as
 * sources and provenance elsewhere, never from here.
 *
 * ALSO APPLIES ONE LEVEL OUT. The eighth page's second fault was subtler
 * than its first: seven living SPOUSES named on dead people's rows. The row
 * itself was legitimate, and the leak was in who else it mentioned. So
 * `nameIfPublishable` exists for that case — it returns a name or null, and
 * a caller that forgets to check gets nothing rather than a living person.
 */
export const livingPolicy = living.policy || "named-bare";

/** Every member of a family the archive may draw as a person. */
export const publishable = (members) =>
  (members || []).filter((m) => m && !m.living);

/** A name to print for somebody who may be living — or null, never a name. */
export const nameIfPublishable = (person) =>
  person && !person.living ? person.name || null : null;

/** How many are withheld. Counting is not publishing and needs its own door,
 *  or a page that only wants a number is pushed into a publishing helper. */
export const countLiving = (rows) => (rows || []).filter((r) => r && r.living).length;

/** The six named on purpose, and nobody else. A page that shows living people
 *  BY NAME — /bloodline is the only one — asks here rather than deciding for
 *  itself, so the list and the reasons stay in living.json where the owner
 *  confirmed them. */
const NAMED = new Set((living.named || []).map((n) => n.phrase));
export const isNamedOnPurpose = (name) => NAMED.has(name);
export const publishableOrNamed = (rows) =>
  (rows || []).filter((r) => r && (!r.living || NAMED.has(r.name)));

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

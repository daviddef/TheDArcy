import ancestors from "../data/ancestors.json";
import families from "../data/families.json";
import living from "../data/living.json";

export const kebab = (s) =>
  String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");


/* THE LIVING STANDARD, AS A VALUE RATHER THAN AS SEVEN COPIES OF A FILTER.
 *
 * Until 16 October 2026 this archive published no living person as a person,
 * and this file was where that was enforced: `build()` skipped them, and every
 * page that read families.json directly had to write the same filter out for
 * itself. On 22 September a page that did not published forty-four.
 *
 * David ruled on 16 October, knowing the tree holds 2,034 people it judges
 * living, that this archive adopts the standard the Defranceschi archive keeps:
 *
 *     A LIVING PERSON IS NAMED, WITH THEIR TOWN AND COUNTRY, AND NOTHING MORE.
 *
 * A name, a relationship, a town and a country. No date, no record, no source,
 * no note, no occupation, no photograph, no structured data. Their page, where
 * this archive has one for the person, is noindex, which takes it out of the
 * sitemap and the search index. THE REASON THIS IS SAFE TO LEAVE TO THE PAGES
 * IS THAT THE DATA ALREADY HOLDS NOTHING ELSE: tools/build_site_data.py builds a
 * living person out of those four things and never reads the rest, so a page
 * that forgets to hide a field has nothing to show.
 *
 * What a page still has to decide for itself is what it SAYS about somebody
 * who is alive — "born", "died" and "buried" are not words for them — and that
 * is what `lifeLine()` and `isLiving()` are for.
 *
 * `publishable()` and `nameIfPublishable()` keep their names because pages and
 * tools/check_living_rule.py are built around them. They now mean "may be
 * named": everybody. What they no longer do is pretend that a living person
 * has no name.
 */
export const livingPolicy = living.policy || "named-place";

/** Every member of a family the archive may draw as a person — the living by name. */
export const publishable = (members) =>
  (members || []).filter((m) => m && m.name);

/** A name to print for somebody, living or not. */
export const nameIfPublishable = (person) =>
  person && person.name && person.name !== "\u2014" ? person.name : null;

export const isLiving = (person) => !!(person && person.living);

/** How many are living. Counting is not publishing and has its own door. */
export const countLiving = (rows) => (rows || []).filter((r) => r && r.living).length;

/** What to print where a dead person's years go. A living person has none, and
 *  the town and country stand in their place; nothing else ever does. */
export const lifeLine = (person) =>
  !person ? "" : person.living ? (person.place || "") : (person.life || "");

/** The six named on purpose, and nobody else. They are named in PROSE, as the
 *  authors of a eulogy and as the reason this archive exists, each with the
 *  owner's recorded confirmation in living.json. That is a different thing from
 *  being listed as a relative, and it is unchanged. */
const NAMED = new Set((living.named || []).map((n) => n.phrase));
export const isNamedOnPurpose = (name) => NAMED.has(name);
export const publishableOrNamed = (rows) => (rows || []).filter((r) => r && r.name);


/* The GEDCOM export HTML-escapes a place written with angle brackets, so the
   data holds "&lt;Ehrstaedt, ...&gt;". Astro escapes the ampersand again and
   the page printed "&lt;Ehrstaedt" as visible text (3 pages). The atlas tools
   already read it as "Ehrstaedt" (html.unescape, then drop the brackets);
   this does the same for display. The data files are left as they are. */
const ENT = { "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&amp;": "&" };
export const cleanPlace = (s) =>
  typeof s === "string"
    ? s.replace(/&(?:lt|gt|quot|#39|amp);/g, (m) => ENT[m]).replace(/[<>]/g, "").replace(/\s+/g, " ").trim()
    : s;
const cleanPlaces = (rec) => {
  const out = {};
  for (const k of ["bornPlace", "diedPlace"]) if (rec[k]) out[k] = cleanPlace(rec[k]);
  return out;
};

/* One person = one GEDCOM record. The tree is the authority on identity here;
   this archive's job is to say how well each record is evidenced, not to merge
   or split people behind the reader's back. */
function build() {
  const byId = new Map();

  const add = (rec, extra = {}) => {
    if (!rec) return;
    const prev = byId.get(rec.id);
    byId.set(rec.id, { ...(prev || {}), ...rec, ...extra, ...cleanPlaces(rec) });
  };

  for (const a of ancestors) add(a, { ancestor: true });
  for (const f of families) for (const m of f.members) add(m, { family: f.surname });

  const people = [...byId.values()];

  // slugs, disambiguated when a name repeats — and names repeat constantly:
  // there are two George Pitt D'Arcys and three Conyers.
  //
  // THE DEAD ARE SLUGGED FIRST, AND AMONG THEMSELVES, so that admitting the
  // living on 16 October changed no address that had been published. A dead
  // person's slug depended on whether anybody else carried the name; had the
  // living been counted in, a dead John Smith whose name a living John Smith
  // shares would have moved from /people/john-smith/ to /people/john-smith-1850/
  // and every link to him, in this archive and outside it, would have broken.
  // The living are slugged afterwards, from what is left. tools/build_register.py
  // and tools/build_family_pages.py reproduce this for the dead only.
  const dead = people.filter((p) => !p.living);
  const alive = people.filter((p) => p.living);
  const counts = {};
  for (const p of dead) counts[kebab(p.name)] = (counts[kebab(p.name)] || 0) + 1;
  const used = new Set();
  for (const p of dead) {
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
  /* A living person has no year to tell them from a namesake, so a name that
     is taken — by the dead or by another living person — is told apart by
     the word "living", then a number. Two living people of one name are not
     merged, for the reason the dead are not. */
  for (const p of alive) {
    const base = kebab(p.name) || "unnamed";
    let slug = base;
    if (used.has(slug)) slug = `${base}-living`;
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

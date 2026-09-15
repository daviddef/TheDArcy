/* The thirteen families, grouped by the generation at which each enters the
   direct line. The ahnentafel number is read from ancestors.json, which owns
   it: a person who is both a numbered ancestor and a family member loses the
   number through lib/people.js, because families.json carries ahn: null. */
import families from "../data/families.json";
import ancestors from "../data/ancestors.json";
const ANC = new Map(ancestors.filter((a) => a.ahn).map((a) => [a.id, a]));
const LABEL = { 1:"The name the archive carries", 2:"Her parents", 3:"Her grandparents",
  4:"Her great-grandparents", 5:"Her great-great-grandparents" };
const entersAt = (f) => {
  const g = f.members.map((m) => ANC.get(m.id)).filter(Boolean).map((a) => a.gen);
  return g.length ? Math.min(...g) : null;
};
const FAMS = families.map((f) => ({ ...f, at: entersAt(f) }));
const gens = [...new Set(FAMS.filter((f) => f.at).map((f) => f.at))].sort((a, b) => a - b);
export const chartGroups = [
  ...gens.map((g) => ({ key: "g" + g, label: LABEL[g] || `${g - 1} generations back`,
    families: FAMS.filter((f) => f.at === g)
      .map((f) => ({ surname: f.surname, n: f.published })) })),
  ...(FAMS.some((f) => !f.at) ? [{ key: "off", label: "In the archive, not on the direct line",
    families: FAMS.filter((f) => !f.at).map((f) => ({ surname: f.surname, n: f.published })) }] : []),
];

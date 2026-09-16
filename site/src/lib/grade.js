/* How sure is this archive about a given person?
 *
 * Not a judgement invented here: it is read off what the archive has already
 * established and written down elsewhere.
 *
 *   documented  provenance.json names at least one record that proves a
 *               relationship for them — a Queensland registration, a baptism,
 *               a NAA passenger record, a sworn deposition
 *   disputed    they hang off one of the two grafts. /how-far-back puts it
 *               exactly: "71 hang on a single unevidenced link in the D'Arcy
 *               line and 27 on a single disproved link in the Sneyd line"
 *   family      on the family tree, with nothing found for them either way.
 *               Most of the archive is here, and saying so is the point.
 */
import prov from "../data/provenance.json";
import personRecords from "../data/person-records.json";

/* The ladder above grades RELATIONSHIPS, because that is what provenance.json
   holds. It said more than it knew: a person with no relationship edge got
   "No record has been found for them", and on 17 September 2026 that sentence
   was being printed on the pages of thirty people for whom this archive had
   read a hundred and thirty records — six London Gazette commissions on one of
   them. The level is unchanged, because the level is about relationships and
   a name-matched record does not prove a parent. The SENTENCE is fixed,
   because it was false. */
const recsFor = (slug) => (personRecords[slug]?.rows || []).length;

const GRAFT = {
  Hornby: { level: "disputed", label: "Hornby graft",
            why: "Reached only through a single unevidenced link. The archive searched for it and found nothing; a legitimate male descent is excluded by the peerage record.",
            href: "/hornby" },
  Keele:  { level: "disputed", label: "Keele graft — disproved",
            why: "Reached only through a link that has been looked for in the right registers and found to be wrong.",
            href: "/how-far-back" },
};

export function grade(slug) {
  const me = prov[slug];
  const nRec = recsFor(slug);
  const read = nRec
    ? ` ${nRec} record${nRec === 1 ? " that names" : "s that name"} them ${nRec === 1 ? "has" : "have"} been read, set out on this page.`
    : "";
  if (!me) return { level: "family", label: null, cites: [], nRec,
    why: "Not in the provenance index — carried by the family tree alone." + read, href: null };

  const cites = Object.values(me.rel || {}).flat();
  if (cites.length) {
    return {
      level: "documented", label: null, cites, nRec,
      why: `Proved by ${cites.length} record${cites.length === 1 ? "" : "s"}.` + read,
      href: null,
    };
  }
  if (me.graft && GRAFT[me.graft]) return { ...GRAFT[me.graft], cites: [], nRec,
    why: GRAFT[me.graft].why + read };
  return {
    level: "family", label: null, cites: [], nRec,
    why: nRec
      ? "No record yet ties them to their parents or their children, so the relationships above are the family tree's."
        + read
      : "Asserted by the family tree. No record has been found for them, and none has been shown against them either.",
    href: null,
  };
}

/* Counts for the pages that want to state the shape of it. */
export function tally(slugs) {
  const out = { documented: 0, disputed: 0, family: 0 };
  for (const s of slugs) out[grade(s).level] += 1;
  return out;
}

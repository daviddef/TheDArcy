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
  if (!me) return { level: "family", label: null, why: "Not in the provenance index — carried by the family tree alone.", href: null };

  const cites = Object.values(me.rel || {}).flat();
  if (cites.length) {
    return {
      level: "documented", label: null, cites,
      why: `Proved by ${cites.length} record${cites.length === 1 ? "" : "s"}.`,
      href: null,
    };
  }
  if (me.graft && GRAFT[me.graft]) return { ...GRAFT[me.graft], cites: [] };
  return {
    level: "family", label: null, cites: [],
    why: "Asserted by the family tree. No record has been found for them, and none has been shown against them either.",
    href: null,
  };
}

/* Counts for the pages that want to state the shape of it. */
export function tally(slugs) {
  const out = { documented: 0, disputed: 0, family: 0 };
  for (const s of slugs) out[grade(s).level] += 1;
  return out;
}

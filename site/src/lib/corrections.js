/* Where research has overturned the exported tree, the person page shows the
   archive's finding and prints the tree's version underneath — the same rule
   /direct-line follows. Correcting silently would hide the one thing this site
   exists to show, and leaving the tree's value alone would make a person page
   contradict the narrative page about the same person. */
export const CORRECTIONS = {
  "william-hartley-sneyd": {
    born: ["30 September 1837", "the tree says 1838. His Queensland death registration 1902/B/2776 records the date of birth outright, and this archive briefly published 1838 against it and was wrong", "/inquest-1902"],
    occupation: ["Fount-room Overseer, Queensland Government Printing Office — a contractor later", "the tree records no trade at all. The Blue Books have him in the Government Printing Office on £225, in the public service from 1 February 1862 and last listed in 1890", "/sergeant-sneyd"],
  },
  "vivian-ernest-william-sneyd": {
    born: ["about October 1890", "the tree says between 1890 and 1892. He gave his age as 25 years 2 months on 4 December 1915", "/great-war"],
    died: ["16 February 1920", "the tree says between 1919 and 1921. Queensland death registration 1920/B/31382", "/great-war"],
  },
  "vivian-claude-sneyd": {
    bornPlace: ["Windsor, Brisbane", "the tree says Rockhampton. His own Service and Casualty Form gives Windsor, Brisbane", "/great-war"],
  },
  "george-pitt-d-arcy-1783": {
    born: ["1780 or 1783 — unresolved", "the tree says 18 February 1783. Every one of the six 1849 death notices gives his age as 69, which puts his birth about 1780. The archive has no register for either and publishes the conflict rather than choosing", "/australia"],
    bornPlace: ["unknown — Portsmouth or the West Indies", "the tree offers both, joined by \u201cor\u201d, which is the tree admitting it does not know", "/australia"],
    burial: ["Parramatta, New South Wales — the exact ground is not established", "the tree says only \u201cAustralia\u201d", "/australia"],
  },
  "samuel-charles-sneyd-1810": {
    occupation: ["Soldier of the 4th (King's Own); sergeant of the NSW Mounted Police; chief constable at Moreton Bay; Governor of Brisbane Gaol", "the tree records no trade at all for a man with four careers", "/sergeant-sneyd"],
  },
  "arthur-hartley-sneyd": {
    occupation: ["Typist", "the tree says Clerk. His own attestation paper of 16 September 1915 says typist", "/great-war"],
    burial: ["No known grave — commemorated at Villers-Bretonneux", "the tree says \u201cFrance\u201d. The Army Form B.2090A gives his burial place as \u201cNot yet to hand\u201d, and it never came to hand", "/finding-arthur"],
    diedPlace: ["\u201cIn the field, France\u201d — and a sergeant of the 10th Battalion reported Mouquet Farm", "the tree says Pozi\u00e8res. The army's own report of death says only \u201cin the field\u201d, and the only witness to a burial named Mouquet Farm on the 22nd, not Pozi\u00e8res on the 20th", "/finding-arthur"],
  },
  "james-wakefield": {
    born: ["1806 \u2014 baptised at Stroud on 6 April", "the tree says 1799 and cites nothing for it. Every record this archive holds on him points the other way: the baptism, aged 35 in the 1841 census, 45 in 1851 and 48 on the 1854 passenger register. A birth in 1799 would make him 42, 52 and 55", "/wakefields"],
    bornPlace: ["Stroud, Gloucestershire", "the tree says only \u201cGloucestershire, England\u201d. The 1851 census gives his birthplace as Stroud, and a baptism there on 6 April 1806 names a father Richard \u2014 the name his Queensland death registration gives for his father", "/wakefields"],
  },
  "robert-d-arcy": {
    born: ["by 1758, and probably earlier", "the tree says 1751 in North Yorkshire. The 1751 is arithmetic from an age on a burial register, not a birth record, and nothing places him in Yorkshire", "/hornby"],
  },
};

/* A corrected birth or death year has to travel with the person wherever they
   are drawn. A pedigree card that still prints the tree's year, two clicks from
   the page that overturned it, is the archive contradicting itself. */
const yr = (v) => (String(v || "").match(/\d{4}/) || [""])[0];

/* The chart must read THIS map and not the tree's raw year. On 16 October 2026
   /tree drew William Hartley Sneyd as 1838\u20131902 while his own page said
   1837\u20131902, because the kit's ahnen() builds a box from the tree row and
   knew nothing of what this file overturns. The comment above says what that
   is: the archive contradicting itself two clicks from the page that
   overturned it. ahnen() takes a reader per field, so the chart passes these. */
export const yearOf = (slug, field, fallback) => {
  const c = CORRECTIONS[slug] && CORRECTIONS[slug][field];
  return (c && yr(c[0])) || yr(fallback);
};

/* Where the archive knows the NAMES of a person's parents from a record but the
   family tree does not hold them, so there is no box to draw. The kit's wall
   text for such a person reads «No parents are recorded in this archive», which
   is false: they are recorded, as record lines, and a record line is not an
   edge. This says what is actually known and where the chart has to stop. */
export const NAMED_ABOVE = {
  "james-wakefield": {
    label: "Stroud 1806 \u00b7 parents named",
    note: "**Richard Wakefield** and **Elizabeth Webb** are named as **James Wakefield**\u2019s parents in a baptism at Stroud on 6 April 1806, from an index entry and not the register itself; his Queensland death registration 1857/B/135 independently names the father as Richard. They are held here as record lines only \u2014 the family tree has neither, so there is no box to draw. Nothing above them has been established: one Richard Wakefield turns up in the free Gloucestershire transcripts, baptised at Chedworth in 1770, and nothing connects him to this family but a name.",
  },
};

export function lifeOf(o) {
  const c = CORRECTIONS[o.slug];
  if (!c) return o.life || "";
  const [lb, ld] = String(o.life || "").split("\u2013");
  const b = yr(c.born ? c.born[0] : o.born) || yr(lb);
  const d = yr(c.died ? c.died[0] : o.died) || yr(ld);
  if (!b && !d) return o.life || "";
  return `${b || "?"}\u2013${d || ""}`.replace(/\u2013$/, "");
}

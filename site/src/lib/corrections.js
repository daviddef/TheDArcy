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
  "robert-d-arcy": {
    born: ["by 1758, and probably earlier", "the tree says 1751 in North Yorkshire. The 1751 is arithmetic from an age on a burial register, not a birth record, and nothing places him in Yorkshire", "/hornby"],
  },
};

/* A corrected birth or death year has to travel with the person wherever they
   are drawn. A pedigree card that still prints the tree's year, two clicks from
   the page that overturned it, is the archive contradicting itself. */
const yr = (v) => (String(v || "").match(/\d{4}/) || [""])[0];

export function lifeOf(o) {
  const c = CORRECTIONS[o.slug];
  if (!c) return o.life || "";
  const [lb, ld] = String(o.life || "").split("\u2013");
  const b = yr(c.born ? c.born[0] : o.born) || yr(lb);
  const d = yr(c.died ? c.died[0] : o.died) || yr(ld);
  if (!b && !d) return o.life || "";
  return `${b || "?"}\u2013${d || ""}`.replace(/\u2013$/, "");
}

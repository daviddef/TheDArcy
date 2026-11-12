/* THE RESEARCH MENU: one list, read by the header menu (layouts/Base.astro), the drawer, the hub page /research/ and the two group
   pages. 12 November 2026 (the research-menu trial, wave 4, after the Defranceski and Lerena archives): "Evidence" and
   "Investigations" became one "Research" menu with three groups. Nothing is renamed or removed: every item keeps the address it had,
   and the labels of the eight pages the estate's Evidence canon names (kit data/evidence-menu.json) are unchanged. `asks` is the
   canon's question for those pages. The five pages that were Investigations (the papers, the 1902 inquest, the search for Arthur,
   Behind the Paywall, Reading the Archive Against Itself) are deep dives under Sources; What the Indexes Hold, which says which
   indexes were searched and what each holds, sits beside Sources. */
export const RESEARCH = [
  { id: "to-do", head: "To do", href: "/research/to-do/",
    dek: "What is not known yet, what has been asked of other people, and what is being worked on.",
    items: [
      { href: "/open-questions/", label: "Open Questions", asks: "What is not known, and what would settle it?" },
      { href: "/errands/", label: "Errands", asks: "What has been asked of other people, or needs someone standing in a place?" },
      { href: "/worklist/", label: "The work list", asks: "What is being done, by whom, since when?" },
    ] },
  { id: "whats-new", head: "What's new", href: "/whats-new/",
    dek: "What was read, found and taken back lately, newest first, and the same record in full.",
    items: [
      { href: "/searched/", label: "What Has Been Read", asks: "What was looked at, and what did it not turn up?", atlas: true },
      { href: "/corrections/", label: "Corrections", asks: "What did this archive get wrong?" },
      { href: "/changes/", label: "What changed", asks: "What happened, most recent first?" },
    ] },
  { id: "sources-and-method", head: "Sources & method", href: "/research/sources-and-method/",
    dek: "What this archive stands on, how it reads a record, and the long studies that sit beside them.",
    items: [
      { href: "/sources/", label: "Sources", asks: "What does this stand on, and where do I check?" },
      { href: "/method/", label: "Method", asks: "What would make you believe or not believe this?" },
      { href: "/gallery/", label: "Gallery", asks: "What has been photographed?" },
      { href: "/documents/", label: "Documents", asks: "What is reproduced whole?" },
      { href: "/coverage/", label: "What the Indexes Hold", atlas: true },
      { sub: "Deep dives", id: "deep-dives",
        note: "Long studies, each of one set of papers, one inquest, one search or one way of reading. They are linked from the Sources page too.",
        items: [
          { href: "/papers/", label: "The Papers" },
          { href: "/inquest-1902/", label: "The Inquest, 1902" },
          { href: "/finding-arthur/", label: "The Search for Arthur" },
          { href: "/behind-the-paywall/", label: "Behind the Paywall" },
          { href: "/crossread/", label: "Reading the Archive Against Itself" },
          { href: "/dna/", label: "The DNA" },   /* 12 Nov 2026 (menu regroup): left Start; the page reads this family's DNA tests */
        ] },
    ] },
];
/* the header menu's shape: [group, ...] with { head, href, items: [[href, label] | { sub }] } */
export const navGroups = RESEARCH.map((g) => ({
  head: g.head, href: g.href,
  items: g.items.flatMap((x) => x.sub ? [{ sub: x.sub }, ...x.items.map((y) => [y.href, y.label])] : [[x.href, x.label]]),
}));

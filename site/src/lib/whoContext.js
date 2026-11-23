/* Which record a /who/ line came out of, in words a reader can act on: a link to the page of this archive that reads that kind of record.
   Moved here from pages/who/[slug].astro (23 November 2026) so a person page that sets the same lines out draws the same link: the output of
   /who/[slug].astro is unchanged. */
export const WHERE = [
  [/QSA coronial/, "The inquest, 1902", "/inquest-1902"],
  [/QSA /, "Queensland State Archives", "/sources"],
  [/AWM 1DRL/, "The search for Arthur", "/finding-arthur"],
  [/AWM 28/, "The Great War", "/great-war"],
  [/NAA B2455|NAA J34/, "The Great War", "/great-war"],
  [/ADM 101/, "Arrival, 1826", "/australia"],
  [/FreeREG/, "Berkeley, Gloucestershire", "/berkeley"],
  [/Blue Book/, "Sergeant Sneyd", "/sergeant-sneyd"],
  [/Trove/, "What the papers said", "/papers"],
  [/Queensland death index/, "The register", "/register"],
  [/Connolly|PROB/, "The Hornby claim", "/hornby"],
];
export const context = (src) => WHERE.find(([re]) => re.test(src));

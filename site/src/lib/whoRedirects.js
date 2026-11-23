/* THE /who/ NAMES THAT ARE REDIRECTS (23 November 2026). Six /who/<slug>/ dossiers (tools/who-fold-rulings.json, key "redirect") are no longer pages: every line of
   each is set out on the one person page that bears the name, so the address is a static redirect (astro.config.mjs) and every link to it goes to the person.
   The list is site/src/data/who-fold.json "redirects" (who slug -> person slug), made by tools/build_who_fold.py, which refuses a name that is not folded in full. */
import whoFold from "../data/who-fold.json";

export const REDIRECTS = whoFold.redirects || {};

/** Is /who/<slug>/ a redirect rather than a page? */
export const isRedirected = (slug) => Object.prototype.hasOwnProperty.call(REDIRECTS, slug);

/** The address of a name: the person's page where the /who/ page is a redirect, the /who/ page otherwise (no base; wrap in u()). */
export const whoPath = (slug) => (isRedirected(slug) ? `/people/${REDIRECTS[slug]}/` : `/who/${slug}/`);

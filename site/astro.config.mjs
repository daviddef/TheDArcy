import { defineConfig } from 'astro/config';

// GitHub Pages project site. To serve from a custom domain later,
// set base to '/' and site to that domain.
/* Phase 1 of the seven-archive standardisation: five archives call this page
   /corrections, this one called it /what-we-got-wrong. Renamed; the old
   address redirects, because it has been linked to from other archives. */
const BASE = '/TheDArcy';
const redirects = { '/what-we-got-wrong': `${BASE}/corrections/` };

export default defineConfig({
  site: 'https://daviddef.github.io',
  base: '/TheDArcy',
  build: { format: 'directory' },
  redirects,
});

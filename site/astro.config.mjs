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
  /* WHY outDir IS A VARIABLE, and why the default must stay 'dist'.
     Several sessions build this estate at once, and `astro build` EMPTIES its
     outDir before it refills it — so one session's build wipes the tree
     another session's gates are reading, and the gates report a torrent of
     absences that are simply not copied yet. The kit's tools all honour
     ARCHIVE_OUT and, when they refuse a shared build, print «build to a
     directory of your own: ARCHIVE_OUT=...» as the way out. WITHOUT THIS LINE
     THAT HATCH CANNOT BE TAKEN: the variable redirected every reader and
     nothing that writes. Found 27 September 2026, after the kit had been
     printing that advice for four days.
     THE DEFAULT MUST STAY 'dist' — .github/workflows uploads `path: site/dist`,
     so changing it here would publish nothing. */
  outDir: process.env.ARCHIVE_OUT || 'dist',

  build: { format: 'directory' },
  redirects,
});

import { defineConfig } from 'astro/config';

// Custom domain, served by GitHub Pages from the TheDArcy repo.
// MOVED 12 October 2026 from https://daviddef.github.io/TheDArcy/. The apex
// defranceski.com is a Pages site in its own right, served by its own repo,
// and project sites do NOT inherit it — defranceski.com/TheDArcy/ returns 404
// — so a subdomain was the only clean route rather than a preference.
// site/public/CNAME CARRIES THE HOSTNAME AND MUST STAY THERE. This repo
// deploys by Actions uploading site/dist; GitHub writes a CNAME of its own
// when the domain is set in the UI, but any later Actions deploy that does
// not carry one DETACHES the custom domain. In public/ it is part of every
// build and cannot go missing.
/* Phase 1 of the seven-archive standardisation: five archives call this page
   /corrections, this one called it /what-we-got-wrong. Renamed; the old
   address redirects, because it has been linked to from other archives. */
// Empty, not '/', so the redirect target below reads '/corrections/' and not
// '//corrections/'. The same empty string is what kit/data/archives.json
// carries for this archive, because every kit consumer derives the base as
// (import.meta.env.BASE_URL || '/').replace(/\/$/, '') — which is '' here.
const BASE = '';
const redirects = { '/what-we-got-wrong': `${BASE}/corrections/` };

export default defineConfig({
  site: 'https://darcy.defranceski.com',
  base: '/',
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

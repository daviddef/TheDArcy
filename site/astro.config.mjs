import { defineConfig } from 'astro/config';

// GitHub Pages project site. To serve from a custom domain later,
// set base to '/' and site to that domain.
export default defineConfig({
  site: 'https://daviddef.github.io',
  base: '/TheDArcy',
  build: { format: 'directory' },
});

// Prefix a site-root path with the deployment base, so the same links work at
// https://archive.defranceski.com/ and at https://defranceski.com/.
//
// ALSO gives a page address its trailing slash. Pages here are built as
// /x/index.html, so /x only works because the host redirects it to /x/; the
// 16 October 2026 audit counted 11,200 internal links that leaned on that
// redirect (a round trip each, and a different address from the canonical
// one). Nearly all of them come through this function, from hrefs held in the
// data files without the slash, so it is added here once. A path whose last
// segment has a file extension (/styles.css, /trove-titles.json) is a file,
// not a page, and is left alone; so are a query and a #fragment, which stay
// after the slash.
const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const page = (p) => {
  const m = /^([^?#]*)(.*)$/.exec(p);
  const path = m[1];
  if (path === "" || path.endsWith("/") || /\.[A-Za-z0-9]{1,8}$/.test(path.split("/").pop())) return p;
  return path + "/" + m[2];
};
export const u = (p = "/") => `${BASE}${page(p.startsWith("/") ? p : "/" + p)}`;

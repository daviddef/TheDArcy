/* This archive's light markup: the kit's md()/mdp() PLUS markdown links.

   The kit's md() renders **bold**, *italic*, «quotes» and `code`, but not
   [text](/path) — only its mdNote() links, and that returns block HTML that
   cannot sit inside a <p>, a <td> or a <span>. So data written with links in
   it printed them as brackets on 19 pages (16 October 2026 audit), and two
   pages had each grown a private link() to cope. This is the one copy.

   Everything the kit escapes stays escaped; only the link markers become
   tags. Links inside a <code> span are left alone, because a code span that
   shows a link (`[text](/path)`) is demonstrating one. Hrefs: a site path
   (/x), a fragment (#x) or https://. Site paths go through u() so the base
   is applied, and are NOT given a trailing slash here: /x#q1 and /file.json
   are not folders. */
import { md as kitMd, mdp as kitMdp, plain as kitPlain } from "@daviddef/archive-kit/lib/md.js";
import { u } from "./url.js";

const LINK = /\[([^\]\n]+)\]\((\/[^)\s]*|#[^)\s]*|https:\/\/[^)\s]+)\)/g;

const linkify = (html) =>
  html
    .split(/(<code>[\s\S]*?<\/code>)/)
    .map((seg, i) =>
      i % 2
        ? seg
        : seg.replace(LINK, (_, t, h) =>
            h.startsWith("https://")
              ? `<a href="${h}" rel="noopener">${t}</a>`
              : `<a href="${h.startsWith("#") ? h : u(h)}">${t}</a>`),
    )
    .join("");

export const md = (x) => linkify(kitMd(x));
export const mdp = (x) => linkify(kitMdp(x));
/* The kit's plain() strips only site-path links; a link to a fragment or to
   another site printed its brackets in a meta line. */
export const plain = (x) =>
  kitPlain(String(x ?? "").replace(/\[([^\]\n]{1,120})\]\((?:#|https?:\/\/)[^)\s]{0,200}\)/g, "$1"));

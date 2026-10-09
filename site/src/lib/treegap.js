/* What a tree-derived surface omits, computed rather than claimed.
 *
 * 9 October 2026. /marriages, /graves and /households are all built from
 * marriages.json, graves.json and households.json, which build_family_pages.py
 * derives from the GEDCOM. So each of them shows what THE TREE holds, and none
 * of them showed what this archive has documented from records and the tree
 * does not carry. /marriages went further and claimed to show "every marriage
 * this archive can date", which was false by 34 — one of them Hannah Saniger's
 * own marriage, the founding marriage of the English line.
 *
 * The difference is small enough to show and too important to leave out:
 * Hannah's father's burial at Berkeley in 1825, Robert West D'Arcy's marriage
 * at Bombay, the 1852 marriage of James Sanigar. So every one of those pages
 * computes its own difference at build time and prints it. It cannot go stale:
 * document something and it appears there until the tree catches up.
 *
 * This lives here rather than three times over, because three copies of one
 * rule drift, and a surface quietly showing a different difference from its
 * neighbour would be worse than the fault being fixed.
 */
import personRecords from "../data/person-records.json";
import dossiers from "../data/dossiers.json";

/** Record lines matching `test`, for people the surface never names.
 *  `onSurface` is a Set of names the page already shows. */
export function notOnSurface(onSurface, test) {
  const out = [];
  const seen = new Set();
  const take = (src, hrefBase, where) => {
    for (const [slug, v] of Object.entries(src || {})) {
      for (const r of v.rows || []) {
        const says = r.says || "";
        if (!test.test(says)) continue;
        if (onSurface.has(v.name)) continue;
        // One person can carry the same line under several slugs; the first
        // forty-four characters are enough to recognise a repeat without
        // collapsing two genuinely different records that open alike.
        const k = `${v.name}|${says.slice(0, 44)}`;
        if (seen.has(k)) continue;
        seen.add(k);
        out.push({ name: v.name, says, href: `${hrefBase}${slug}/`, where });
      }
    }
  };
  take(personRecords, "/people/", "in the tree");
  take(dossiers.people, "/who/", "named in a record");
  out.sort((a, b) => a.name.localeCompare(b.name));
  return out;
}

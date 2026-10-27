/* THE MINI FLAGS, PUT BACK ON THE RIBBON CARDS (kit 1fa6b54, 27 October 2026).

   The kit draws a card's `flags` (StoryRibbon, FamilyRibbon; kit/docs/ribbon-flags.md). They are made by the kit's generator
   through tools/build_ribbon_flags.py and kept in src/data/ribbon-flags.json, not on the cards, because the story's and the family
   ribbon's contracts at this kit refuse a card field they do not know. Each entry names its card by place, name and person; a card
   that is not the one the flags were made for stops the build, so a stale file can never put one card's flags on another. */
import flags from "../data/ribbon-flags.json";

function put(cards, entries, where) {
  if (!entries || !entries.length) return cards;
  const out = cards.map((c) => ({ ...c }));
  for (const e of entries) {
    const c = out[e.card];
    if (!c || c.name !== e.name || (c.person ?? null) !== (e.person ?? null)) {
      throw new Error(`ribbon-flags.json: ${where} card ${e.card} is not ${e.name} any more: run python3 tools/build_ribbon_flags.py`);
    }
    c.flags = e.flags;
  }
  return out;
}

/* the story book with its ribbon's cards flagged */
export function storyWithFlags(book) {
  return { ...book, ribbon: { ...book.ribbon, cards: put(book.ribbon.cards, flags.story, "story") } };
}

/* one family's ribbon with its cards flagged */
export function familyWithFlags(fam) {
  return fam ? { ...fam, cards: put(fam.cards || [], (flags.families || {})[fam.id], `family ${fam.id}`) } : fam;
}

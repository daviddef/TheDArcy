/* THE YEAR OF AN EVENT, FOR THE «AT THE TIME» NOTES (kit/docs/era-notes.md; 18 October 2026).

   The person page prints a date and a place beside each other in three spots: the Born row, the Died row and a marriage. The kit's eraAt()
   wants a place and a PLAIN year. This file turns the date the page prints into that year, and refuses it (null) when it should not stand:

   1. plainYear (the kit) gives a year only for «1860», «Mar 1860», «12 Mar 1860» or ISO, and only if the number agrees with the one passed in.
      This archive's tree writes «27 OCT 1406», «MAR 1600» and, for some marriages, «June 24 1497»; month-first is turned round here. «AFT 1268»,
      «BET 1799 AND 1801», «ABT 21 JUL 1776», «TO 1797», «1621/22», «buried 16 January 1825, aged 55» and the archive's own prose («1781 — baptised
      at Madeley») are not plain and give no year.
   2. BRITISH DATES BEFORE 1752. England, and the colonies and Ireland with it, began the year on 25 March until 1752 and was eleven days behind the
      Gregorian calendar, so a printed «10 FEB 1650» may mean the year the tree would call 1651, and a bare year may be either. The kit says plainly
      that it does not handle this (an archive that has such events must hand it null). A note is therefore drawn before 1752 ONLY where the year
      before and the year after the printed one lie in the SAME era as the printed year (a bound that falls within one year of it gives no note):
      read either way, the date then lies in one era, and the note is true. An era that carries margins already keeps the note five years from
      each bound (the kit's floor), so for it this changes nothing; it bites on an era without a margin. It is applied to every region alike, which is the cautious
      side: the German Protestant states, Denmark and Norway also changed calendar (in 1700), and a note is only ever lost near an era's bound.

   The page's rule c (never for a living, held-out or noindex person) stays the PAGE's; this file cannot know who is living. */
import { eraAt, plainYear, fold } from "@daviddef/archive-kit/lib/era.js";

const MONTH_FIRST = /^([A-Za-z]{3,9})\.?\s+(\d{1,2})\s+(\d{4})$/;   // «June 24 1497», «Nov 12 1807»
export const dayFirst = (d) => {
  const t = String(d == null ? "" : d).trim().replace(/\s+/g, " ");
  const m = MONTH_FIRST.exec(t);
  return m ? `${m[2]} ${m[1]} ${m[3]}` : t;
};
const yearOf = (d) => { const m = /(\d{4})$/.exec(d); return m ? Number(m[1]) : null; };

/* The first year the Gregorian calendar and the 1 January year were used in Great Britain, Ireland and the colonies. */
export const CALENDAR_YEAR = 1752;

/* The id of the snapshot's era that covers `year` for this place, whether or not a note may be drawn there (the margin rule is not asked). */
function eraIdAt(snapshot, place, year) {
  const region = snapshot && snapshot.places ? snapshot.places[fold(place)] : null;
  const eras = typeof region === "string" && snapshot.regions ? snapshot.regions[region] : null;
  if (!Array.isArray(eras)) return null;
  const hit = eras.filter((e) => e.from <= year && (e.to === null || year < e.to));
  return hit.length === 1 ? hit[0].id : null;
}

/* The note for a place and the date the page prints, or null. */
export function eraFor(snapshot, place, date) {
  if (!place || !date) return null;
  const d = dayFirst(date);
  const year = plainYear(d, yearOf(d));
  if (year === null) return null;
  const era = eraAt(snapshot, place, year);
  if (era === null) return null;
  if (year < CALENDAR_YEAR && (eraIdAt(snapshot, place, year - 1) !== era.id || eraIdAt(snapshot, place, year + 1) !== era.id)) return null;
  return era;
}

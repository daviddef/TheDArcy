/* Helpers for the linking standard's L3 on the narrative pages (18 October 2026).

   hasRecord(ref): true when src/data/records.json holds a record listed under that reference (a National Archives reference, a
   Trove locator), so a table cell can write <Rec act={ref}>{ref}</Rec> when it can and plain text when it cannot. Nothing here
   invents an address: the table says what exists.

   The EXEMPT reasons are the words of data-cite-exempt="..." (the standard's attribute; counted in the gate's EX column and
   ratcheted). A passage is exempt only when no public address exists to link to, or the passage says itself that the record has
   not been seen and is queued: never to hide a link that could be made. */
import { index, fold } from "@daviddef/archive-kit/lib/rec.js";
import records from "../data/records.json";

const ix = index(records);

export const hasRecord = (ref) => ix.byKey.has(fold(String(ref ?? "").replace(/\.$/, "")));

export const GLOS =
  "text only: a Gloucestershire Archives catalogue description; the document has not been seen and no public address for it is held";
export const FREEBMD =
  "text only: the GRO volume and page and the registrar's local register entry are quoted as FreeBMD's index prints them, and FreeBMD gives no address for a single entry";
export const QUEUED =
  "the record has not been seen: the passage itself says it is still to be ordered or queued, and no public address for it is held";

/* the reason for a catalogue row whose reference has no record in the table, or undefined */
export const glosReason = (ref) => (/^D\s?\d{3,4}\b/.test(String(ref)) && !hasRecord(ref) ? GLOS : undefined);

/* data-name-exempt for the blocks that read medieval and early-modern deeds and pedigrees (the Berkeley Castle muniments, Smyth's
   pedigree of about 1639, Cooke's articles): there the parties are named by a given name alone or by a name no deed ties to one
   man, so no full name exists to write and no single person exists to link. It hides the block's L2 and L5 hits in the gate's EX
   column, where they are ratcheted like every other exemption. */
export const DEED_PARTIES =
  "medieval and early-modern deed parties: named in the calendar or in the pedigree by a given name alone, or by a name no deed ties to one man, so there is no full name to write and no one person to link";

/* What is new here, and the archive in numbers: the kit computes it at build time from this archive's own logs (kit/docs/whats-new.md).
   This file is the only D'Arcy-specific part: which data is which, and the counts no log holds.
   The search log's rows call their date `when` (already the kit's first choice) and their outcomes yield/null/empty/blocked, all words the kit knows.
   There is no corrections.json: the corrections list is OWN in src/lib/errors.js (what /corrections/ prints), each with a long-form `when` and `what`. */
import { buildPulse } from "@daviddef/archive-kit/lib/pulse.js";
import searched from "../data/searched.json";
import worklist from "../data/worklist.json";
import sources from "../data/sources.json";
import { OWN } from "./errors.js";
import { nPeople } from "./people.js";

export const pulse = buildPulse({
  searched, corrections: OWN, worklist,
  counts: { people: nPeople, sources: sources.recordSets.length },
});

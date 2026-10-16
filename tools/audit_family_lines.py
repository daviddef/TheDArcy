#!/usr/bin/env python3
"""Which names does this archive carry, and which of them have a family page? (Report only; it never fails.)

Run it to see why the lines in site/src/data/family-lines.json are the lines they are, and to find the next
ones when the research grows. It reads the committed data only.

    python3 tools/audit_family_lines.py            # the top 30 names and the ranked list of core names with no page
    python3 tools/audit_family_lines.py 60         # more rows

THE RULE (also written in family-lines.json, and applied here as code):
  published people  the numbered ancestors, the thirteen clusters and the relatives named beside them, minus
                    declared copies (same-person.json). Counted by SURNAME FIELD as the tree writes it, cut
                    and lowercased as tools/familylines.py does; spellings are grouped only where
                    family-lines.json groups them.
  CORE              a direct-line ancestor carries the name, OR at least 8 published people carry it, OR the
                    archive's own research files (work list, search register, open questions, errands) treat
                    it as a family under investigation: a row naming someone with that surname, three or
                    more times in all.
  HAS A PAGE        it is one of the thirteen clusters, a line in family-lines.json, or listed in
                    pagesElsewhere. A name whose research belongs to another archive (`otherArchive`) is
                    reported and not offered.
  RANK              direct line first, then published people, then research rows, then direct-line ancestors.
  The twelve highest-ranked core names with no page are the lines.
"""
import os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import familylines as FL

CAP = 12
MIN_PUBLISHED = 8
MIN_RESEARCH = 3


def research_rows():
    rows = []
    for f in ("worklist.json", "searched.json", "questions.json", "errands.json"):
        d = FL._j(f, {}) or {}
        for r in d.get("rows", []):
            rows.append(json.dumps(r, ensure_ascii=False))
    return rows


def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 30
    cfg = FL.config()
    by, in_cluster = FL.published()
    cp = FL.copies()
    group_of = {}                      # key -> the key of the line it is grouped into
    for l in cfg["lines"]:
        for k in l["keys"]:
            group_of[k] = l["keys"][0]
    cluster_keys = {FL.surname_key(f["surname"]) for f in FL._j("families.json", [])}
    line_primary = {l["keys"][0]: l for l in cfg["lines"]}
    elsewhere = {k for k in (cfg.get("pagesElsewhere") or {}) if not k.startswith("_")}
    other = {k for k in (cfg.get("otherArchive") or {}).get("keys", [])}

    rows = research_rows()
    groups = collections.defaultdict(list)
    for pid, r in by.items():
        if pid in cp:
            continue
        k = FL.surname_key(r.get("surname"))
        l = FL.line_of(r, cfg["lines"])
        key = l["keys"][0] if l else group_of.get(k, k)
        if key:
            groups[key].append(r)

    table = []
    for key, ps in groups.items():
        dead = [p for p in ps if not p.get("living")]
        ys = [int(y) for p in dead for y in re.findall(r"\b(\d{4})\b", p.get("life") or "")]
        towns = collections.Counter((p.get("bornPlace") or "").split(",")[0].strip() for p in dead if p.get("bornPlace"))
        word = key.split()[-1].title()
        pat = re.compile(r"\b[A-Z][a-z]+ (?:[A-Z][a-z]+ )?%s\b" % re.escape(word))
        res = sum(1 for r in rows if pat.search(r))
        page = ("cluster" if key in cluster_keys else "line" if key in line_primary
                else "elsewhere" if key in elsewhere else "")
        dl = sum(1 for p in ps if p.get("ahn"))
        core = dl > 0 or len(ps) >= MIN_PUBLISHED or res >= MIN_RESEARCH
        table.append(dict(key=key, n=len(ps), dead=len(dead), living=len(ps) - len(dead), dl=dl, res=res,
                          span=(min(ys), max(ys)) if ys else None,
                          towns=[t for t, _ in towns.most_common(2) if t], page=page,
                          other=key in other, core=core))
    table.sort(key=lambda r: (-(r["dl"] > 0), -r["n"], -r["res"], -r["dl"]))

    print("%-16s %4s %4s %4s %3s %4s  %-11s %-10s %s" % ("name", "pub", "dead", "live", "dl", "res", "years", "page", "born at"))
    for r in table[:top]:
        print("%-16s %4d %4d %4d %3d %4d  %-11s %-10s %s%s" % (
            r["key"][:16], r["n"], r["dead"], r["living"], r["dl"], r["res"],
            "%s-%s" % r["span"] if r["span"] else "", r["page"] or "NONE", ", ".join(r["towns"]),
            "   (other archive)" if r["other"] else ""))
    print()
    cand = [r for r in table if r["core"] and r["page"] in ("", "line") and not r["other"]]
    print("core names that have no page of their own apart from a line (the first %d are the lines):" % CAP)
    for i, r in enumerate(cand[:CAP + 8], 1):
        made = r["key"] in line_primary
        print("  %2d  %-16s pub %3d  direct line %2d  research rows %2d   %s" % (
            i, r["key"][:16], r["n"], r["dl"], r["res"],
            "line" if made else ("not created (beyond the cap)" if i > CAP else "SHOULD BE A LINE and is not in family-lines.json")))
    print()
    print("not offered (another archive's families):", ", ".join(sorted(k for k in other)) or "none")
    nolines = [r for r in cand[:CAP] if r["key"] not in line_primary]
    return 1 if nolines and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())

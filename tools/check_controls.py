#!/usr/bin/env python3
"""A null must name the test that could have disproved it.

/method promises that every null on this site carries its control. Nothing
enforced it, and on 15 September 2026 an audit found most null and empty rows
naming none. That is exactly how a written convention drifts: the rule lived in
prose and no build refused when it slipped.

So this refuses — for NEW rows only.

WHY IT IS A FIELD AND NOT A REGEX
---------------------------------
The first version of this gate read the prose and guessed. It was wrong in both
directions: it missed "John Smith across the WHOLE OF CHESHIRE returns TWO
entries" because the count was a word rather than a digit, and it accepted
"1841 entries" because a year is also a number. Tuning the pattern further was
tuning a machine to approximate an editorial judgement, which it cannot do.

So `ctl` is a FIELD on the row — "named" or "unstated" — and the regex survives
only as the bootstrap that set it once. The author says whether a control was
stated. The gate checks that they said.

The bias is deliberate. A row the pattern could not read as controlled was
marked `unstated`, even where a reader would call it controlled. Being called
untested when you are not is the harmless direction; the reverse is not.

  python3 tools/check_controls.py            # gate
  python3 tools/check_controls.py --list     # show the grandfathered rows
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCHED = os.path.join(HERE, "..", "site", "src", "data", "searched.json")
BASELINE = os.path.join(HERE, "controls-grandfathered.json")
VALID = {"named", "unstated"}


def key(r):
    """Identify a row by source and date, not by position."""
    return f"{r.get('src','')}||{r.get('when','')}"


COVERAGE = os.path.join(HERE, "..", "site", "src", "data", "coverage.json")


def check_verdicts():
    """A coverage verdict outside the declared vocabulary renders as its opposite.

    /coverage used to render its verdict through a fallthrough chain: good,
    partial, absent, and everything else "cannot answer". So BLOCKED — a source
    nobody has asked, because it wants an account this archive will not make —
    displayed as a source that had been asked and could not answer. And one row
    carried the freehand verdict "unusable as a control", which fell through the
    same way. Both were found on 15 September 2026 by reading the template.
    """
    j = json.load(open(COVERAGE, encoding="utf-8"))
    vocab = j.get("verdicts") or {}
    if not vocab:
        return ["coverage.json declares no `verdicts` vocabulary to check against"]
    bad = []
    for r in j.get("rows", []):
        v = r.get("verdict")
        if v not in vocab:
            bad.append(f"coverage row {r.get('db','?')[:44]!r} has verdict {v!r} — "
                       f"not one of " + ", ".join(sorted(vocab)))
    return bad


SPELLING = re.compile(
    r"(in any spelling|any spelling|every spelling|all spellings"
    r"|under (?:eight|nine|ten|eleven|twelve|fifteen|\w+) spellings)", re.I)


def check_spelling_claims():
    """A null that claims "every spelling" must have been asked without a list.

    Written 21 September 2026, the day own error 40 was found. This archive had
    published "None, in any spelling" for Sanigers at Chew Magna, with a control
    that passed, and the parish register holds two of them — one of them under
    SINEGAR, which was on the list. The same week, "Not found, in any spelling"
    stood for eight days over a marriage indexed SANIGRE.

    A list of spellings is a guess about a clerk and it cannot be complete: a
    single wildcard sweep of eleven years of one county turned up two forms this
    archive's own table did not hold. FindMyPast's surname box takes wildcards,
    so on that site the claim can be made without the guess — and where it can
    be, it must be. `S*N*G*R` at Chew Magna returns four records and two of them
    are the name.

    Scoped to FindMyPast because the claim is only checkable where wildcards
    exist. A full-text read of a printed book really is every spelling, and
    Rudder's index does not take an asterisk.
    """
    rows = json.load(open(SEARCHED, encoding="utf-8"))["rows"]
    bad = []
    for r in rows:
        if not r.get("src", "").startswith("FindMyPast"):
            continue
        if r.get("outcome") not in ("null", "empty"):
            continue
        hay = f"{r.get('src','')} {r.get('what','')} {r.get('got','')}"
        m = SPELLING.search(hay)
        if m and "*" not in hay:
            bad.append(f"{r.get('src','?')[:60]!r} ({r.get('when','?')}) claims "
                       f"{m.group(0)!r} and names no wildcard — a spelling list "
                       f"is a guess; ask it as S*N*G* and read what comes back")
    return bad


def main(argv):
    base = set()
    if os.path.exists(BASELINE):
        base = set(json.load(open(BASELINE, encoding="utf-8"))["grandfathered"])

    rows = json.load(open(SEARCHED, encoding="utf-8"))["rows"]
    bad, named, grand = [], 0, 0
    for r in rows:
        if r.get("outcome") not in ("null", "empty"):
            if "ctl" in r:
                bad.append((r, f"carries ctl={r['ctl']!r} but its outcome is "
                               f"{r.get('outcome')!r} — ctl belongs to nulls only"))
            continue
        c = r.get("ctl")
        if c not in VALID:
            bad.append((r, f"outcome {r.get('outcome')!r} and ctl={c!r} — "
                           f"must be one of " + ", ".join(sorted(VALID))))
        elif c == "named":
            named += 1
        elif key(r) in base:
            grand += 1
        else:
            bad.append((r, "ctl='unstated' and it is not grandfathered — "
                           "what test could have failed and did not?"))

    if "--list" in argv:
        for k in sorted(base):
            print("  grandfathered  " + k.split("||")[0][:90])
        return 0

    for r, why in bad:
        print(f"  FAIL  controls   {r.get('src','?')[:70]}")
        print(f"          {why}")
    vbad = check_verdicts()
    for m in vbad:
        print(f"  FAIL  verdicts   {m}")
    sbad = check_spelling_claims()
    for m in sbad:
        print(f"  FAIL  spellings  {m}")

    if bad or vbad or sbad:
        print(f"  FAIL  controls   {len(bad) + len(vbad) + len(sbad)} row(s) fail the control rule")
        return 1
    print(f"  ok    controls   {named} null(s) name a control, "
          f"{grand} grandfathered from before the rule")
    nv = len(json.load(open(COVERAGE, encoding="utf-8")).get("verdicts") or {})
    print(f"  ok    verdicts   every coverage row uses one of the {nv} declared verdicts")
    nfmp = sum(1 for r in json.load(open(SEARCHED, encoding="utf-8"))["rows"]
               if r.get("src", "").startswith("FindMyPast")
               and r.get("outcome") in ("null", "empty"))
    print(f"  ok    spellings  {nfmp} FindMyPast null(s) — none claims every "
          f"spelling without a wildcard")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

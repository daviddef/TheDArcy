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
import os, sys, json

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

    if bad or vbad:
        print(f"  FAIL  controls   {len(bad) + len(vbad)} row(s) fail the control rule")
        return 1
    print(f"  ok    controls   {named} null(s) name a control, "
          f"{grand} grandfathered from before the rule")
    nv = len(json.load(open(COVERAGE, encoding="utf-8")).get("verdicts") or {})
    print(f"  ok    verdicts   every coverage row uses one of the {nv} declared verdicts")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

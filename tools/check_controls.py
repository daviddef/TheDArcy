#!/usr/bin/env python3
"""A null must name the test that could have disproved it.

/method promises that every null on this site carries its control. Nothing
enforced it, and on 15 September 2026 an audit found 59 of 89 null and empty
rows naming none. That is exactly how a written convention drifts: the rule
lived in prose and no build refused when it slipped.

So this refuses — for NEW rows only.

The 59 that predate the rule are grandfathered by name in GRANDFATHERED below.
They are not wrong; they are untested, they are marked as such on the page, and
working them off is a separate job. What this stops is the sixtieth.

  python3 tools/check_controls.py            # gate
  python3 tools/check_controls.py --list     # show the grandfathered rows
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCHED = os.path.join(HERE, "..", "site", "src", "data", "searched.json")
BASELINE = os.path.join(HERE, "controls-grandfathered.json")

# A control is a test that COULD have failed. These are the ways this archive
# has actually written one — a named control search, a coverage statement with
# a number in it, a cap that was hit, a span that was measured.
CONTROL = re.compile(
    r"\bcontrol\b|\bcontrolled\b|\bcoverage checked\b|\bcap\b|\bcapped\b|"
    r"\breturns? \d|\bcomplete \d{4}|\bindexed\b|\btested\b|\bcould have failed\b|"
    r"\bmention count\b|\bagainst a .{0,24}control\b", re.I)


def rows():
    j = json.load(open(SEARCHED, encoding="utf-8"))
    return j["rows"]


def key(r):
    """Identify a row by source and date, not by position."""
    return f"{r.get('src','')}||{r.get('when','')}"


def main(argv):
    base = set()
    if os.path.exists(BASELINE):
        base = set(json.load(open(BASELINE, encoding="utf-8"))["grandfathered"])

    bad, ok_new, grand = [], 0, 0
    for r in rows():
        if r.get("outcome") not in ("null", "empty"):
            continue
        has = bool(CONTROL.search(r.get("got", "")))
        if has:
            ok_new += 1
            continue
        if key(r) in base:
            grand += 1
            continue
        bad.append(r)

    if "--list" in argv:
        for k in sorted(base):
            print("  grandfathered  " + k.split("||")[0][:90])
        return 0

    for r in bad:
        print(f"  FAIL  controls   {r.get('src','?')[:70]}")
        print(f"          outcome {r.get('outcome')!r} and no control named — "
              f"what test could have failed and did not?")
    if bad:
        print(f"  FAIL  controls   {len(bad)} new null(s) name no control")
        return 1
    print(f"  ok    controls   {ok_new} null(s) name a control, "
          f"{grand} grandfathered from before the rule")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

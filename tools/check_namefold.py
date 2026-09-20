#!/usr/bin/env python3
"""A refusal that nothing enforces will be overturned by the next session.

namefold-deny.json records spelling clusters this archive has READ and REFUSED
to fold, with the reason beside each. Its own opening note says why it exists:
"a refusal without one gets overturned by the next session that runs the tool
and sees a plausible-looking pair."

On 21 September 2026 check_published.py reported it as an ORPHAN — a data file
no page and no tool reads. So the refusals were written down and nothing on
earth consulted them. The next run of the kit's namefold.py would have offered
ZANIGAR → Sanigar again, and the next session would have had only the argument
this one had, not the answer it reached.

This is the reader. It refuses the build if a denied token has been folded
after all. It cannot stop the kit's tool OFFERING the fold — that tool belongs
to the shared kit and is not this archive's to change — but it can stop a fold
that was refused from reaching the search index unnoticed.

WHY THE STAKES ARE HIGHER THAN THEY LOOK
----------------------------------------
Folding is a SEARCH rule. A wrong fold breaks nothing: no page fails, no gate
trips, no reader sees an error. Somebody searching this site for a surname is
simply handed a record that has nothing to do with them, with no way to know
why. ZANIGAR is worse still — it is a nonsense string this archive invented as
a control test, and folding it would make the archive appear to hold it as an
attested spelling of the family name.

    python3 tools/check_namefold.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "src", "data")
FOLD = os.path.join(DATA, "namefold.json")
DENY = os.path.join(DATA, "namefold-deny.json")


def main():
    if not os.path.exists(DENY):
        print("  FAIL  namefold   namefold-deny.json is missing — "
              "the refusals have no home")
        return 1
    deny = json.load(open(DENY, encoding="utf-8"))
    never = [t.strip().lower() for t in deny.get("never", [])]
    why = {k.lower(): v for k, v in (deny.get("why") or {}).items()}

    if not never:
        print("  FAIL  namefold   namefold-deny.json lists nothing — "
              "a deny list with no entries cannot fail, so it is not a control")
        return 1

    missing = [t for t in never if t not in why]
    if missing:
        for t in missing:
            print(f"  FAIL  namefold   {t!r} is refused with no reason recorded — "
                  f"the next session will overturn it")
        return 1

    fold = {}
    if os.path.exists(FOLD):
        fold = {k.lower(): v for k, v in
                (json.load(open(FOLD, encoding="utf-8")).get("fold") or {}).items()}

    bad = []
    for t in never:
        if t in fold:
            bad.append(f"{t.upper()} was folded to {fold[t].upper()} and this "
                       f"archive refused that fold. Reason on file: "
                       f"{why[t][:120]}…")
        # a denied token must not be the TARGET of a fold either
        for k, v in fold.items():
            if v.lower() == t:
                bad.append(f"{k.upper()} was folded INTO {t.upper()}, which this "
                           f"archive refused as a canonical form.")

    for m in bad:
        print(f"  FAIL  namefold   {m}")
    if bad:
        return 1

    print(f"  ok    namefold   {len(never)} refused fold(s), each with its reason, "
          f"none of them in the {len(fold)}-token fold map")
    return 0


if __name__ == "__main__":
    sys.exit(main())

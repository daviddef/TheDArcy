#!/usr/bin/env python3
"""The handful of values in this archive that encode a DECISION, not a measurement.

Written 27 September 2026, out of own error 48. The kit pin moved inside a
commit about gating a chart, this archive built on top of it three times, and
then told a neighbouring session their reading of it was wrong. The build had
printed the right pin every run. It was not silent; it was unread.

That session's answer was to report the DELTA rather than the state: speak only
when the pin moves. The principle is right and the scope is the interesting
part. Most numbers in this build move every run for good reasons — pages,
records, badges — so a general delta report would cry wolf until it was turned
off, which is the failure mode of every noisy check ever written.

What does NOT move without somebody deciding it should is a much smaller set:
the kit this archive is pinned to, the rule it applies to living people, the
six people named on purpose, the two grafts it has rejected and how many hang
off them, and the pages exempt from the retired-reading gate. Each is an act of
judgement written down somewhere. A change to any of them without a
corresponding edit here is either a mistake or somebody else's commit passing
through.

So this REFUSES rather than reports. A decision changing is exactly the case
where a deliberate act should be required, and updating decisions.json in the
same commit is that act — one file, one line, and the move then also shows as a
diff in a file whose only subject is the decision.

Both empty cases are safe, because a check that can cry wolf gets turned off:
an undeclared key is refused rather than adopted silently, and a source that
cannot be read is reported as unreadable rather than guessed at.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "site", "src", "data")
DECISIONS = os.path.join(D, "decisions.json")


class Unreadable(Exception):
    """The source could not be read. NOT the same as a value that changed."""


def _json(name):
    try:
        with open(os.path.join(D, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise Unreadable(f"{name}: {e}")


def kit_pin():
    p = os.path.join(ROOT, "site", "package.json")
    try:
        txt = open(p, encoding="utf-8").read()
    except Exception as e:
        raise Unreadable(f"site/package.json: {e}")
    m = re.search(r"TheArchiveKit#([0-9a-f]{7,40})", txt)
    if not m:
        raise Unreadable("site/package.json: no TheArchiveKit pin found")
    return m.group(1)[:7]


def living_policy():
    # people.js reads `living.policy || "named-bare"`. The fallback is correct
    # today and that is exactly why it is watched: if the key ever appears with
    # a different value, or the fallback in people.js changes, nothing else here
    # would say so.
    return (_json("living.json").get("policy") or "named-bare")


def named_living():
    return sorted(n["phrase"] for n in _json("living.json").get("named", []))


def grafts():
    prov = _json("provenance.json")
    c = collections.Counter(v.get("graft") for v in prov.values() if v.get("graft"))
    return {k: c[k] for k in sorted(c)}


def retired_allow():
    return sorted(_json("retired.json").get("allow", []))


CHECKS = {
    "kitPin": kit_pin,
    "livingPolicy": living_policy,
    "namedLiving": named_living,
    "grafts": grafts,
    "retiredAllow": retired_allow,
}


def main():
    try:
        declared = json.load(open(DECISIONS, encoding="utf-8"))["decisions"]
    except Exception as e:
        print(f"  FAIL  decisions  cannot read {os.path.relpath(DECISIONS, ROOT)} — {e}")
        return 1

    moved, undeclared, unreadable = [], [], []
    for key, fn in CHECKS.items():
        try:
            now = fn()
        except Unreadable as e:
            unreadable.append((key, str(e)))
            continue
        if key not in declared:
            undeclared.append((key, now))
            continue
        was = declared[key].get("value")
        if was != now:
            moved.append((key, was, now, declared[key].get("why", "")))

    for key in declared:
        if key not in CHECKS:
            undeclared.append((key, "declared here and computed by nothing"))

    if not (moved or undeclared or unreadable):
        print(f"  ok    decisions  {len(CHECKS)} decision(s) unchanged since they were made")
        return 0

    for key, was, now, why in moved:
        print(f"  FAIL  decisions  {key} MOVED")
        print(f"          was  {json.dumps(was, ensure_ascii=False)}")
        print(f"          now  {json.dumps(now, ensure_ascii=False)}")
        if why:
            print(f"          the decision: {why}")
        print("          If that was deliberate, record it in site/src/data/decisions.json in")
        print("          the SAME commit. If it was not, look for a commit about something else")
        print("          that carried the file with it — that is how the kit pin moved unseen.")
    for key, what in undeclared:
        print(f"  FAIL  decisions  {key} is not declared — {json.dumps(what, ensure_ascii=False)[:90]}")
    for key, why in unreadable:
        print(f"  FAIL  decisions  {key} UNREADABLE — {why}")
        print("          Reported as unreadable rather than guessed at: a source that cannot be")
        print("          read is not a decision that has not moved.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

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


def living_exemptions():
    """EVERY phrase the living gate is told to let through, not just the six.

    check_living.py builds its allow-set from THREE lists in living.json —
    `named` (living people this archive decided to name), `namesakes` (not
    living people at all) and `allow` (bare strings). namedLiving above watches
    the first, because who this archive publishes is its own decision. This
    watches the union, because the union is the SURFACE: a phrase added to
    namesakes is exempted from the living rule just as effectively as one added
    to named, and nothing else here would say so.

    Found by a neighbouring session's account of Tersia Booyzen — a probe that
    read the declaration agreed with a gate that could not see her. The shape
    of that fault is a probe watching a narrower thing than the gate enforces.
    """
    l = _json("living.json")
    out = set(l.get("allow", []))
    for k in ("namesakes", "named"):
        out |= {e["phrase"] for e in l.get(k, []) if e.get("phrase")}
    return sorted(out)


CHECKS = {
    "kitPin": kit_pin,
    "livingPolicy": living_policy,
    "namedLiving": named_living,
    "livingExemptions": living_exemptions,
    "grafts": grafts,
    "retiredAllow": retired_allow,
}


def canon(v):
    """Compare by MEANING, not by spelling.

    The probes below already return sorted lists, so the computed side is
    canonical. The DECLARED side is whatever is in the file, and a list that
    has been reordered — by a hand edit, by a merge, by a tool that rewrites
    JSON — is the same decision written differently. Refusing it would be a
    false alarm, and a check that cries wolf gets turned off, which is the one
    way this gate can fail completely. Borrowed from the landing session, who
    put it in the kit's version and were right that mine did not have it.
    """
    if isinstance(v, list):
        return sorted(canon(x) for x in v)
    if isinstance(v, dict):
        return sorted((k, canon(x)) for k, x in v.items())
    return v


def main():
    try:
        declared = json.load(open(DECISIONS, encoding="utf-8"))["decisions"]
    except Exception as e:
        print(f"  FAIL  decisions  cannot read {os.path.relpath(DECISIONS, ROOT)} — {e}")
        return 1

    moved, undeclared, orphaned, unreadable = [], [], [], []
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
        if canon(was) != canon(now):
            moved.append((key, was, now, declared[key].get("why", "")))

    for key in declared:
        if key not in CHECKS:
            orphaned.append(key)

    if not (moved or undeclared or orphaned or unreadable):
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
        print(f"  FAIL  decisions  {key} is COMPUTED AND NOT DECLARED — {json.dumps(what, ensure_ascii=False)[:80]}")
        print("          A probe nobody declared would be adopted silently at whatever value it")
        print("          happens to hold today. Declare it, with the reason it is a decision.")
    for key in orphaned:
        print(f"  FAIL  decisions  {key} is DECLARED AND COMPUTED BY NOTHING")
        print("          A key with no probe is written down rather than watched, which reads")
        print("          exactly like a check and is not one. Add a probe or remove the key.")
    for key, why in unreadable:
        print(f"  FAIL  decisions  {key} UNREADABLE — {why}")
        print("          Reported as unreadable rather than guessed at: a source that cannot be")
        print("          read is not a decision that has not moved.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

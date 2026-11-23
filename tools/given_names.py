#!/usr/bin/env python3
"""This archive's own given-name counts, for the /your-name/ page ("The forenames").

    python3 tools/given_names.py           # write site/src/data/given-names-seen.json from the committed people data
    python3 tools/given_names.py --check   # the build gate: that file is current, and the committed Atlas snapshot holds every form in it
    python3 tools/given_names.py --refresh # write the counts, then fetch the Atlas catalogue with the kit's tool (needs the network)

THE FORMS ARE NOT KEPT HERE. Every form of a given name, by language, is kept ONCE, in Record Atlas
(data/given-name-families.json, written only through scripts/given_name_variants.py) and published as
https://recordatlas.org/given-names.json. This archive keeps no table of forms. What it keeps, and what this tool writes,
is only a COUNT: how many of the people it publishes were written with a given name, so that the page can say
«met in the records gathered here» of a form and mean this archive's own records, not the Atlas's count across every
archive (the kit's atlas_given_names.py overlays this file as `seen`, and keeps the Atlas's number as `seenAll`).

WHAT IS COUNTED. The people the site publishes as people (site/src/lib/people.js reads the same three files:
ancestors.json, families.json's members, relatives.json, de-duplicated by tree id), EVERY ONE WHO IS NOT LIVING, and for
each the FIRST given name only, one count per person. Living people are never counted, named or listed; the output is
form -> number, and no name of a person is in it. A middle name is not counted (a tree writes surnames, saints' names
and nicknames there as often as names), and neither is a name this tool cannot read as «given name + surname»:
  - a one-word name (a surname or a given name alone: which, the tree does not say);
  - a name that begins with a title or rank (Lady, Maj., King, Prince, Duke, Elector, Countess, Abbess, Marshal, Hon., Lt,
    Capt, Col, Sir, Lord, Dr, Rev ...) is read from the first word after it, but only when that is a plain word: a title
    followed by «of» (Prince of Wales ...) is a place and a rank, so it is left out;
  - a particle first (von, van, de, di): a surname alone;
  - a placeholder (unknown, unnamed, infant), an initial, or an abbreviation that ends in a full stop;
  - a name that carries a note about a family in square brackets (a tree's «[Unconfirmed Family]»): the first word is not
    reliably a given name.
  - a form the Atlas holds as «not the same» as the name it is filed under (Percy is not Pietro): it has no row to count against;
  - Formauro, read as the start of a family note and not a given name (see SKIP).
The counts of what was left out, and why, are in the file, as numbers.

THE GATE (--check, last in the build chain's data checks). It fails if (1) the committed counts are not what the people data
makes, or (2) a form in the counts is not in the committed Atlas snapshot (site/src/data/given-names.json): the fix is
never a local table, it is `given_name_variants.py add` (with evidence), `publish`, then `npm run given-names`.
"""
import argparse, json, os, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "site", "src", "data")
SEEN = os.path.join(DATA, "given-names-seen.json")
SNAP = os.path.join(DATA, "given-names.json")
KIT = os.path.join(ROOT, "site", "node_modules", "@daviddef", "archive-kit", "kit", "tools", "atlas_given_names.py")

TITLES = {"lady", "lord", "sir", "dame", "king", "queen", "prince", "princess", "duke", "duchess", "earl", "countess", "baron",
          "baroness", "elector", "palatine", "marshal", "abbess", "abbot", "bishop", "hon", "maj", "major", "lt", "capt", "captain", "col",
          "colonel", "gen", "general", "dr", "rev", "revd", "mr", "mrs", "miss", "ms", "fr", "st", "saint"}
PARTICLES = {"von", "van", "de", "di", "du", "der", "del", "della", "le", "la"}
SKIP = {"formauro": "the first word of an Italian tree entry that reads as a place or family, not a given name"}
PLACEHOLDERS = {"unknown", "unnamed", "infant", "child", "baby", "stillborn", "twin"}


def fold(s):
    t = "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if not unicodedata.combining(c))
    return t.strip().rstrip("?").strip()


def people():
    """Everyone the site publishes as a person, once each, as lib/people.js builds them (by tree id)."""
    def load(n):
        return json.load(open(os.path.join(DATA, n), encoding="utf-8"))
    byid = {}
    for p in load("ancestors.json"):
        byid[p["id"]] = {**byid.get(p["id"], {}), **p}
    for f in load("families.json"):
        for m in f["members"]:
            byid[m["id"]] = {**byid.get(m["id"], {}), **m}
    for p in load("relatives.json"):
        byid[p["id"]] = {**byid.get(p["id"], {}), **p}
    return list(byid.values())


def first_given(name):
    """(form, None) or (None, reason)."""
    raw = str(name or "")
    if re.search(r"\[[^\]]*famil", raw, re.I):
        return None, "a tree's note about a family in brackets"
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", raw)
    s = re.sub(r'"[^"]*"', " ", s)
    s = s.split(",")[0]
    toks = s.split()
    if not toks:
        return None, "no name"
    low = [t.strip(".").lower() for t in toks]
    if low[0] in PLACEHOLDERS:
        return None, "a placeholder"
    if low[0] in TITLES:
        if len(toks) > 2 and low[1] == "of":
            return None, "a title followed by a place"
        toks = toks[1:]
        low = low[1:]
        while toks and low[0] in TITLES:
            toks, low = toks[1:], low[1:]
    if len(toks) < 2:
        return None, "a one-word name"
    if low[0] in PARTICLES:
        return None, "a particle first (a surname alone)"
    if low[0] in PLACEHOLDERS:
        return None, "a placeholder"
    f = toks[0]
    if fold(f) in SKIP:
        return None, "a word the tree writes first that is not a given name"
    if f.endswith("."):
        return None, "an abbreviation"
    if len(f.strip(".")) < 2:
        return None, "an initial"
    return f, None


def not_same():
    """Forms the Atlas holds as NOT a form of the name they are filed under (Percy is not Pietro). They have no row of their own in
    the page's data, so they cannot be counted against one; they are left out, and the file says how many."""
    if not os.path.exists(SNAP):
        return set()
    snap = json.load(open(SNAP, encoding="utf-8"))
    return {fold(x["form"]) for r in snap["rows"] for x in (r.get("notSame") or [])}


def count():
    ppl = people()
    ns = not_same()
    dead = [p for p in ppl if not p.get("living")]
    forms, left = {}, {}
    for p in dead:
        f, why = first_given(p.get("name"))
        if f is None:
            left[why] = left.get(why, 0) + 1
            continue
        if fold(f) in ns:
            left["a form the Atlas holds as another name's not-same"] = left.get("a form the Atlas holds as another name's not-same", 0) + 1
            continue
        forms[f] = forms.get(f, 0) + 1
    # one entry per folded form, spelt as most often written
    merged = {}
    for f, n in forms.items():
        merged.setdefault(fold(f), []).append((n, f))
    obs = {}
    for k, v in merged.items():
        v.sort(key=lambda x: (-x[0], x[1]))
        obs[v[0][1]] = sum(n for n, _ in v)
    return {
        "note": "Generated by tools/given_names.py from the committed people data; edit nothing here. Counts of people, never of names of people: "
                "the FIRST given name of each person published as a person who is not living, one count per person. Living people are not counted. "
                "The forms themselves live only in Record Atlas (https://recordatlas.org/given-names.json).",
        "people": len(ppl), "notLiving": len(dead), "counted": sum(obs.values()), "leftOut": dict(sorted(left.items())),
        "observed": {"first given name": dict(sorted(obs.items(), key=lambda kv: fold(kv[0])))},
    }


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=1) + "\n"


def held(snap):
    out = {}
    for r in snap["rows"]:
        for fl in (r.get("langs") or {}).values():
            for f in fl:
                out[fold(f["form"])] = f
    return out


def check():
    want = count()
    ok = True
    have = open(SEEN, encoding="utf-8").read() if os.path.exists(SEEN) else ""
    if have != dump(want):
        print("given-names: FAIL, %s is not what the people data makes; run `python3 tools/given_names.py`" % os.path.relpath(SEEN, ROOT))
        ok = False
    if not os.path.exists(SNAP):
        print("given-names: FAIL, there is no Atlas snapshot at %s; run `npm run given-names` (needs the network)" % os.path.relpath(SNAP, ROOT))
        return 1
    snap = json.load(open(SNAP, encoding="utf-8"))
    h = held(snap)
    obs = want["observed"]["first given name"]
    missing = sorted(f for f in obs if fold(f) not in h)
    if missing:
        print("given-names: FAIL, %d form(s) in this archive's records are not in the Atlas catalogue snapshot: %s" % (len(missing), ", ".join(missing)))
        print("  Fix: Record Atlas `given_name_variants.py add` (with evidence) then `publish`, then `npm run given-names`. Never a local table.")
        ok = False
    stale = sorted(f for f in obs if fold(f) in h and h[fold(f)].get("seen", 0) != sum(n for g, n in obs.items() if fold(g) == fold(f)))
    if stale:
        print("given-names: FAIL, the snapshot's `seen` for %d form(s) is not this archive's count: %s; run `npm run given-names`" % (len(stale), ", ".join(stale[:12])))
        ok = False
    zero = sorted(k for k, f in h.items() if f.get("seen", 0) and k not in {fold(x) for x in obs})
    if zero:
        print("given-names: FAIL, the snapshot says this archive met %d form(s) the counts do not hold: %s" % (len(zero), ", ".join(zero[:12])))
        ok = False
    if ok:
        print("given-names: %d people, %d not living, %d counted in %d forms, %d left out; all %d forms are in the Atlas snapshot (%d names, %d forms)"
              % (want["people"], want["notLiving"], want["counted"], len(obs), sum(want["leftOut"].values()), len(obs), len(snap["rows"]), snap["totalForms"]))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--from", dest="src", help="read the Atlas catalogue from this file instead of the network")
    a = ap.parse_args()
    if a.check:
        return check()
    open(SEEN, "w", encoding="utf-8").write(dump(count()))
    print("wrote %s" % os.path.relpath(SEEN, ROOT))
    if a.refresh:
        cmd = [sys.executable, KIT, SNAP, "--seen", SEEN, "--strict"] + (["--from", a.src] if a.src else [])
        return subprocess.run(cmd).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())

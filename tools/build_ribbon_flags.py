#!/usr/bin/env python3
"""THE MINI FLAGS ON THE RIBBON CARDS (kit 1fa6b54, 27 October 2026): the kit's generator, run with this archive's inputs.

Each card of the story's ribbon (site/src/data/story.json) and of every family ribbon (site/src/data/family-ribbons.json) is
drawn with the kit's mini flags: for each place the card names, the flag of the state that held it in the card's year (from the
committed era snapshot, the same rules as the "at the time" notes) and today's country's flag where that is another flag. The
rule, the refusals and the gate are the kit's (site/node_modules/@daviddef/archive-kit/kit/docs/ribbon-flags.md); nothing here
decides a flag.

WHERE THE FLAGS LIVE. The kit's generator writes `flags` into the cards themselves, but at kit 1fa6b54 the story's contract
(checkfamilystory.py, S0) and the family ribbon's (checkfamilyribbon.py, F0) both refuse a card field they do not know, and
`flags` is one. So the cards stay as they are, and the flags are written to their own generated file, site/src/data/ribbon-flags.json
(the kit's flag records, card by card, each with the card's name and person so a card that moved is caught), which
src/lib/ribbonFlags.js puts back on the cards when the page draws them. The kit's gate is run on the cards WITH their flags.

This archive adds only its own two tables, both hand-made, each line with its evidence (`_evidence`):

    site/src/data/flag-places.json      a card's shorter place text -> the place as the person's page and the era table print it
    site/src/data/flag-countries.json   a card's place text -> today's country, where the archive's pages settle it and no
                                        era-table region does

    python3 tools/build_ribbon_flags.py            write site/src/data/ribbon-flags.json
    python3 tools/build_ribbon_flags.py --check    refuse (exit 1) a ribbon-flags.json that is not what the cards, the snapshot,
                                                   the kit's tables and this archive's two tables make
    python3 tools/build_ribbon_flags.py --gate     the kit's checkribbonflags.py on the cards with their flags and on the built
                                                   pages (the build tools/outdir.py names), then its self-test
    python3 tools/build_ribbon_flags.py --report   every flag, and every place line left without one and why

Run it after the story's ribbon, the family ribbons (tools/build_family_ribbons.mjs), the era snapshot or either table changes,
and commit ribbon-flags.json with them.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outdir  # noqa: E402

ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "src", "data")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
GEN = os.path.join(KIT_TOOLS, "ribbonflags.py")
GATE = os.path.join(KIT_TOOLS, "checkribbonflags.py")
SNAPSHOT = os.path.join(DATA, "era-snapshot.json")
STORY = os.path.join(DATA, "story.json")
FAMILIES = os.path.join(DATA, "family-ribbons.json")
ALIAS = os.path.join(DATA, "flag-places.json")
COUNTRIES = os.path.join(DATA, "flag-countries.json")
OUT = os.path.join(DATA, "ribbon-flags.json")
NOTE = ("Made by tools/build_ribbon_flags.py (the kit's ribbonflags.py on story.json and family-ribbons.json, with era-snapshot.json, "
        "flag-places.json and flag-countries.json); do not edit by hand. Each entry is one ribbon card's flags, by the card's place in "
        "its ribbon, with its name and person; src/lib/ribbonFlags.js puts them on the cards the page draws.")


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text_of(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def flagged(td, quiet=True, report=None):
    """Copies of story.json and family-ribbons.json with the kit's flags on their cards: (story, families, process)."""
    s, f = os.path.join(td, "story.json"), os.path.join(td, "family-ribbons.json")
    shutil.copyfile(STORY, s)
    shutil.copyfile(FAMILIES, f)
    cmd = [sys.executable, GEN, "--snapshot", SNAPSHOT, "--alias", ALIAS, "--countries", COUNTRIES, "--story", s,
           "--family-lines", f, "--write"] + (["--report", report] if report else [])
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    if r.returncode != 0:
        if quiet:
            sys.stdout.write(r.stdout or "")
            sys.stderr.write(r.stderr or "")
        raise SystemExit(r.returncode)
    return s, f, r


def entries(cards):
    return [{"card": i, "name": c.get("name"), "person": c.get("person"), "flags": c["flags"]}
            for i, c in enumerate(cards or []) if c.get("flags")]


def make(td):
    s, f, r = flagged(td)
    story, fams = load(s), load(f)
    doc = {"_note": NOTE,
           "story": entries((story.get("ribbon") or {}).get("cards")),
           "families": {fam["id"]: entries(fam.get("cards")) for fam in fams["families"] if entries(fam.get("cards"))}}
    return doc, r


def merged(td, doc):
    """story.json and family-ribbons.json with ribbon-flags.json put back on their cards (what the pages draw)."""
    story, fams = load(STORY), load(FAMILIES)

    def put(cards, ents, where):
        for e in ents:
            c = cards[e["card"]] if e["card"] < len(cards) else None
            if c is None or c.get("name") != e["name"] or c.get("person") != e["person"]:
                raise SystemExit(f"build_ribbon_flags: {where} card {e['card']} is not {e['name']!r} any more: run python3 tools/build_ribbon_flags.py")
            c["flags"] = e["flags"]
    put(story["ribbon"]["cards"], doc.get("story") or [], "story")
    by_id = {fam["id"]: fam for fam in fams["families"]}
    for fid, ents in (doc.get("families") or {}).items():
        if fid not in by_id:
            raise SystemExit(f"build_ribbon_flags: family {fid} has no ribbon any more: run python3 tools/build_ribbon_flags.py")
        put(by_id[fid]["cards"], ents, f"family {fid}")
    s, f = os.path.join(td, "story-merged.json"), os.path.join(td, "family-ribbons-merged.json")
    with open(s, "w", encoding="utf-8") as fh:
        fh.write(text_of(story))
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(text_of(fams))
    return s, f


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true")
    g.add_argument("--gate", action="store_true")
    g.add_argument("--report", action="store_true")
    a = ap.parse_args()
    for p in (GEN, GATE):
        if not os.path.exists(p):
            print(f"build_ribbon_flags: the kit's {os.path.basename(p)} is not installed (npm install in site/)", file=sys.stderr)
            return 2
    with tempfile.TemporaryDirectory() as td:
        if a.report:
            flagged(td, quiet=False)
            return 0
        if a.gate:
            s, f = merged(td, load(OUT))
            cmd = [sys.executable, GATE, "--snapshot", SNAPSHOT, "--story", s, "--family-lines", f, "--alias", ALIAS,
                   "--countries", COUNTRIES, "--dist", outdir.out()]
            r = subprocess.run(cmd)
            if r.returncode:
                return r.returncode
            return subprocess.run([sys.executable, GATE, "--selftest"]).returncode
        doc, r = make(td)
        text = text_of(doc)
        head = (r.stdout.splitlines() or [""])[0]
        if a.check:
            try:
                with open(OUT, encoding="utf-8") as fh:
                    same = fh.read() == text
            except OSError:
                same = False
            if not same:
                print("build_ribbon_flags: site/src/data/ribbon-flags.json is not what the cards, the snapshot and the tables make: "
                      "run python3 tools/build_ribbon_flags.py", file=sys.stderr)
                return 1
            merged(td, doc)
            print(f"  ok    ribbon flags  ribbon-flags.json is what the data makes ({head.replace('ribbonflags: ', '')})")
            return 0
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("build_ribbon_flags: wrote site/src/data/ribbon-flags.json; " + head.replace("ribbonflags: ", ""))
        return 0


if __name__ == "__main__":
    sys.exit(main())

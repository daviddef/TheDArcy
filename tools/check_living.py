#!/usr/bin/env python3
"""Refuse to ship a build that names a living person.

The rule this archive is built on: LIVING PEOPLE ARE NOT PUBLISHED AT ALL —
not hidden, not gated, absent from the output. build_site_data.py applies it
once, at the boundary between the research data and the site, so that nobody
can be living on one page and dead on another.

This is the check that the rule actually held, and it reads the BUILT HTML,
because that is the only place a leak can be seen. Source can be correct and
output wrong: a living person's name reaches a page through a deceased
relative's spouses, parents and children long after they were filtered out of
the person list.

WHY IT DOES NOT USE A COMMITTED LIST OF NAMES
---------------------------------------------
The kit's checkliving.py has a --declared mode that reads a living.json full
of forbidden names. That is right for the children's site, which guards four
people. It is wrong here, for two reasons:

  1. This tree holds over two thousand living people. A file listing them, in
     a PUBLIC repository, would be precisely the disclosure the rule exists to
     prevent — a machine-readable directory of living relatives, committed
     forever to a git history.
  2. A hand-kept list goes stale. The GEDCOM is the authority on who is alive,
     it is regenerated whenever the tree is exported, and it is gitignored.

So the names are read from sources/*.ged at check time and never written down.
What IS committed is site/src/data/living.json: the policy, the exceptions,
and the counts. Exceptions need human judgement and version control. Names do
not need either.

    python3 tools/check_living.py            # gate the build
    python3 tools/check_living.py --verbose  # show what was matched and why

Exit 1 on any leak, and exit 1 if the GEDCOM is missing — a guard that cannot
read its source has not passed, it has failed to run.
"""
import os, re, sys, json, html, glob, argparse, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gedcom import load, display, classify_living          # noqa: E402

DIST = os.path.join(ROOT, "site", "dist")
DECL = os.path.join(ROOT, "site", "src", "data", "living.json")

# A bare surname matches every page in this archive and a bare forename matches
# most of them, so what is forbidden is a NAME PHRASE: given + surname, and the
# full recorded name. Two things then have to be subtracted, or the check cries
# wolf 1,500 times and gets switched off:
#
#   · EXACT NAMESAKES. Names repeat every generation in this family. Where a
#     living person's name is also a published dead person's name, the phrase
#     cannot distinguish them and must not be forbidden.
#   · LONGER NAMES THAT CONTAIN IT. "Bruce Atwell" sits inside "Eric George
#     Bruce Atwell" (b. 1918), "Mary Davis" inside "Norma Mary Davis", "Anne
#     Corbett" inside "Eliza Anne Corbett Sneyd". A hit is only a hit if it is
#     not part of a longer published name at that position.
MIN_PHRASE = 7


def norm(name):
    name = re.sub(r"\s*\(.*?\)", " ", name or "")
    name = re.sub(r"[\"\u201c\u201d]", " ", name)
    return " ".join(name.split())


def phrases_of(full):
    """The forms a page might use: the whole recorded name, and first + last."""
    parts = full.split()
    if len(parts) < 2:
        return set()
    return {" ".join(parts), parts[0] + " " + parts[-1]}


def visible(src):
    """What a reader sees. A name inside <script> is still a leak, so the raw
    HTML is searched too — this is only used to quote the context back."""
    s = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", src)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=DIST)
    ap.add_argument("--declared", default=DECL)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    geds = sorted(glob.glob(os.path.join(ROOT, "sources", "*.ged")))
    if not geds:
        print("check_living: no GEDCOM under sources/. This guard reads the tree to "
              "learn who is alive, so a missing tree is a FAILURE, not a pass.")
        return 1
    if not os.path.isdir(a.dist):
        print(f"check_living: no {a.dist} — build first")
        return 1

    if not os.path.exists(a.declared):
        print(f"check_living: no declaration at {a.declared}. The exceptions are the "
              f"part a human has to judge, so a missing declaration is a FAILURE.")
        return 1
    decl = json.load(open(a.declared, encoding="utf-8"))
    # Two kinds of exception, kept apart on purpose. A NAMESAKE is not a living
    # person at all — a historical Richard Smith, a middle name inside a longer
    # one. A NAMED entry IS a living person this archive has decided to name,
    # and the reader of this file should be able to see which is which without
    # reading the reasons.
    allow = {x.lower() for x in decl.get("allow", [])}
    allow |= {e["phrase"].lower() for e in decl.get("namesakes", []) if e.get("phrase")}
    allow |= {e["phrase"].lower() for e in decl.get("named", []) if e.get("phrase")}
    allow_files = set(decl.get("allowFiles", []))

    people, families = load()
    living_ids = classify_living(people, families)
    living  = [p for p in people if living_ids.get(p)]
    publish = [p for p in people if not living_ids.get(p)]

    # Everything the archive is allowed to say. Used twice: to drop exact
    # namesakes, and to recognise a longer name that merely contains a
    # forbidden phrase.
    pub_names = {norm(display(people[p]) or "") for p in publish}
    pub_names = {n for n in pub_names if len(n.split()) >= 2}
    pub_phrases = set()
    for n in pub_names:
        pub_phrases |= {x.lower() for x in phrases_of(n)}

    forbidden = collections.defaultdict(set)
    for pid in living:
        for ph in phrases_of(norm(display(people[pid]) or "")):
            low = ph.lower()
            if len(low) < MIN_PHRASE or low in pub_phrases:
                continue                       # an exact namesake: cannot tell them apart
            forbidden[low].add(pid)

    # For each forbidden phrase, the longer published names that contain it —
    # a hit inside one of these is somebody else, spelled at greater length.
    covers = {ph: sorted((n for n in pub_names if ph in n.lower() and
                          len(n) > len(ph)), key=len, reverse=True)
              for ph in forbidden}

    pages = {}
    for root, _, files in os.walk(a.dist):
        for f in files:
            if f.endswith(".html"):
                p = os.path.join(root, f)
                pages[os.path.relpath(p, a.dist).replace(os.sep, "/")] = \
                    open(p, encoding="utf-8", errors="replace").read()
    if len(pages) < 5:
        print(f"check_living: only {len(pages)} page(s) under {a.dist} — the build is "
              f"unfinished. Refusing to pass.")
        return 1

    # One combined pattern, one pass per page: two thousand separate regex
    # sweeps over seven hundred pages is slow enough that nobody would keep it
    # in the build, and a guard that gets switched off guards nothing.
    rx = re.compile(r"\b(" + "|".join(sorted(map(re.escape, forbidden), key=len,
                                             reverse=True)) + r")\b", re.I)

    fails, allowed_hits, covered_hits = [], 0, 0
    for rel, raw in pages.items():
        if rel in allow_files:
            continue
        text = visible(raw)
        for m in rx.finditer(text):
            ph = m.group(1).lower()
            window = text[max(0, m.start() - 40):m.end() + 40]
            if any(longer.lower() in window.lower() for longer in covers.get(ph, ())):
                covered_hits += 1
                continue                       # part of a longer published name
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 70):m.end() + 70]).strip()
            if ph in allow or any(x in ctx.lower() for x in allow):
                allowed_hits += 1
                continue
            fails.append((rel, m.group(1), ctx))

    counts = {"tree": len(people), "living": len(living),
              "published": len(publish),
              "phrases": len(forbidden), "pages": len(pages)}

    if fails:
        print(f"  FAIL  living      {len(fails)} leak(s) in {len(pages)} pages")
        seen = set()
        for rel, who, ctx in fails:
            if who in seen and not a.verbose:
                continue
            seen.add(who)
            print(f"          /{rel}  →  «{who}» is judged LIVING by the tree")
            print(f"              …{ctx}…")
            if not a.verbose and len(seen) >= 10:
                break
        if len(fails) > len(seen):
            print(f"          … {len(fails)} hits in total")
        print("\n  A living person is not published here at all. If one of these people "
              "has died,\n  record the death in the tree and re-export — do not add them to "
              "the allow list.\n  If it is a namesake, add the phrase to `allow` in "
              "site/src/data/living.json\n  with a note saying who the historical person is.")
        return 1

    if not a.quiet:
        named = sum(1 for e in decl.get("named", []) if e.get("living"))
        print(f"  ok    living      {counts['pages']} pages carry none of "
              f"{counts['phrases']:,} name phrases belonging to "
              f"{counts['living']:,} living people"
              + (f" — {allowed_hits} declared, {covered_hits} inside longer published names"
                 if (allowed_hits or covered_hits) else "")
              + (f"; {named} living people named by declaration" if named else ""))
    if a.verbose:
        print(f"        tree {counts['tree']:,} · living {counts['living']:,} · "
              f"publishable {counts['published']:,}")

    # The counts are quoted on six pages of this site. They were hardcoded on
    # all six until 14 September 2026, which is how the nationality audit
    # drifted. Write them down once, here, where they are computed.
    if os.path.exists(a.declared):
        decl["counts"] = counts
        decl.pop("countsNote", None)
        decl["countsNote"] = ("Written by tools/check_living.py on every build. "
                              "Never type these numbers into a page.")
        json.dump(decl, open(a.declared, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

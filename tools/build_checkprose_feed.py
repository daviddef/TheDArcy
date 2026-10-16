#!/usr/bin/env python3
"""Build the feed the kit's prose gate (kit/tools/checkprose.py) reads: who is living, who is dead.

    python3 tools/build_checkprose_feed.py            # writes the feed OUTSIDE the repository
    python3 tools/build_checkprose_feed.py --counts   # counts only, writes nothing

The feed holds living people's NAMES, so it is never inside the repository: it goes to
$CHECKPROSE_FEED or ~/.local/state/darcy-archive/checkprose-feed.json, created readable by its
owner only. This script prints COUNTS ONLY, never a name.

    {"living":    [{"id": "person-<tree number>", "names": ["Given Family", ...]}, ...],
     "deadNames": ["Given Family", ...]}

WHO IS LIVING IS NOT DECIDED HERE. It is gedcom.classify_living(), which asks the kit's
living_rule.py and, since 16 October 2026, passes each person's youngest dated child, so an
undated parent of a recent child is living and is in this feed. A second definition of who is
living would be the thing the kit exists to prevent. HELD-OUT people (possible minors, the one
promised privacy by id) are fed in as living too: held out means ABSENT, so any date beside such
a name in a hand-written file is as wrong as for a living person.

WHO IS DEAD IS DECIDED BY IDENTITY, never as "every name that is not a living name". A living
person and an ancestor who share a name would then cancel each other out of the corpus; the kit
skips and counts a phrase both have rather than guess. The dead are the tree's rows that are
neither living nor held out.

THE FEED CAN ONLY BE BUILT FROM THE GEDCOM, which is gitignored and absent in CI, because it
carries every living person in full. When it cannot be read this says so (exit 2, NOT RUN):
"cannot say who is living" is not "nobody is".
"""
import os, sys, re, json, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
KIT_TOOLS = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools")
DEFAULT_FEED = os.path.join(os.path.expanduser("~"), ".local", "state", "darcy-archive", "checkprose-feed.json")
sys.path.insert(0, HERE)
sys.path.insert(0, KIT_TOOLS)


def feed_path(explicit=None):
    return explicit or os.environ.get("CHECKPROSE_FEED") or DEFAULT_FEED


def _clean(n):
    return re.sub(r"\s+", " ", str(n or "").replace("/", " ").replace('"', " ")).strip()


def spellings(p):
    """Every plain 'Given Family' string the tree records for one person."""
    out = set()
    given, sur, nick = _clean(p.get("given")), _clean(p.get("surname")), _clean(p.get("nick"))
    name = _clean(p.get("name"))
    if given and sur:
        out.add("%s %s" % (given, sur))
        first = given.split()[0]
        if nick:
            out.add("%s %s" % (nick, sur))               # "Nita Lerena"
            out.add("%s %s %s" % (first, nick, sur))
        m = re.search(r"\(([^)]+)\)", given)              # "Maria (Catherine)" -> "Catherine Whiite"
        if m:
            out.add("%s %s" % (m.group(1).strip(), sur))
    if name:
        out.add(name)
    return sorted(s for s in out if len(s.split()) >= 2)


def build():
    """Return (feed, stats), or (None, reason) when who is living cannot be decided on this machine."""
    if not glob.glob(os.path.join(ROOT, "sources", "*.ged")):
        return None, "the GEDCOM is not here (it is gitignored: it carries every living person)"
    try:
        import gedcom as g
        people, fams = g.load()[:2]
    except Exception as e:                                           # noqa: BLE001
        return None, "the tree could not be read (%s)" % type(e).__name__
    if len(people) < 1000:
        return None, "the tree has %d people; refusing to decide who is living from that" % len(people)
    living = g.classify_living(people, fams)
    held = g.held_out(people, living)
    live = {pid for pid, v in living.items() if v}
    hold = set(held)
    anyone = live | hold
    num = lambda pid: re.sub(r"\D", "", pid) or pid

    feed_living = [{"id": "person-%s" % num(pid), "names": spellings(people[pid])} for pid in sorted(anyone)]
    feed_living = [x for x in feed_living if x["names"]]
    dead = set()
    n_dead_rows = 0
    for pid, p in people.items():
        if pid in anyone:
            continue
        n_dead_rows += 1
        dead.update(spellings(p))
    feed = {"living": feed_living, "deadNames": sorted(dead)}

    stats = {"people in the tree": len(people), "living by the kit rule": len(live),
             "held out (also fed as living)": len(hold),
             "living people in the feed": len(feed_living),
             "living names": sum(len(x["names"]) for x in feed_living),
             "dead rows": n_dead_rows, "dead names": len(dead)}
    try:
        import checkprose as cp
        lp, dp = set(), set()
        for x in feed_living:
            lp |= cp.phrases(x["names"])
        for n in dead:
            dp |= cp.phrases([n])
        stats["living phrases"] = len(lp)
        stats["living phrases shared with a dead person (skipped, never guessed)"] = len(lp & dp)
    except ImportError:
        pass
    return feed, stats


def write(feed, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the living / dead name feed for checkprose.py (counts only are printed).")
    ap.add_argument("--out")
    ap.add_argument("--counts", action="store_true")
    a = ap.parse_args(argv)
    feed, stats = build()
    if feed is None:
        print("build_checkprose_feed: NOT RUN (%s)" % stats)
        return 2
    for k, v in stats.items():
        print("  %-68s %d" % (k, v))
    if not a.counts:
        out = feed_path(a.out)
        write(feed, out)
        print("  feed written, mode 0600, outside the repository")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read this archive against its own open questions.

Written on 14 September 2026, immediately after discovering that Constantine
D'Arcy's christening had been published on one page of this site for weeks
while three other pages called him unplaced. That was not a research failure;
it was a filing failure, and the fix for a filing failure is an index.

For each open question this script holds a set of search terms. It then reads
EVERY data file, the register, and the built HTML of every page, and reports
each place the terms appear — so a question can be checked against what the
archive already knows before anybody goes looking outside it.

    python3 tools/crossread.py            # all questions
    python3 tools/crossread.py pitt jane  # only the ones whose id matches

It answers nothing by itself. It puts the evidence in one place so a person
can see whether an answer is already sitting here.
"""
import json, os, re, sys, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "src", "data")
DIST = os.path.join(ROOT, "site", "dist")

# Files that are indexes OF this archive rather than evidence IN it. Searching
# them just reports that the search page can find things, which is not news.
SKIP = {"mentions.json", "searchindex.json", "search.json", "provenance.json",
        "dossiers.json", "audit.json", "trees.json"}

QUESTIONS = [
    dict(id="parentage", owner="/hornby",
         q="Who were Robert D'Arcy's own parents?",
         terms=[r"Holderness", r"Conyers", r"\bD'?Arcy of\b", r"Aston",
                r"Hornby", r"son of .{0,30}D'?Arcy"]),
    dict(id="richard", owner="/joseph-darcy",
         q="Was Richard Darcy, aged 57 at Priestlands in 1841, Robert's son?",
         terms=[r"Richard\s+D'?Arc", r"Richard\s+Darc"]),
    dict(id="jane", owner="/constantine",
         q="What became of Jane D'Arcy, christened Barbados 1788?",
         terms=[r"Jane\s+D'?Arc", r"Jane\s+Darc", r"Jean\s+Ward"]),
    dict(id="barbados", owner="/the-corps",
         q="When did Robert D'Arcy go to Barbados and when did he come home?",
         terms=[r"Barbado", r"West Indies", r"St Domingo", r"Leeward"]),
    dict(id="pitt", owner="/joseph-darcy",
         q="Who was Elizabeth Pitt, in Joseph's house in 1841?",
         # "Pitt" alone drowns in George Pitt D'Arcy, whose middle name is the
         # whole reason the question exists. Look for the surname standing alone.
         terms=[r"\bPitt\b(?![-\s]*[’']?\s*(?:D|d'|Darcy|D'Arcy))"]),
    dict(id="marthaw", owner="/wakefields",
         q="Who was Martha Wakefield, named on five pages with no source?",
         terms=[r"Martha\s+Wakef", r"Martha\s+Golding"]),
    dict(id="lydia", owner="/hannah-baptism",
         q="What was Lydia's surname?",
         terms=[r"Lydia", r"Lyddya", r"Liddia"]),
    dict(id="mariawhite", owner="/george-pitt",
         q="Where did George Pitt D'Arcy marry Maria White?",
         terms=[r"Maria\s+White", r"Wicklow"]),
    dict(id="charlotte", owner="/chatham",
         q="What became of Charlotte D'Arcy, born Chatham 1825?",
         terms=[r"Charlotte\s+D'?Arc", r"Charlotte\s+Darc"]),
    dict(id="wsneyd", owner="/sneyds",
         q="Who was William Sneyd of Madeley, born 1746?",
         terms=[r"William\s+Sneyd", r"Madeley"]),
    dict(id="cotton", owner="/sneyds",
         q="Where did Catherine Cotton come from?",
         terms=[r"Cotton"]),
    dict(id="gpgap", owner="/australia",
         q="Where was George Pitt D'Arcy between 1832 and 1849?",
         terms=[r"Orthes", r"39th (?:Regiment|Foot)", r"half.?pay"]),
    dict(id="frederick", owner="/people/frederick-robert-d-arcy",
         q="Frederick Robert D'Arcy the surveyor — the rest of him",
         terms=[r"Frederick\s+Robert", r"Spring Hill"]),
]


URL = re.compile(r"https?://\S+|\b[\w-]+\.(?:com|org|uk|au|ie|gov)\S*")


def strip_urls(t):
    """A slug is a link, not a mention. george-pitt-darcy is not somebody
    writing about Pitt, and left in it swamps every surname search."""
    return URL.sub(" ", t)


def load_texts():
    """Everything this archive has written down, as (where, text) pairs."""
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        if os.path.basename(f) in SKIP:
            continue
        out.append(("data/" + os.path.basename(f),
                    strip_urls(json.dumps(json.load(open(f, encoding="utf-8")),
                                          ensure_ascii=False))))
    for f in sorted(glob.glob(os.path.join(DIST, "**", "index.html"),
                              recursive=True)):
        page = "/" + os.path.relpath(os.path.dirname(f), DIST).replace("\\", "/")
        if page == "/.":
            page = "/"
        # Person pages under /who and /people are generated from the register,
        # so they echo it; keep them but mark them, they are not independent.
        t = open(f, encoding="utf-8").read()
        t = re.sub(r"(?s)<(script|style|nav|footer)[^>]*>.*?</\1>", " ", t)
        t = re.sub(r"<[^>]+>", " ", t)
        out.append((page, strip_urls(html.unescape(re.sub(r"\s+", " ", t)))))
    return out


def main(argv):
    want = [a.lower() for a in argv[1:]]
    texts = load_texts()
    print(f"crossread: {len(texts)} data files and pages\n")
    for qn in QUESTIONS:
        if want and not any(w in qn["id"] for w in want):
            continue
        print("=" * 72)
        print(f"{qn['id'].upper()}  ·  {qn['q']}")
        print(f"  owned by {qn['owner']}")
        pat = re.compile("|".join(qn["terms"]), re.I)
        hits = []
        for where, text in texts:
            if where == qn["owner"] or where.startswith(qn["owner"] + "/"):
                continue
            found = list(pat.finditer(text))
            if found:
                hits.append((where, len(found), found[0]))
        if not hits:
            print("  nothing elsewhere in the archive.\n")
            continue
        # Data files first: they are the source, pages are the rendering.
        hits.sort(key=lambda h: (not h[0].startswith("data/"), -h[1]))
        for where, n, m in hits[:14]:
            s = max(0, m.start() - 90)
            snip = m.string[s:m.start() + 150].strip()
            print(f"  {where}  ({n})")
            print(f"      …{snip}…")
        if len(hits) > 14:
            print(f"  … and {len(hits) - 14} more places")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

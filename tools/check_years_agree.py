#!/usr/bin/env python3
"""Does every page that prints a person's years print the years THEIR page prints?

Written 16 October 2026, and rewritten the same day. It began as a check on one
chart (check_chart_years.py) after /tree drew William Hartley Sneyd as 1838–1902
for weeks while his own page said 1837–1902. Fixing the chart and looking again
found the SAME fault in six more places, which is the real finding: this archive
keeps a corrections map (lib/corrections.js) for where its research overturned
the family tree, and every page that prints a lifespan has to remember to read
it. Person pages did. Pedigree cards did. The chart, /people, /bloodline,
/register, /graves, /sneyd and /families did not. Patching renderers one at a
time is how it recurred; this refuses the whole class.

IT READS ONLY THE BUILT HTML, because the fault lives between two readers of one
fact and no gate that reads one source can see it. For every link to a person
page, anywhere on the site, followed by a lifespan — either just after the link
or inside it, which is how a card is built — the years must be the years that
person's own page prints. It never asks which is right. That is a research
question. It asks only whether the archive agrees with itself.

THREE THINGS IT DOES NOT DO, SAID PLAINLY. It cannot see /bloodline, which embeds its
data as JSON for the browser and prints no person links to compare; that page was fixed
and checked by hand, and a regression there would pass this gate. It compares only a full «YYYY–YYYY»;
a «b. 1814» or a lone death year is not checked. And it compares what is
printed beside a LINK, so a lifespan in running prose that happens to name
somebody is not seen — which is also why /changes and /corrections can quote the
tree's old year, on purpose, without tripping it.

SECOND CLAUSE, ADDED THE SAME WEEK: THE PROSE CASE. Everything above compares a lifespan printed
beside a LINK, so a birth year typed into a sentence is invisible to it, and that is exactly where
the stale 1810 for Samuel Charles Sneyd survived on two hand-written pages after his correction
was made. So for each person in lib/corrections.js whose birth or death year the archive has
overturned, the TREE's lifespan (and the tree's full dates) must not appear in the text of any
page within 160 characters of that person's name, unless the words around it quote it as the
tree's claim. The pages whose job is narrating errors (/changes, /corrections, /worklist,
/searched) are exempt, because they quote the old value on purpose and say why. What this cannot
see: a stale year written WITHOUT the person's name beside it, or in a different form than the
tree's own lifespan string; and it does not read data files, only built pages.

THIRD CLAUSE: THE CAUSE, NOT THE SYMPTOM. Four of the six stale years found in two days had one
origin: a record line said "the tree says <year>" for a person the archive had read a register for,
and the person never reached lib/corrections.js, so only the pages that read the map were right. The
prose clause cannot see a person who is not in the map at all. So every record line in register.json
that states what the tree says, with a year the record's own text does not contain, must name a person
who IS in the map. It covers only that phrasing ("the tree says / puts / gives / said / has ..."): a
discrepancy recorded in other words escapes it, and a person genuinely left uncorrected on purpose
belongs in UNRESOLVED below with the reason.

A check that examined nothing must not pass. It prints how many links it
compared, refuses at zero, and separately refuses if it compared no chart box,
because the chart was the first place this was found and a markup change there
must not silently drop it out of the count.
"""
import os, re, sys, glob, html, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import outdir
    DIST = outdir.out()
except ImportError:
    _o = os.environ.get("ARCHIVE_OUT")
    DIST = os.path.join(os.path.dirname(HERE), "site", _o) if _o else os.path.join(os.path.dirname(HERE), "site", "dist")

Y = r"(\d{4}\s*[–-]\s*\d{4})"
H1 = re.compile(r"<h1[^>]*>")
LINK = re.compile(r'<a [^>]*href="/people/([a-z0-9-]+)/?"[^>]*>(.*?)</a>(.{0,170})', re.S)
CHART_BOX = re.compile(r'<span class="ac-d">')


def norm(x):
    return re.sub(r"\s", "", html.unescape(x)).replace("-", "–")


def read(f):
    return open(f, encoding="utf-8", errors="ignore").read()


def truth():
    """slug -> the years that person's own page prints, from its eyebrow."""
    t = {}
    for f in glob.glob(os.path.join(DIST, "people", "*", "index.html")):
        slug = f.split(os.sep)[-2]
        s = read(f)
        m = H1.search(s)
        if not m:
            continue
        head = re.sub(r"<[^>]+>", " ", s[max(0, m.start() - 400):m.start()])
        ys = re.findall(Y, head)
        if ys:
            t[slug] = norm(ys[-1])
    return t


NARRATING = {"changes", "corrections", "worklist", "searched"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def _fold(x):
    return re.sub(r"\s+", " ", html.unescape(x)).replace("-", "\u2013").lower()


def corrected_people(tr):
    """{slug: (name, [needles])}: for each person whose born/died the corrections map overturns, what the
    TREE says, as strings a page could print. Read from the committed data and corrections.js only."""
    import json
    src = read(os.path.join(os.path.dirname(HERE), "site", "src", "lib", "corrections.js"))
    body = src[src.index("export const CORRECTIONS"):src.index("export const yearOf")]
    slugs = []
    for m in re.finditer(r'^  "([a-z0-9-]+)": \{', body, re.M):
        blk = body[m.end():]
        blk = blk[:blk.index("\n  },")]
        if re.search(r"^\s+(born|died):", blk, re.M):
            slugs.append(m.group(1))
    sys.path.insert(0, HERE)
    import slugrule
    id_by_slug = {v: k for k, v in slugrule.slugs().items()}
    data = os.path.join(os.path.dirname(HERE), "site", "src", "data")
    rows = {}
    for f in ("ancestors", "families", "relatives"):
        d = json.load(open(os.path.join(data, f + ".json"), encoding="utf-8"))
        items = [m for fam in d for m in fam["members"]] if f == "families" else (d if isinstance(d, list) else [])
        for r in items:
            if isinstance(r, dict) and r.get("id") and r["id"] not in rows:
                rows[r["id"]] = r
    out = {}
    for sl in slugs:
        r = rows.get(id_by_slug.get(sl))
        if not r:
            continue
        needles = set()
        if r.get("life"):
            needles.add(_fold(re.sub(r"\s", "", r["life"])))
        # A FULL DATE IS A NEEDLE ONLY FOR THE FIELD THE ARCHIVE OVERTURNED. The first version added the tree's
        # death date for everybody and flagged Robert D'Arcy's 13 May 1827, which is RIGHT: the archive corrected
        # his birth, not his death. A needle that fires on a correct statement teaches people to ignore the gate.
        truth_years = ((tr.get(sl) or "").replace("\u2013", "-").split("-") + ["", ""])[:2]
        for k, ty in (("born", truth_years[0]), ("died", truth_years[1])):
            if not ty or str(ty) in str(r.get(k) or ""):
                continue                          # the finding agrees with the tree on this field
            ty_tree = re.search(r"\d{4}", str(r.get(k) or ""))
            if ty_tree:                           # "born 1787", "b. 1787", "died 1856", "d. 1856"
                for w in (("born", "b.") if k == "born" else ("died", "d.")):
                    needles.add(_fold("%s %s" % (w, ty_tree.group(0))))
            m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s+(\d{4})$", str(r.get(k) or "").strip())
            if m:
                mon = next((x for x in MONTHS if x[:3].lower() == m.group(2).lower()), None)
                if mon:
                    needles.add(_fold("%d %s %s" % (int(m.group(1)), mon, m.group(3))))
        words = re.sub(r"[^\w' -]", " ", r.get("name") or "").split()
        names = {_fold(" ".join(words))}
        if len(words) >= 2:
            names.add(_fold(words[0] + " " + words[-1]))
        tree_years = (re.findall(r"\d{4}", str(r.get("life") or "")) + ["", ""])[:2]
        out[sl] = (r.get("name"), sorted(n for n in needles if n), sorted(n for n in names if n), tree_years)
    return out


def stale_prose(pages, tr):
    """Pages that print a corrected person's TREE year beside their name, as if it were the finding."""
    people = corrected_people(tr)
    # a needle is only a fault where the archive actually disagrees with it
    live = {}
    for sl, (nm, needles, names, tree_years) in people.items():
        truth = tr.get(sl)
        live[sl] = (nm, [n for n in needles if n != truth], names)
    n_needles = sum(len(v[1]) for v in live.values())
    # the corrected years, per person, for the comparison exemption
    # ONLY A YEAR THAT DIFFERS FROM THE TREE'S COUNTS AS «THE CORRECTED VALUE STATED BESIDE IT». The first version
    # took every year of the corrected lifespan, so a stale «1810–1885» was excused by the 1885 inside itself,
    # which the archive never changed. A planted fault found it: the gate passed a statement it should refuse.
    truth_tokens = {}
    for sl in live:
        yrs = re.findall(r"\d{4}", tr.get(sl) or "")
        ty = people[sl][3]
        truth_tokens[sl] = {y for i, y in enumerate(yrs[:2]) if i < 2 and y != ty[i]}
    bad = []
    for f in pages:
        page = os.path.relpath(f, DIST).replace(os.sep, "/").replace("/index.html", "") or "/"
        if page in NARRATING:
            continue
        s = read(f)
        mk = s.find("Corrected against the family tree")
        if mk != -1:                          # the correction box quotes the tree's year on purpose
            end = s.find("</ul>", mk)
            s = s[:mk] + s[end:] if end != -1 else s[:mk]
        # THE «EVERYWHERE X APPEARS» SECTION IS EXCERPTS OF OTHER PAGES, gathered by a script. A snippet is cut at
        # a fixed length, so it can quote a narrating page's old value and lose the words that said it was old.
        # The page it was cut from is checked in its own right (or exempt as a narrating page), so nothing is lost.
        em = re.search(r"<h2>Everywhere .{0,80}? appears in this archive</h2>.*?</section>", s, re.S)
        if em:
            s = s[:em.start()] + s[em.end():]
        t = _fold(re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>|<script.*?</script>", " ", s, flags=re.S)))
        for sl, (nm, needles, names) in live.items():
            for nd in needles:
                for m in re.finditer(re.escape(nd), t):
                    lo, hi = max(0, m.start() - 160), m.end() + 160
                    if not any(name in t[lo:hi] for name in names):
                        continue
                    if re.search(r"\btree\b|\btree's\b", t[max(0, m.start() - 230):m.end() + 80]):
                        continue              # quoted as the tree's claim
                    if any(re.search(r"\b%s\b" % re.escape(y), t[max(0, m.start() - 220):m.end() + 220])
                               for y in truth_tokens.get(sl, ())):
                            continue
                    if any(re.search(r"\b%s\b" % re.escape(y), t[max(0, m.start() - 220):m.end() + 220])
                           for y in truth_tokens.get(sl, ())):
                        # "born 1782, not 1787" / "as 1838-1902 and his own page said 1837-1902": the old value is
                        # quoted AS the old value, with the corrected one stated right beside it. That is a
                        # comparison and not a stale claim.
                        continue
                    bad.append((page, sl, nd, t[max(0, m.start() - 70):m.end() + 40]))
    return bad, len(live), n_needles


# A person whose record line says the tree is wrong, left uncorrected ON PURPOSE. Name: reason. Empty today.
UNRESOLVED = {}
TREE_CLAIM = re.compile(r"\bthe tree (?:says|puts|gives|said|has|had|wrote|dates|records|calls)\b([^;\u00b7\u2014]{0,100}?)(\b1[5-9]\d{2}\b)", re.I)


def pending_corrections():
    """Record lines that say 'the tree says <year>' with a year the record's own text lacks, for a person who is
    not in lib/corrections.js. Returns (pending, total_lines, disagreeing_lines)."""
    import json
    src = read(os.path.join(os.path.dirname(HERE), "site", "src", "lib", "corrections.js"))
    body = src[src.index("export const CORRECTIONS"):src.index("export const yearOf")]
    mapped = {m.group(1) for m in re.finditer(r'^  "([a-z0-9-]+)": \{', body, re.M)}
    reg = json.load(open(os.path.join(os.path.dirname(HERE), "site", "src", "data", "register.json"), encoding="utf-8"))
    tree = {}
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] == "tree":
                tree.setdefault(r["name"], []).append(r["link"].rsplit("/", 1)[-1])
    total = disagree = 0
    pending = []
    for g in reg["groups"]:
        for r in g["rows"]:
            if r["kind"] != "record":
                continue
            t = str(r.get("says"))
            m = TREE_CLAIM.search(t)
            if not m:
                continue
            total += 1
            own = set(re.findall(r"\b1[5-9]\d{2}\b", t[:m.start()]))
            if m.group(2) in own:
                continue                           # the record agrees with the tree on the year
            disagree += 1
            if r["name"] in UNRESOLVED:
                continue
            if not any(sl in mapped for sl in tree.get(r["name"], [])):
                pending.append((r["name"], m.group(2)))
    return pending, total, disagree


def main():
    pages = glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)
    if not pages:
        print(f"  FAIL  years      no built pages under {DIST} — nothing was examined")
        return 1
    tr = truth()
    if not tr:
        print("  FAIL  years      no person page prints a lifespan in the eyebrow — the markup this "
              "reads has changed, so nothing can be compared")
        return 1
    compared = chart = 0
    bad = collections.defaultdict(set)
    for f in pages:
        page = os.path.relpath(f, DIST).replace(os.sep, "/").replace("/index.html", "") or "/"
        s = read(f)
        # the correction box prints the tree's year on purpose, beside the finding
        s = re.sub(r"Corrected against the family tree.*?Set out in full", "", s, flags=re.S)
        on_chart = bool(CHART_BOX.search(s))
        for m in LINK.finditer(s):
            slug = m.group(1)
            if slug not in tr:
                continue
            inner = re.sub(r"<[^>]+>", " ", m.group(2))
            after = re.sub(r"<[^>]+>", " ", m.group(3))
            mm = re.search(Y, inner) or re.match(r"\s*[·|(\[]?\s*" + Y, after)
            if not mm:
                continue
            compared += 1
            if on_chart:
                chart += 1
            if norm(mm.group(1)) != tr[slug]:
                grp = page if not page.startswith("people/") else "people/*"
                bad[(grp, slug, norm(mm.group(1)), tr[slug])].add(page)
    if compared == 0:
        print("  FAIL  years      no person link followed by a lifespan could be compared — the "
              "markup has changed, or nothing was built, and that is this gate failing and not the "
              "archive passing")
        return 1
    if chart == 0:
        print("  FAIL  years      links were compared but none on a chart — the chart's markup "
              "(ac-d) has changed, so the first place this fault was found is no longer being read")
        return 1
    if bad:
        print(f"  FAIL  years      {len(bad)} place(s) print a lifespan that the linked person's own page contradicts")
        for (grp, slug, shown, page_says), where in sorted(bad.items())[:8]:
            print(f"          /{grp}: {slug} — prints {shown!r}, the page says {page_says!r} ({len(where)} page(s))")
        print("          lib/corrections.js is what the person pages read; whatever prints a lifespan must too.")
        return 1
    prose, n_people, n_needles = stale_prose(pages, tr)
    if n_people == 0 or n_needles == 0:
        print("  FAIL  years      the corrections map yielded no overturned year to look for in prose \u2014 the "
              "map's layout or the data it is read against has changed, so the prose clause examined nothing")
        return 1
    if prose:
        print(f"  FAIL  years      {len(prose)} place(s) in prose print a TREE year the archive has overturned, beside the person's name")
        for page, sl, nd, ctx in prose[:8]:
            print(f"          /{page}: {sl} \u2014 prints the tree's {nd!r}, not the finding")
            print(f"              ...{ctx}...")
        print("          Fix the sentence to say the finding, or word it as the tree's claim.")
        return 1
    pend, n_lines, n_dis = pending_corrections()
    if n_lines == 0:
        print("  FAIL  years      no record line states what the tree says, so the cause clause examined nothing \u2014 "
              "the register's wording or layout has changed")
        return 1
    if pend:
        print(f"  FAIL  years      {len(pend)} record line(s) say the tree is wrong for a person who is NOT in lib/corrections.js")
        for name, yr in pend[:8]:
            print(f"          {name}: the record says the tree's {yr} is wrong, and the person pages still print it")
        print("          Add them to the map, or to UNRESOLVED in this file with the reason.")
        return 1
    print(f"  ok    years      {compared} person link(s) with a lifespan, {chart} of them on a chart, all "
          f"carry the years the linked page carries; in prose, {n_people} corrected people ({n_needles} tree "
          f"value(s)) are printed nowhere as fact; and of {n_lines} record lines that state the tree's year, "
          f"{n_dis} disagree and every one is in the map")
    return 0


if __name__ == "__main__":
    sys.exit(main())

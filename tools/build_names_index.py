#!/usr/bin/env python3
"""Build the two files the kit's build-time name linker (kit/tools/autolink.py) is run with.

    python3 tools/build_names_index.py             # reads the build ARCHIVE_OUT names (default site/dist)
    python3 tools/build_names_index.py --counts    # prints the counts only

18 October 2026. site/public/wholink.js used to turn a person's name in the prose into a link in the
reader's BROWSER, so the served HTML carried almost no person links (no JavaScript, in print, to a crawler).
The kit's autolink.py does the same job once, after the build, in the HTML. It links only what an index lists,
and THE INDEX IS THIS FILE'S ANSWER, reached by the SAME rules as tools/build_mentions.py (whoindex.json) and
graded by the SAME gate (tools/check_whoindex.py): the names come from the built /people/ and /who/ pages, the
pages group a name case-folded with a declared copy (canonical naming another /people/ page) counted as the one
person it copies, and

  people     a name that exactly ONE page bears, and that page is indexable (not noindex)
  ambiguous  a name two or more pages bear and no living person is among them: it goes to
             /people/?q=<name>, never to a guess. At least one of the pages is a /people/ page, because that
             is the list the search address filters
  left out   a name any of whose bearers is noindex (a living person). The kit says "link such a name to the
             search or not at all", and its living list holds the living name, so an ambiguous row for it would
             be refused (exit 2). It is left out: that is the safe half of the kit's choice.
  aliases    only a spelling the archive's own data STATES for that person, listed with the place it is stated in
             site/src/data/names-aliases.json (18 October 2026). Each is a row of its own, {name: the form, url: the page},
             and is written only if (a) the form (case, accents, punctuation folded) is in the record lines of the person's
             own page (person-records.json or dossiers.json, named in "stated_by"), (b) no built page bears the form, so it
             can never shadow a namesake, and (c) the page is indexable. namefold.json folds spellings of a SURNAME for the
             search only and merges nobody, so it is NOT a source of aliases. A name written in capitals ("Hannah SANIGER")
             matches without one: the kit reads a word in capitals as the same word.
  one word   never. A name needs two words (the kit's --min-words 2 as well).
  not a name the page holds in a shape a reader writes: a page title with a digit, a square bracket or a
             question mark in it ("Agnes Isabel Scott?", "Hyland1"), a placeholder (unknown, unnamed, infant,
             "A or B"), a surname alone with a title or a particle ("Dr Dods", "von Schomberg"), one initial and a
             surname ("R. Kent": which Kent?), a surname that is one letter ("Caroline N"), a title that ends in
             punctuation or begins with it,
             and a person whose tree record carries NO surname unless the name is of the form "X of Y" or "X von Y"
             (it is two given names, "Mary Catherine", and a bare given name is never linked). The few pages
             that are not a person at all are listed with the reason in tools/names-index-skip.json.
  case       the kit matches a word written in capitals against the word in capitals' lower form, so the index
             holds a name in the form a reader writes it: a page titled "Alice SUTTON" is indexed as
             "Alice Sutton", and "ALICE SUTTON" and "Alice Sutton" in the prose both match it.

THE LIVING LIST (autolink.py --living) is written OUTSIDE the repository, in ~/.local/state/darcy-archive/,
as living names are never in a tracked file:

  - from the BUILD: the name and address of every /people/ and /who/ page that is noindex. Those pages are
    noindex because the committed data flags the person living (site/src/data/*.json, read by
    site/src/lib/people.js), so this is the part of the list that exists in CI as well;
  - from the PRIVATE FEED, when this machine has it (tools/build_checkprose_feed.py, which asks the kit's
    living_rule.py and so also holds the people HELD OUT of the site, who have no page): their names. In CI
    there is no GEDCOM and no feed, and this says so.

WHAT IT REFUSES (exit 2, counts only, never a name). A name in the index that the feed also holds as a living
or held-out person's: the linker would refuse it anyway, and the right place to find out is here. In CI the
feed is not there, so the same collision could not be seen; it is none today and this gate runs it on every
local build, which is how a new one would be found before it reached CI.

This prints COUNTS ONLY. The index holds dead people's names and public addresses and is not committed
(site/.autolink/ is ignored); the living list is never inside the repository.
"""
import argparse, hashlib, json, os, re, sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outdir
import build_mentions as bm

ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
STATE = os.path.join(os.path.expanduser("~"), ".local", "state", "darcy-archive")
FEED = os.environ.get("CHECKPROSE_FEED") or os.path.join(STATE, "checkprose-feed.json")


def paths(dist):
    """(names index, living list) for one build. The index sits beside the site (ignored), the living list outside the repository."""
    tag = os.path.basename(os.path.normpath(dist))
    idx = os.path.join(SITE, ".autolink", tag, "names-index.json")
    live = os.environ.get("AUTOLINK_LIVING") or os.path.join(
        STATE, "autolink-living-%s.json" % hashlib.sha1(os.path.abspath(dist).encode()).hexdigest()[:10])
    return idx, live


SKIP = os.path.join(HERE, "names-index-skip.json")
TITLES = {"dr", "mr", "mrs", "miss", "ms", "rev", "hon", "lt", "col", "maj", "capt", "sir", "lady", "von", "van",
          "de", "di", "del", "della", "la", "le", "zu", "of", "st", "saint"}
PLACEHOLDER = {"unknown", "unnamed", "infant", "unconfirmed", "living"}
PARTICLES = {"of", "von", "van", "de", "di", "zu"}
SHAPE = re.compile(r"^[^\W\d_(\"][^\W\d_]*(?:[ '’.\-,()\"]+[^\W\d_]+)*[.)\"]?$")


def tree_records():
    """name (folded) -> set of surnames the tree records for it, from the committed data the pages are built from."""
    data = os.path.join(SITE, "src", "data")
    recs = []
    try:
        recs += json.load(open(os.path.join(data, "ancestors.json"), encoding="utf-8"))
        for f in json.load(open(os.path.join(data, "families.json"), encoding="utf-8")):
            recs += f.get("members", [])
        recs += json.load(open(os.path.join(data, "relatives.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for r in recs:
        if isinstance(r, dict) and r.get("name"):
            out.setdefault(bm.fold(r["name"]), set()).add(str(r.get("surname") or "").strip())
    return out


def skipped_names():
    try:
        return {bm.fold(r["name"]) for r in json.load(open(SKIP, encoding="utf-8")) if r.get("name") and r.get("why")}
    except (OSError, ValueError):
        return set()


ALIASES = os.path.join(SITE, "src", "data", "names-aliases.json")


def _sfold(s):
    """Case, accents, apostrophes and every run of punctuation or space folded to one space (for finding a form in a line of text)."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(s).replace("\u2019", "'").casefold())
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).split())


def _stated_text(stated_by):
    """The record lines of the page's own data (person-records.json or dossiers.json), folded, or None."""
    f, key = (stated_by or {}).get("file"), (stated_by or {}).get("key")
    try:
        if f == "person-records":
            e = json.load(open(os.path.join(SITE, "src", "data", "person-records.json"), encoding="utf-8")).get(key)
        elif f == "dossiers":
            e = json.load(open(os.path.join(SITE, "src", "data", "dossiers.json"), encoding="utf-8"))["people"].get(key)
        else:
            return None
    except (OSError, ValueError, KeyError):
        return None
    if not e:
        return None
    return _sfold(" | ".join(r.get("says", "") + " " + r.get("source", "") for r in e.get("rows", [])))


def verified_aliases(pages, groups, path=ALIASES):
    """([(form, url)], held): the aliases of names-aliases.json that pass every test; `held` counts the rest (never named).

    A spelling is an alias of a page only if the archive's own data states it in that page's record lines, no built page bears
    it, the page is built and indexable, and the form is two words or more and listed once."""
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return [], 0
    ok, held, seen = [], 0, set()
    for a in doc.get("aliases", []):
        form, url, why = a.get("form", ""), a.get("url", ""), a.get("stated_by")
        key = bm.fold(form) if isinstance(form, str) else ""
        parts = url.strip("/").split("/") if isinstance(url, str) else []
        page = pages.get((parts[0], parts[1])) if len(parts) == 2 else None
        text = _stated_text(why)
        good = bool(key and len(form.split()) >= 2 and page is not None and not page["noindex"] and not page["dup"]
                    and text is not None and (" " + _sfold(form) + " ") in (" " + text + " ")
                    and key not in groups and key not in seen and (why or {}).get("key") == parts[1])
        if good:
            seen.add(key)
            ok.append((form, url))
        else:
            held += 1
    return ok, held


def linkable(name, surnames):
    """Is this page title a name a reader writes, of a person, with a surname? (see the docstring)"""
    if not SHAPE.match(name) or not re.search(r"[^\W\d_]{2}", name):
        return False
    words = name.replace("’", "'").split()
    low = [w.casefold().strip(".") for w in words]
    if len(words) < 2 or any(w in PLACEHOLDER for w in low) or "or" in [w for w in words]:
        return False
    if len(words) == 2 and low[0] in TITLES:
        return False
    if len(re.sub(r"[^\w]", "", words[-1])) < 2:
        return False
    if len(words) == 2 and len(re.sub(r"[^\w]", "", words[0])) == 1:
        return False                                  # one initial and a surname ("R. Kent"): which Kent?
    if "" in surnames and not (set(low) & PARTICLES):
        return False
    return True


def written_form(names):
    """The form of a name a reader writes: one with no word wholly in capitals if any page has it, else title-cased."""
    allcaps = lambda w: len(re.sub(r"[^A-Za-zÀ-ɏ]", "", w)) >= 2 and w == w.upper()
    plain = sorted(n for n in names if not any(allcaps(w) for w in n.split()))
    if plain:
        return plain[0]
    n = sorted(names)[0]
    return " ".join(w.title() if allcaps(w) else w for w in n.split())


def page_url(kind, slug):
    return "/%s/%s/" % (kind, slug)


def search_url(name):
    return "/people/?q=" + quote(name, safe="")


def index_from_pages(pages):
    """(names index, left-out count, not-a-name count, aliases written, aliases held) from {(kind, slug): {name, noindex, dup}}."""
    groups = bm.name_groups(pages)
    recs, skip = tree_records(), skipped_names()
    people, ambiguous, living_left_out, not_a_name = [], [], 0, 0
    for key, members in groups.items():
        if any(m[3] for m in members):                 # a living (noindex) bearer: not linked at all
            living_left_out += 1
            continue
        shown = written_form({m[2] for m in members})
        if key in skip or not linkable(shown, recs.get(key, set())):
            not_a_name += 1
            continue
        if len(members) == 1:
            kind, slug, _, _ = members[0]
            people.append({"name": shown, "url": page_url(kind, slug)})
        elif any(m[0] == "people" for m in members):
            ambiguous.append({"name": shown, "url": search_url(shown)})
    aliases, aliases_held = verified_aliases(pages, groups)
    people.extend({"name": f, "url": u} for f, u in aliases)
    people.sort(key=lambda r: (r["name"].casefold(), r["url"]))
    ambiguous.sort(key=lambda r: r["name"].casefold())
    return {"people": people, "ambiguous": ambiguous}, living_left_out, not_a_name, len(aliases), aliases_held


def living_from_pages(pages):
    """Names and addresses of every noindex page: the part of the living list the committed data decides."""
    names, urls = set(), set()
    for (kind, slug), e in pages.items():
        if e["noindex"]:
            urls.add(page_url(kind, slug))
            if e["name"]:
                names.add(e["name"])
    return names, urls


def living_from_feed(path=FEED):
    """(names, readable) from the private feed. Counts are all that is ever printed."""
    try:
        d = json.load(open(path, encoding="utf-8"))
        names = set()
        for row in d.get("living", []):
            for n in row.get("names", []):
                if isinstance(n, str) and n.strip():
                    names.add(n.strip())
        return names, True
    except (OSError, ValueError, AttributeError):
        return set(), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", action="store_true", help="print the counts, write nothing")
    ap.add_argument("--dist")
    a = ap.parse_args()
    return main_with(outdir.resolve(a.dist), a.counts)


def main_with(dist, counts_only=False):
    if not os.path.isdir(os.path.join(dist, "people")):
        print("  FAIL  names-index  no built person pages under %s: nothing to index" % dist)
        return 2
    pages = bm.built_pages(dist)
    doc, left_out, not_a_name, n_alias, n_held = index_from_pages(pages)
    ln, lu = living_from_pages(pages)
    feed, have_feed = living_from_feed()
    k = lambda s: bm.fold(s)
    fold_idx = {k(r["name"]) for r in doc["people"] + doc["ambiguous"]}
    clash = len(fold_idx & {k(n) for n in feed})
    if clash:
        print("  FAIL  names-index  %d name(s) in the index are also a living or held-out person's name in the private "
              "feed. The kit's linker would refuse the run (exit 2). Nothing was written; find them with the feed and "
              "leave them out of the index." % clash)
        return 2
    if not doc["people"]:
        print("  FAIL  names-index  the index is empty: a run that examined nothing has not passed")
        return 2
    if n_held:
        print("  FAIL  names-index  %d entr%s of site/src/data/names-aliases.json fail%s a test (the form is not stated in the "
              "record lines it names, a built page bears it, the page is not built or indexable, or it is listed twice). The "
              "file lists only spellings meant to be live: fix or remove the entry." % (n_held, "y" if n_held == 1 else "ies", "s" if n_held == 1 else ""))
        return 2
    idx_path, live_path = paths(dist)
    summary = ("%d people (%d of them stated spellings of a page's person), %d shared names sent to the search; left out: %d names a "
               "living person bears, %d page titles that are not a name a reader writes, %d stated spellings that failed a test; "
               "living list: %d names and %d addresses from the build%s"
               % (len(doc["people"]), n_alias, len(doc["ambiguous"]), left_out, not_a_name, n_held, len(ln), len(lu),
                  (", plus %d names from the private feed" % len(feed)) if have_feed
                  else ", and NO private feed on this machine (the committed living flags alone, as in CI)"))
    if counts_only:
        print("  ..    names-index  " + summary)
        return 0
    os.makedirs(os.path.dirname(idx_path), exist_ok=True)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=0)
    os.makedirs(os.path.dirname(live_path), exist_ok=True)
    fd = os.open(live_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"names": sorted(ln | feed), "urls": sorted(lu)}, f, ensure_ascii=False)
    print("  ok    names-index  " + summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())

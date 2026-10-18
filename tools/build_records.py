#!/usr/bin/env python3
"""The records table: every record a narrative page may link to, from the data this archive already holds.

    python3 tools/build_records.py            # writes site/src/data/records.json
    python3 tools/build_records.py --check    # exits 1 if the committed file is not what the data gives (CI runs this)

18 October 2026, for the linking standard's L3 (kit/docs/linking-standard.md): a passage that quotes a record links to it, and the
link is the kit's <Rec> (site/src/components/Rec.astro) or, in a data file's string, the markup [the words](rec:ID) (site/src/lib/md.js),
both reading THIS table. The words the author wrote become the link; nothing is reworded.

WHERE A ROW COMES FROM. Never from a guess: an address is in the register already, or follows by a rule from a locator the pages print.

  1. register.json, record rows with a DEEP address (about 45 distinct): an archive.org book or volume, a Trove article, a TNA
     Discovery entry, a Queensland State Archives item, a Gazette page, an archive-department ark. Not the front doors of a paid
     index (FindMyPast, FreeREG, the Queensland BDM index...), which the register holds for 300 rows and which are not records.
     Left out on purpose: Find a Grave (a memorial of someone buried within living memory), a FamilySearch tree person (other
     people's tree, not a record), a downloadable scan (QSA image DR38490), and any row whose line says it is NOT published on this
     site (a police file of 1922, ITM86903): those are held, and a row that is held is never in this table.
  2. The Trove locators the narrative pages print (nla.news-article<N>, nla.news-page<N>): https://nla.gov.au/<locator> is Trove's own
     permalink, the form the register already uses for the six it holds.
  3. The National Archives references the narrative pages print (WO 12/8483, PROB 11/1825/326, E 179/114/240...): Discovery's
     search for the reference, https://discovery.nationalarchives.gov.uk/results/r?_q=<reference>. The address CARRIES THE RECORD'S OWN
     REFERENCE and is labelled a catalogue search (kind "catalogue-search"): it is not the record's page, it is the catalogue's answer to
     its reference. Where the register holds the entry's own page (PROB 11/1728/64, ADM 101/26/1) that address wins.
  4. A few archive.org identifiers a page prints itself (STATED below), each checked against the page's own text.

NOT HERE: Gloucestershire Archives, Hertfordshire Archives, the National Library of Wales, the Berkeley Castle Muniments, local
registers, the Queensland BDM index and NAA items. Their references are printed on the pages and the archive holds no public address
for them, so a passage that cites only those stays plain and counted (or carries its reasoned exemption), and no address is invented.
"""
import json, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "site", "src", "data")
PAGES = os.path.join(ROOT, "site", "src", "pages")
OUT = os.path.join(DATA, "records.json")

# the twelve narrative pages' own files: the page and the data file it renders
NARRATIVE = {
    "saniger-place": ["saniger-place.json"], "swonhungre": ["swonhungre.json"], "joseph-darcy": ["joseph-darcy.json"],
    "sneyds": ["sneyds.json"], "behind-the-paywall": ["fmp.json"], "hornby": [], "the-corps": ["the-corps.json"],
    "hannah-baptism": ["hannah-baptism.json"], "sanigers": ["sanigers.json"], "sneyd": [], "great-war": [], "sergeant-sneyd": [],
}
TNA_RE = re.compile(r"\b(?:WO|IR|PROB|HO|ADM|RG|CP|E)\s?\d{1,3}\b(?:/[\w.-]+)*")
TROVE_RE = re.compile(r"nla\.news-(?:article|page)\d+")
# identifiers a page prints itself: id -> (what it is, the page that prints it)
STATED = {"berkeleymanuscri03smyt": ("John Smyth, The Berkeley Manuscripts, vol. 3 (1885), full text", "saniger-place")}
LEFT_OUT_HOSTS = ("www.findagrave.com",)
LEFT_OUT_PATHS = ("/tree/person/", "/api/download_file/")


def narrative_text():
    out = {}
    for p, datafiles in NARRATIVE.items():
        t = open(os.path.join(PAGES, p + ".astro"), encoding="utf-8").read()
        for f in datafiles:
            t += "\n" + open(os.path.join(DATA, f), encoding="utf-8").read()
        out[p] = t
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def tna_norm(ref):
    """'HO107/347' and 'HO 107/347.' are one reference: letters, a space, then the number and the rest."""
    r = ref.strip().rstrip(".").strip()
    m = re.match(r"^([A-Z]{1,4})\s?(\d.*)$", r)
    return "%s %s" % (m.group(1), m.group(2)) if m else r


def label_of(source):
    s = re.sub(r"^record\s*[·.]\s*", "", source).strip()
    return s[:150]


def rows():
    reg = json.load(open(os.path.join(DATA, "register.json"), encoding="utf-8"))
    table, byurl = [], {}

    def add(row):
        table.append(row)

    # 1. register deep addresses ----------------------------------------------------------------------------------
    for g in reg["groups"]:
        for r in g["rows"]:
            if r.get("kind") != "record" or not r.get("link"):
                continue
            u = r["link"]
            pu = urllib.parse.urlparse(u)
            if not pu.scheme.startswith("http") or pu.path.strip("/") == "" or pu.netloc in LEFT_OUT_HOSTS \
                    or any(x in u for x in LEFT_OUT_PATHS) or u.startswith("https://archive.org/search") or "search-newspapers" in u:
                continue
            if "NOT published on this site" in r["says"]:
                continue                                                # held: never in the table
            if u in byurl:
                continue
            host = pu.netloc
            if host == "archive.org" and pu.path.startswith("/details/"):
                ident = pu.path.split("/details/")[1].strip("/")
                row = {"id": "ia-" + ident, "url": u, "label": label_of(r["source"]), "kind": "book"}
            elif host == "nla.gov.au":
                loc = pu.path.strip("/")
                row = {"id": "trove-" + loc.replace("nla.news-", ""), "url": u, "label": "Trove: " + loc, "kind": "newspaper", "key": [loc]}
            elif host == "discovery.nationalarchives.gov.uk" and "/details/r/" in u:
                m = TNA_RE.search(r["source"])
                ref = tna_norm(m.group(0)) if m else None
                row = {"id": ("tna-" + slug(ref)) if ref else "tna-" + pu.path.rsplit("/", 1)[1].lower(), "url": u,
                       "label": "The National Archives, " + (ref or "catalogue entry") + " (the entry's own page)", "kind": "catalogue-entry"}
                if ref:
                    row["key"] = [ref]
            elif host == "www.archivessearch.qld.gov.au" and "/items/" in u:
                itm = pu.path.rsplit("/", 1)[1]
                row = {"id": "qsa-" + itm.lower(), "url": u, "label": "Queensland State Archives " + itm, "kind": "archive-item", "key": [itm]}
            elif host == "www.thegazette.co.uk" and "/page/" in u:
                m = re.search(r"/issue/(\d+)/page/(\d+)", u)
                row = {"id": "gazette-%s-p%s" % m.groups(), "url": u, "label": "The London Gazette, issue %s, page %s" % m.groups(), "kind": "gazette"}
            else:
                continue                                                # an ark or a county site: not cited by the narratives
            byurl[u] = row
            add(row)

    ids = {r["id"] for r in table}
    haveref = {fold_ref(k) for r in table for k in r.get("key", [])}
    text = narrative_text()
    alltext = "\n".join(text.values())

    # 2. Trove locators the pages print ---------------------------------------------------------------------------
    for loc in sorted(set(TROVE_RE.findall(alltext))):
        if loc in haveref:
            continue
        rid = "trove-" + loc.replace("nla.news-", "")
        if rid in ids:
            continue
        ids.add(rid)
        add({"id": rid, "url": "https://nla.gov.au/" + loc, "label": "Trove: " + loc, "kind": "newspaper", "key": [loc]})
        haveref.add(loc)

    # 3. National Archives references the pages print -> Discovery's search for the reference -----------------------
    spell = {}
    for m in TNA_RE.finditer(alltext):
        spell.setdefault(tna_norm(m.group(0)), set()).add(m.group(0).rstrip(".").strip())
    for ref in sorted(spell):
        if fold_ref(ref) in haveref:
            continue
        rid = "tna-" + slug(ref)
        if rid in ids:
            continue
        ids.add(rid)
        add({"id": rid, "url": "https://discovery.nationalarchives.gov.uk/results/r?_q=" + urllib.parse.quote(ref, safe=""),
             "label": "The National Archives, Discovery: search for %s (the catalogue's answer to the reference, not the record's own page)" % ref,
             "kind": "catalogue-search", "key": sorted(spell[ref] | {ref})})

    # 4. identifiers a page prints itself -------------------------------------------------------------------------
    for ident, (what, page) in STATED.items():
        if ident not in text[page]:
            continue
        rid = "ia-" + ident
        if rid not in ids:
            ids.add(rid)
            add({"id": rid, "url": "https://archive.org/details/" + ident, "label": what, "kind": "book"})

    table.sort(key=lambda r: (r["kind"], r["id"]))
    return table


def fold_ref(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main(argv):
    doc = {"_note": "Generated by tools/build_records.py from register.json and the references the narrative pages print; do not edit. "
                    "Where each row comes from is in that file's docstring. A row flagged living or hold would never be drawn; none is here.",
           "records": rows()}
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if "--check" in argv:
        try:
            cur = open(OUT, encoding="utf-8").read()
        except OSError:
            cur = ""
        if cur != text:
            print("  FAIL  records   site/src/data/records.json is not what tools/build_records.py gives from the data: run it and commit the result")
            return 1
        print("  ok    records   records.json is what the data gives (%d row(s))" % len(doc["records"]))
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    kinds = {}
    for r in doc["records"]:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("records: %d row(s) %s" % (len(doc["records"]), kinds))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Holds every record link on the narrative pages to the records table and to the words it wraps.

    python3 tools/check_records.py             # from the repository (npm run check:records, first in the build)

The linking standard's L3 makes a passage that quotes a record carry a link to it. A link to the WRONG record is worse than none, and
the gate that counts links cannot tell. This reads the SOURCES (it runs before the build):

  * site/src/data/records.json is what tools/build_records.py gives from the data (--check);
  * every <Rec id="..."> or act="..." in site/src/pages names a row, and every [words](rec:ID) in a data file names a row;
  * the row is not held out (living / hold): the kit's Rec and src/lib/md.js would draw nothing there, and the author's words with it;
  * WHERE THE WORDS ARE A REFERENCE (a National Archives reference, a Trove locator, a Queensland item number), they ARE the row's
    reference: <Rec id="tna-wo-47">WO 54</Rec> is refused. Words that describe the record ("Bigland's monuments") are not held to this,
    only to the row existing: the row's label says what it is.

It prints counts. It reads source files only.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "site", "src")
REC = re.compile(r"<Rec\b([^>]*)>(.*?)</Rec>", re.S)
ATTR = re.compile(r'\b(id|act)="([^"]*)"')
MD = re.compile(r"\[([^\]\n]+)\]\(rec:([A-Za-z0-9_.\-]+)\)")
REFWORDS = re.compile(r"^(?:(?:WO|IR|PROB|HO|ADM|RG|CP|E)\s?\d{1,3}\b(?:/[\w.-]+)*\.?|nla\.news-(?:article|page)\d+|ITM\d+)$")


def fold(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main():
    bad = []
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_records.py"), "--check"], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        bad.append("build_records.py --check failed")
    rows = {x["id"]: x for x in json.load(open(os.path.join(SRC, "data", "records.json"), encoding="utf-8"))["records"]}
    bykey = {}
    for x in rows.values():
        for k in x.get("key", []):
            bykey[fold(k)] = x
    uses = {}
    n = 0

    def judge(where, ident, act, words):
        nonlocal n
        n += 1
        row = rows.get(ident) if ident is not None else bykey.get(fold(act or ""))
        if row is None:
            bad.append("%s: record %r is not in the records table" % (where, ident or act))
            return
        if row.get("living") or row.get("hold"):
            bad.append("%s: record %s is held out: it would draw nothing" % (where, row["id"]))
            return
        uses[row["id"]] = uses.get(row["id"], 0) + 1
        plain = re.sub(r"<[^>]+>|\{[^}]*\}|\*\*|\*", "", words).strip()
        if REFWORDS.match(plain):
            keys = {fold(k) for k in row.get("key", [])}
            if keys and fold(plain) not in keys:
                bad.append("%s: the words %r are a reference, and record %s is %s" % (where, plain, row["id"], sorted(keys)[:2]))

    for root, _d, files in os.walk(os.path.join(SRC, "pages")):
        for fn in files:
            if not fn.endswith(".astro"):
                continue
            path = os.path.join(root, fn)
            where = os.path.relpath(path, ROOT)
            for m in REC.finditer(open(path, encoding="utf-8").read()):
                attrs, words = m.group(1), m.group(2)
                a = dict(ATTR.findall(attrs))
                if ("id=" in attrs and "id" not in a) or ("act=" in attrs and "act" not in a):
                    continue                                  # an expression: the build checks it
                judge(where, a.get("id"), a.get("act"), words)
            for m in MD.finditer(open(path, encoding="utf-8").read()):
                judge(where, m.group(2), None, m.group(1))
    for fn in sorted(os.listdir(os.path.join(SRC, "data"))):
        if fn.endswith(".json") and fn != "records.json":
            txt = open(os.path.join(SRC, "data", fn), encoding="utf-8").read()
            for m in MD.finditer(txt):
                judge("site/src/data/" + fn, m.group(2), None, m.group(1))
    print("check_records: %d record link(s) read, %d distinct record(s); %d problem(s)" % (n, len(uses), len(bad)))
    for b in bad:
        print("  FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

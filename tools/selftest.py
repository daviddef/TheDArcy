#!/usr/bin/env python3
"""End-to-end self-test: the code, the data, and every page the build produced.

WHY THIS EXISTS. This archive has gates — check_controls, check_links,
checkliving, checkarchive, checkcovers — and they are good ones, but they are
gates on specific promises. It had no test that simply asks whether the whole
thing is sound: whether every tool still compiles, whether every data file is
what it claims to be, and whether any of the 875 published pages is showing a
reader something no reader should see.

It is not a unit-test suite. There is no unit-test framework in this project,
and pretending otherwise would be the sort of claim this archive exists to
refuse. It is an integration test over the built site plus a static check of
the source that produced it.

    python3 tools/selftest.py            # check everything, report, exit 1 on failure
    python3 tools/selftest.py --warn     # report but always exit 0

Sections:
  CODE    every tool compiles; no tool has a duplicate function definition
  DATA    every JSON parses; NO DUPLICATE KEYS — json.load silently keeps the
          last, which is exactly how hannah-saniger lost half her links from a
          JavaScript object literal on 20 September 2026
  PAGES   every built page has a lang, a title, exactly one h1, and none of the
          tells of a rendering failure: literal "undefined", "NaN",
          "[object Object]", unrendered **markdown**, or a leaked {expression}
"""
import ast, json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
DATA = os.path.join(ROOT, "site", "src", "data")
DIST = os.path.join(ROOT, "site", "dist")

fails, warns = [], []
def fail(sec, what): fails.append((sec, what))
def warn(sec, what): warns.append((sec, what))


# ── CODE ────────────────────────────────────────────────────────────────────
def check_code():
    n = 0
    for f in sorted(os.listdir(TOOLS)):
        if not f.endswith(".py"):
            continue
        n += 1
        p = os.path.join(TOOLS, f)
        src = open(p, encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=f)
        except SyntaxError as e:
            fail("CODE", f"{f}: syntax error line {e.lineno}: {e.msg}")
            continue
        # a second def of the same name at module level silently replaces the first
        seen = collections.Counter(
            node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        for name, c in seen.items():
            if c > 1:
                fail("CODE", f"{f}: {name}() defined {c} times at module level — the later wins silently")
    return f"{n} python tool(s) compile"


# ── DATA ────────────────────────────────────────────────────────────────────
def dup_keys(pairs):
    """json object_pairs_hook that reports repeats instead of dropping them."""
    seen, out = set(), {}
    for k, v in pairs:
        if k in seen:
            dup_keys.found.append(k)
        seen.add(k)
        out[k] = v
    return out


def check_data():
    n = 0
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".json"):
            continue
        n += 1
        p = os.path.join(DATA, f)
        dup_keys.found = []
        try:
            json.load(open(p, encoding="utf-8"), object_pairs_hook=dup_keys)
        except Exception as e:
            fail("DATA", f"{f}: will not parse — {e}")
            continue
        for k in sorted(set(dup_keys.found)):
            fail("DATA", f"{f}: DUPLICATE KEY {k!r} — json keeps the last and drops the rest")
    # the public indexes the browser fetches at runtime
    pub = os.path.join(ROOT, "site", "public")
    for f in ("searchindex.json", "whoindex.json"):
        p = os.path.join(pub, f)
        if not os.path.exists(p):
            warn("DATA", f"public/{f} is missing — search or name-linking will be dead in the browser")
            continue
        n += 1
        try:
            json.load(open(p, encoding="utf-8"))
        except Exception as e:
            fail("DATA", f"public/{f}: will not parse — {e}")
    return f"{n} json file(s) parse, no duplicate keys"


# ── PAGES ───────────────────────────────────────────────────────────────────
TELLS = [
    (re.compile(r">\s*undefined\s*<"), "renders the word “undefined”"),
    (re.compile(r">\s*NaN\s*<"), "renders NaN"),
    (re.compile(r"\[object Object\]"), "renders [object Object]"),
    (re.compile(r"\*\*[^*\n]{3,80}\*\*"), "shows unrendered **markdown**"),
    (re.compile(r">\s*\{[a-zA-Z_$][\w.$]*\}\s*<"), "leaked an unrendered {expression}"),
]
SCRIPTS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def check_pages():
    # A floor, because "ok, 0 pages checked" is not a pass.
    #
    # This test reported exactly that on 20 September: a build had been killed
    # part-way, dist existed but was empty, and every page check passed
    # vacuously. The archive's own rule — a control that cannot fail is not a
    # control — caught it, but only after it had printed ok.
    FLOOR = 400
    if not os.path.isdir(DIST):
        fail("PAGES", "site/dist does not exist — nothing was built")
        return "no build to check"
    n = 0
    for r, _, fs in os.walk(DIST):
        for f in fs:
            if not f.endswith(".html"):
                continue
            n += 1
            path = "/" + os.path.relpath(os.path.join(r, f), DIST).replace(os.sep, "/")
            raw = open(os.path.join(r, f), encoding="utf-8", errors="ignore").read()
            # Astro writes a redirect as a bare stub: a title, a refresh meta and
            # one link. It has no lang and no h1 on purpose, and checking it for
            # either is checking the wrong kind of document.
            if 'http-equiv="refresh"' in raw and len(raw) < 1200:
                continue
            body = SCRIPTS.sub(" ", raw)
            if not re.search(r"<html[^>]*\slang=", raw):
                fail("PAGES", f"{path}: <html> has no lang attribute")
            t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S)
            if not t or not t.group(1).strip():
                fail("PAGES", f"{path}: empty or missing <title>")
            h1 = len(re.findall(r"<h1[\s>]", body))
            if h1 == 0:
                warn("PAGES", f"{path}: no <h1>")
            elif h1 > 1:
                warn("PAGES", f"{path}: {h1} <h1> elements")
            for rx, why in TELLS:
                m = rx.search(body)
                if m:
                    fail("PAGES", f"{path}: {why} — {m.group(0)[:60]!r}")
    if n < FLOOR:
        fail("PAGES", f"only {n} pages in site/dist, expected at least {FLOOR} — "
                      f"the build did not finish, so these checks mean nothing")
    return f"{n} built page(s) checked"


def main():
    warn_only = "--warn" in sys.argv
    for name, fn in (("CODE", check_code), ("DATA", check_data), ("PAGES", check_pages)):
        summary = fn()
        bad = [x for x in fails if x[0] == name]
        print(f"  {'ok  ' if not bad else 'FAIL'}  {name:7} {summary}")
    for sec, what in fails[:40]:
        print(f"   FAIL {sec:6} {what}")
    if len(fails) > 40:
        print(f"   … and {len(fails) - 40} more failures")
    for sec, what in warns[:15]:
        print(f"   warn {sec:6} {what}")
    if len(warns) > 15:
        print(f"   … and {len(warns) - 15} more warnings")
    print(f"  selftest: {len(fails)} failure(s), {len(warns)} warning(s)")
    return 0 if (warn_only or not fails) else 1


if __name__ == "__main__":
    sys.exit(main())

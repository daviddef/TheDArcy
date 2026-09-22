#!/usr/bin/env python3
"""A page may not write the living rule out for itself.

On 22 September a page was added to this repository that rendered every member
of families.json and suppressed only their dates and places. It published
FORTY-FOUR living people. The gate caught it and its author removed them within
the hour, and then found a second fault under the first: seven living SPOUSES
named on dead people's rows, where the row itself was legitimate and the leak
was in who else it mentioned.

The cause was not carelessness. The rule existed only as a line of presentation
code, written out separately in each page that needed it —

    const shown = f.members.filter((m) => !m.living);

— four times in this archive, and the fifth page inherited none of them. A rule
that lives in a template is a rule the next template cannot know about.

So it is `publishable()` in src/lib/people.js now, beside the policy it applies,
and this refuses any page that goes back to writing its own. It does not stop
a page reading families.json — that is ordinary — it stops a page deciding for
itself what living means.

    python3 tools/check_living_rule.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "..", "site", "src", "pages")
LIB = os.path.join(HERE, "..", "site", "src", "lib", "people.js")
DECL = os.path.join(HERE, "..", "site", "src", "data", "living-rule.json")

# A hand-rolled test on the `living` flag, anywhere outside people.js.
OWN_FILTER = re.compile(r"(!\s*\w+\.living|\.living\s*===?\s*false|\w+\.living\s*\?)")
# Reading .members at all, which is what makes the filter necessary.
READS_MEMBERS = re.compile(r"\.members\b")


def main():
    if not os.path.exists(LIB) or "export const publishable" not in open(LIB, encoding="utf-8").read():
        print("  FAIL  livingrule  src/lib/people.js does not export publishable() — "
              "the rule has no home, so nothing below can be enforced")
        return 1

    declared, why = set(), {}
    if os.path.exists(DECL):
        for e in json.load(open(DECL, encoding="utf-8")).get("allow", []):
            declared.add(e["page"].replace("\\", "/"))
            why[e["page"].replace("\\", "/")] = e.get("why", "")
        missing = [p for p in declared if not os.path.exists(os.path.join(HERE, "..", p))]
        for m in missing:
            print(f"  FAIL  livingrule  living-rule.json declares {m!r} and that page "
                  f"does not exist — a permission outliving its subject")
        if missing:
            return 1

    bad = []
    reads = 0
    for r, _, fs in os.walk(PAGES):
        for f in fs:
            if not f.endswith(".astro"):
                continue
            p = os.path.join(r, f)
            src = open(p, encoding="utf-8", errors="ignore").read()
            # the frontmatter is where the decision gets made
            head = src.split("---")[1] if src.count("---") >= 2 else src
            code = "\n".join(l for l in head.splitlines()
                             if not l.strip().startswith(("*", "/*", "//")))
            if READS_MEMBERS.search(code):
                reads += 1
            m = OWN_FILTER.search(code)
            if m:
                rel = os.path.relpath(p, os.path.join(HERE, "..")).replace("\\", "/")
                if rel not in declared:
                    bad.append((rel, m.group(0)))

    for rel, hit in bad:
        print(f"  FAIL  livingrule  {rel} decides for itself what living means "
              f"({hit!r}). Use publishable() or nameIfPublishable() from "
              f"src/lib/people.js — the rule is a value there, with the policy "
              f"it applies written beside it")
    if bad:
        print(f"  FAIL  livingrule  {len(bad)} page(s) carry their own copy of the living rule")
        return 1

    print(f"  ok    livingrule  {reads} page(s) read family members; none writes its "
          f"own living filter, and {len(declared)} direct read(s) are declared with a reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())

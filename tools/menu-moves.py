#!/usr/bin/env python3
"""Every entry of the header menu, old build against new: where each address stood and where it stands now (12 November 2026, the menu regroup).
    python3 scripts/menu-moves.py BEFORE_DIST AFTER_DIST [OUT.md]
Reads the <nav class="topnav"> of the home page of each build. Exit 1 if an address that was in the menu is in no menu now and is not
listed in DROPPED below with its reason."""
import re, sys, html

# an address that left the menu on purpose, and why
DROPPED = {
    "/families/blackbourne/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/cotton/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/howard/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/jones/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/kent/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/noel/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/schomberg/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/stuart/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/sutton/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/von-degenfeld/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/von-der-pfalz/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/families/ward/": "left the Families menu on 13 November 2026 (PR D); linked from the /families/ index (its card and its \"all N published\" link) and the menu links the index",
    "/tree/": "left the People menu on 23 November 2026 (estate clean-up); listed on the /drawn/ hub with a line on what it shows, and the menu links the hub",
    "/trees/": "left the People menu on 23 November 2026 (estate clean-up); listed on the /drawn/ hub with a line on what it shows, and the menu links the hub",
    "/timeline/": "left the People menu on 23 November 2026 (estate clean-up); listed on the /drawn/ hub with a line on what it shows, and the menu links the hub",
    "/bloodline/": "left the People menu on 23 November 2026 (estate clean-up); listed on the /drawn/ hub with a line on what it shows, and the menu links the hub",
    "/roots/": "Roots & Routes was retired on 23 November 2026 (David); the address redirects to /tree/ and is not in the sitemap",
    "/sergeant-sneyd/": "left the Places & families menu on 23 November 2026 (four named families at most); linked from the /families/ index, Pages of their own, and the menu links the index as All the families",
    "/robert-family/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/the-corps/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/obituary/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/joseph-darcy/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/margaret-jones/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/constantine/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/sussex-sisters/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/george-pitt/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/chatham/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/portsea/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/hannah-baptism/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/berkeley-woman/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/thomas-sinegar/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/berkeley/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/sanigers/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/saniger-place/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/saniger-1608/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/chew-magna/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/wakefields/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/drivers-fields/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/bristol-chapels/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/sneyds/": "left the header menu on 23 November 2026 (The studies, 24 links, became one entry); listed on the /studies/ hub with its blurb, and the menu links the hub",
    "/papers/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
    "/inquest-1902/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
    "/finding-arthur/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
    "/behind-the-paywall/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
    "/crossread/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
    "/dna/": "left the Research menu on 23 November 2026 (the Deep dives sub-group became the one entry The studies); listed on the /studies/ hub, the Sources page and /research/",
}


def menu(dist):
    t = open(dist + "/index.html", encoding="utf-8").read()
    nav = t[t.index('<nav class="topnav"'):]
    nav = nav[:nav.index("</nav>")]
    out = []   # (menu, group-or-sub, href, label)
    for m in re.finditer(r'<details class="menu">(.*?)</details>', nav, re.S):
        body = m.group(1)
        label = html.unescape(re.search(r"<summary>(.*?)</summary>", body, re.S).group(1))
        grp = ""
        for tok in re.finditer(r'<(?:div class="pg"|a [^>]*href="([^"]+)"[^>]*>(.*?)</a>|span class="ps[^"]*">(.*?)</span>)', body, re.S):
            if tok.group(0).startswith('<div class="pg"'):
                grp = ""
            elif tok.group(3) is not None:
                grp = html.unescape(tok.group(3))
            else:
                href, txt = tok.group(1), html.unescape(re.sub(r"<[^>]+>", "", tok.group(2)))
                if "ph" in tok.group(0)[:40]:
                    grp = txt
                    out.append((label, grp, href, txt + "  (group heading)"))
                else:
                    out.append((label, grp, href, txt))
    return out


def main():
    b, a = menu(sys.argv[1]), menu(sys.argv[2])
    bh = {}
    for m, g, h, l in b:
        bh.setdefault(h, []).append((m, g, l))
    ah = {}
    for m, g, h, l in a:
        ah.setdefault(h, []).append((m, g, l))
    L = ["# The menu, before and after", "", "| address | was | now |", "|---|---|---|"]
    bad = 0
    for h in list(dict.fromkeys([x[2] for x in b] + [x[2] for x in a])):
        was = "; ".join("%s%s: %s" % (m, " / " + g if g else "", l) for m, g, l in bh.get(h, [])) or "—"
        now = "; ".join("%s%s: %s" % (m, " / " + g if g else "", l) for m, g, l in ah.get(h, [])) or "—"
        if h in bh and h not in ah and h not in DROPPED:
            now = "**not in the menu**"
            bad += 1
        if was != now:
            L.append("| `%s` | %s | %s |" % (h, was, now))
    L += ["", "%d address(es) were in the menu and are in none now without a stated reason." % bad]
    out = "\n".join(L) + "\n"
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(out)
    print(out)
    sys.exit(1 if bad else 0)


main()

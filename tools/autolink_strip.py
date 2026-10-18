"""Read a built page as it read before the build-time name linker ran, and before its citations were links.

18 October 2026. The kit's autolink.py (run by tools/autolink_pass.py inside `npm run build`) wraps a name in
<a href=".." data-autolink>..</a>, and tools/autolink_pass.py wraps a person's own name on their own page in
<span data-no-autolink>..</span>. Neither adds or removes a word. But the tools here that make text out of a built
page (build_mentions.py -> mentions.json, build_search.py -> searchindex.json) turn every tag into a space, so
"Samuel Sneyd's" would become "Samuel Sneyd 's" and a committed file would change because of a pass that changed
nothing a reader reads. They take the wrappers off first, keeping the text.

The same holds for the record links of the linking standard (the kit's Rec, or [words](rec:ID) through src/lib/md.js, which draw
<a class="lk-rec" data-rec data-cite>words</a>): the words were already there, in one text node, and a link around them must not turn
"HO107/347, book 6" into "HO107/347 , book 6" in a snippet. They come off with the others. So does the kit's Rec component's own <style> (the .rec-fig rules): build_search.py turns every tag into
a space and keeps the text of a <style>, so the first page to use Rec would otherwise gain 300 characters of CSS in its search text.

THE "AT THE TIME" NOTES (kit/docs/era-notes.md; 18 October 2026) ARE NOT TEXT EITHER. A note beside a dated place on a person's page ("Britain and its colonies
per the Record Atlas") is context the kit draws from a committed snapshot, not a word of the archive's own, and the kit's EraNote component draws its
<style data-era-css> from the first note on a page. Both come off whole, text included, so mentions.json, whoindex.json and the search text are what they
were before the notes (build_search.py would keep a <style>'s CSS as text, as it would a Rec's).
"""
import re

_LINK = re.compile(r"<a\b[^>]*\bdata-autolink\b[^>]*>(.*?)</a>", re.S | re.I)
_REC = re.compile(r"<a\b[^>]*\bdata-rec=[^>]*\bdata-cite\b[^>]*>(.*?)</a>", re.S | re.I)
_RECSTYLE = re.compile(r"<style>\s*\.rec-fig\[[^<]*</style>", re.I)
_ERA_STYLE = re.compile(r"<style\b[^>]*\bdata-era-css\b[^>]*>.*?</style>", re.S | re.I)
# <span class="era-note" ...><span class="era-pre">..</span><span class="era-lab">..</span> <a class="era-src" ..>..</a></span>: the inner elements hold text only
_ERA_NOTE = re.compile(r'<span\b[^>]*\bclass="era-note"[^>]*>(?:<span\b[^>]*>[^<]*</span>|<a\b[^>]*>[^<]*</a>|\s+)*</span>', re.I)
_KEEP = re.compile(r"<span\b[^>]*\bdata-no-autolink\b[^>]*>(.*?)</span>", re.S | re.I)


def plain(raw):
    """`raw` page HTML without the wrappers the linker added (the text inside them stays)."""
    return _ERA_NOTE.sub("", _ERA_STYLE.sub("", _RECSTYLE.sub("", _KEEP.sub(r"\1", _REC.sub(r"\1", _LINK.sub(r"\1", raw))))))

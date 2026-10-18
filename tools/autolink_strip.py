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
"""
import re

_LINK = re.compile(r"<a\b[^>]*\bdata-autolink\b[^>]*>(.*?)</a>", re.S | re.I)
_REC = re.compile(r"<a\b[^>]*\bdata-rec=[^>]*\bdata-cite\b[^>]*>(.*?)</a>", re.S | re.I)
_RECSTYLE = re.compile(r"<style>\s*\.rec-fig\[[^<]*</style>", re.I)
_KEEP = re.compile(r"<span\b[^>]*\bdata-no-autolink\b[^>]*>(.*?)</span>", re.S | re.I)


def plain(raw):
    """`raw` page HTML without the wrappers the linker added (the text inside them stays)."""
    return _RECSTYLE.sub("", _KEEP.sub(r"\1", _REC.sub(r"\1", _LINK.sub(r"\1", raw))))

"""Read a built page as it read before the build-time name linker ran.

18 October 2026. The kit's autolink.py (run by tools/autolink_pass.py inside `npm run build`) wraps a name in
<a href=".." data-autolink>..</a>, and tools/autolink_pass.py wraps a person's own name on their own page in
<span data-no-autolink>..</span>. Neither adds or removes a word. But the tools here that make text out of a built
page (build_mentions.py -> mentions.json, build_search.py -> searchindex.json) turn every tag into a space, so
"Samuel Sneyd's" would become "Samuel Sneyd 's" and a committed file would change because of a pass that changed
nothing a reader reads. They take the wrappers off first, keeping the text.
"""
import re

_LINK = re.compile(r"<a\b[^>]*\bdata-autolink\b[^>]*>(.*?)</a>", re.S | re.I)
_KEEP = re.compile(r"<span\b[^>]*\bdata-no-autolink\b[^>]*>(.*?)</span>", re.S | re.I)


def plain(raw):
    """`raw` page HTML without the wrappers the linker added (the text inside them stays)."""
    return _KEEP.sub(r"\1", _LINK.sub(r"\1", raw))

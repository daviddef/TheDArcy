/* Turn every known person's name in the page text into a link to their page.
   Runs after render, touches text nodes only, never re-links inside an existing
   anchor, and matches longest names first so "Arthur William Hartley Sneyd"
   beats "Arthur Sneyd".

   Only people who are actually written about somewhere are in the index, so a
   name that appears solely in a list does not become a link.

   whoindex.json rows are [name, slug, count, kind, n]. kind "p" links to
   /people/<slug>/, "w" to /who/<slug>/ (a witness or an official), and "a" is a
   name n >= 2 people bear: it links to the search at /people/?q=<name> and never
   to one of them. Rows of three fields (an older index) are all kind "p".
   Matching ignores case ("Hannah SANIGER" matches "Hannah Saniger"), and a name
   is linked at its FIRST mention in each section of a page, not twice per page. */
(function () {
  var BASE = (document.documentElement.getAttribute("data-base") || "").replace(/\/+$/, "");
  fetch(BASE + "/whoindex.json").then(function (r) { return r.json(); }).then(function (idx) {
    if (!idx || !idx.length) return;
    var here = location.pathname.replace(/\/$/, "");
    var map = Object.create(null), parts = [];
    for (var i = 0; i < idx.length; i++) {
      var n = idx[i][0];
      var k = idx[i][3] || "p";
      if (k !== "a" && here.endsWith((k === "w" ? "/who/" : "/people/") + idx[i][1])) continue;   // don't self-link
      map[n.toLowerCase()] = idx[i];
      parts.push(n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    }
    if (!parts.length) return;

    var L = "A-Za-z\\u00C0-\\u024F";
    var re;
    try {
      re = new RegExp("(?<![" + L + "])(" + parts.join("|") + ")(?![" + L + "])", "g");
    } catch (e) {
      return;   // no lookbehind on this engine: leave the prose alone
    }

    var main = document.querySelector("main") || document.body;
    var walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || node.nodeValue.length < 5) return NodeFilter.FILTER_REJECT;
        var p = node.parentElement;
        while (p && p !== main) {
          var t = p.tagName;
          /* Never touch anything inside an SVG: an HTML <a> injected into an
             SVG <text> is not laid out by the SVG renderer, so the label
             measures zero and silently disappears from the chart. SVG tag
             names are lower-case, so the checks below never catch it. */
          if (p.ownerSVGElement || t === "svg" || t === "SVG") return NodeFilter.FILTER_REJECT;
          if (t === "A" || t === "CODE" || t === "PRE" || t === "SCRIPT" || t === "STYLE" ||
              t === "H1" || t === "TITLE" || p.classList.contains("noauto"))
            return NodeFilter.FILTER_REJECT;
          p = p.parentElement;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);

    /* First mention per section: one name is linked once in each <section>, so a
       long page links it again where a reader may have jumped in, and a short
       one is not peppered. Text outside any section counts as one section. */
    var secs = [], seen = Object.create(null);
    for (var j = 0; j < nodes.length; j++) {
      var node = nodes[j], text = node.nodeValue, linked = 0;
      re.lastIndex = 0;
      if (!re.test(text)) continue;
      re.lastIndex = 0;
      var frag = document.createDocumentFragment(), last = 0, m;
      var sec = node.parentElement.closest("section") || main;
      var si = secs.indexOf(sec);
      if (si < 0) si = secs.push(sec) - 1;
      while ((m = re.exec(text))) {
        var row = map[m[1].toLowerCase()];
        if (!row) continue;
        var key = si + "|" + m[1].toLowerCase();
        if (seen[key]) continue;             // first mention in this section only
        seen[key] = 1;
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var a = document.createElement("a");
        var kind = row[3] || "p";
        a.className = "wholink";
        if (kind === "a") {
          a.href = BASE + "/people/?q=" + encodeURIComponent(m[1]);
          a.title = row[4] + " people of this name \u2014 see them in the list";
        } else {
          a.href = BASE + (kind === "w" ? "/who/" : "/people/") + row[1] + "/";
          a.title = row[0] + " \u2014 written about on " + row[2] + " page" + (row[2] === 1 ? "" : "s") + " of this archive";
        }
        a.textContent = m[1];
        frag.appendChild(a);
        last = m.index + m[1].length;
        linked++;
      }
      if (!linked) continue;
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  }).catch(function () {});
})();

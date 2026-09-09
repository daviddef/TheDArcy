/* Turn every known person's name in the page text into a link to their page.
   Runs after render, touches text nodes only, never re-links inside an existing
   anchor, and matches longest names first so "Arthur William Hartley Sneyd"
   beats "Arthur Sneyd".

   Only people who are actually written about somewhere are in the index, so a
   name that appears solely in a list does not become a link. */
(function () {
  var BASE = (document.documentElement.getAttribute("data-base") || "").replace(/\/+$/, "");
  fetch(BASE + "/whoindex.json").then(function (r) { return r.json(); }).then(function (idx) {
    if (!idx || !idx.length) return;
    var here = location.pathname.replace(/\/$/, "");
    var map = Object.create(null), parts = [];
    for (var i = 0; i < idx.length; i++) {
      var n = idx[i][0];
      if (here.endsWith("/people/" + idx[i][1])) continue;   // don't self-link
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

    var seen = Object.create(null);
    for (var j = 0; j < nodes.length; j++) {
      var node = nodes[j], text = node.nodeValue, linked = 0;
      re.lastIndex = 0;
      if (!re.test(text)) continue;
      re.lastIndex = 0;
      var frag = document.createDocumentFragment(), last = 0, m;
      while ((m = re.exec(text))) {
        var row = map[m[1].toLowerCase()];
        if (!row) continue;
        seen[row[1]] = (seen[row[1]] || 0) + 1;
        if (seen[row[1]] > 2) continue;      // at most twice per page
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var a = document.createElement("a");
        a.href = BASE + "/people/" + row[1] + "/";
        a.className = "wholink";
        a.title = row[0] + " — written about on " + row[2] + " page" + (row[2] === 1 ? "" : "s") + " of this archive";
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

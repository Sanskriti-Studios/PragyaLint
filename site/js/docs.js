/* Injects the docs sidebar navigation (grouped, collapsible on mobile) and
 * a Previous/Next pager at the bottom of each page, based on that page's
 * position in the flattened PRAGYALINT_DOCS_NAV order. No per-page config
 * needed -- the pager just follows the sidebar. */
(function () {
  "use strict";

  var SECTIONS = window.PRAGYALINT_DOCS_NAV || [];
  var FLAT = [];
  SECTIONS.forEach(function (sec) {
    sec.items.forEach(function (item) { FLAT.push(item); });
  });

  var p = location.pathname;

  function isActive(href) {
    var full = "/" + href;
    return (
      p === full ||
      p === full.replace(/\/$/, "/index.html") ||
      p.endsWith(full) ||
      p.endsWith(full.replace(/\/$/, "/index.html"))
    );
  }

  function renderAside() {
    var aside = document.getElementById("docs-aside");
    if (!aside) return;
    var html =
      '<button class="docs-aside-toggle" id="docs-aside-toggle" aria-expanded="false">' +
      '<span><i class="fa-solid fa-bars"></i> Browse docs</span>' +
      '<i class="fa-solid fa-chevron-down"></i></button>' +
      '<div class="docs-aside-body" id="docs-aside-body">';
    SECTIONS.forEach(function (sec) {
      html += "<h4>" + sec.label + "</h4>";
      sec.items.forEach(function (item) {
        var active = isActive(item.href);
        html +=
          '<a href="' + item.href + '"' +
          (active ? ' class="active"' : "") +
          "><i class=\"" + item.icon + "\"></i><span>" + item.label + "</span></a>";
      });
    });
    html += "</div>";
    aside.innerHTML = html;

    var toggle = document.getElementById("docs-aside-toggle");
    var body = document.getElementById("docs-aside-body");
    if (toggle && body) {
      toggle.addEventListener("click", function () {
        var open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!open));
        body.classList.toggle("open", !open);
      });
    }
  }

  function renderPager() {
    var target = document.getElementById("docs-pager");
    if (!target) return;

    var idx = -1;
    for (var i = 0; i < FLAT.length; i++) {
      if (isActive(FLAT[i].href)) { idx = i; break; }
    }
    if (idx === -1) return;

    var prev = idx > 0 ? FLAT[idx - 1] : null;
    var next = idx < FLAT.length - 1 ? FLAT[idx + 1] : null;

    function side(item, dir) {
      if (!item) return '<span class="pager-btn pager-btn-empty"></span>';
      var arrow = dir === "prev"
        ? '<i class="fa-solid fa-arrow-left pager-arrow"></i>'
        : '<i class="fa-solid fa-arrow-right pager-arrow"></i>';
      var label = dir === "prev" ? "Previous" : "Next";
      var textBlock =
        '<span class="pager-text"><span class="pager-label">' + label + '</span>' +
        '<span class="pager-title">' + item.label + "</span></span>";
      return (
        '<a class="pager-btn pager-btn-' + dir + '" href="' + item.href + '">' +
        (dir === "prev" ? arrow + textBlock : textBlock + arrow) +
        "</a>"
      );
    }

    target.innerHTML = side(prev, "prev") + side(next, "next");
  }

  renderAside();
  renderPager();
})();
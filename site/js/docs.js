/* Injects the docs sidebar navigation (grouped, collapsible on mobile) and,
 * when a page has <div id="docs-next"></div>, a grid of big button cards
 * linking to a curated set of "next step" pages instead of plain text links.
 * Both read from the single PRAGYALINT_DOCS_NAV source in docs-nav.js. */
(function () {
  "use strict";

  var SECTIONS = window.PRAGYALINT_DOCS_NAV || [];
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

  function renderNextSteps() {
    var target = document.getElementById("docs-next");
    if (!target) return;
    var grid = target.querySelector(".next-grid");
    if (!grid) return;
    var keys = (target.getAttribute("data-pages") || "")
      .split(",")
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
    if (!keys.length) return;

    var all = [];
    SECTIONS.forEach(function (sec) {
      sec.items.forEach(function (item) { all.push(item); });
    });

    var html = "";
    keys.forEach(function (key) {
      var item = all.filter(function (i) { return i.href === "docs/" + key; })[0];
      if (!item) return;
      html +=
        '<a class="next-btn" href="' + item.href.replace(/^docs\//, "") + '">' +
        '<i class="' + item.icon + '"></i>' +
        '<span class="next-btn-label">' + item.label + "</span>" +
        '<span class="next-btn-desc">' + item.desc + "</span>" +
        '<i class="fa-solid fa-arrow-right next-btn-arrow"></i>' +
        "</a>";
    });
    grid.innerHTML = html;
  }

  renderAside();
  renderNextSteps();
})();
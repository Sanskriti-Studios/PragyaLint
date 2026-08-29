/* Injects the docs sidebar navigation. */
(function () {
  "use strict";
  var aside = document.getElementById("docs-aside");
  if (!aside) return;

  var SECTIONS = [
    { label: "Guides", items: [
      { href: "docs/", label: "Getting started" },
      { href: "docs/install.html", label: "Installation" },
      { href: "docs/config.html", label: "Configuration" },
      { href: "docs/fixes.html", label: "Fixes" },
      { href: "docs/faq.html", label: "FAQ" },
    ] },
  ];

  var html = "";
  // location.pathname is the real path regardless of <base>; match by tail.
  var p = location.pathname;
  SECTIONS.forEach(function (sec) {
    html += "<h4>" + sec.label + "</h4>";
    sec.items.forEach(function (item) {
      var full = "/" + item.href;
      var active = p === full || p === full.replace(/\/$/, "/index.html") || p.endsWith(full) || p.endsWith(full.replace(/\/$/, "/index.html"));
      html +=
        '<a href="' +
        item.href +
        '"' +
        (active ? ' class="active"' : "") +
        ">" +
        item.label +
        "</a>";
    });
  });
  aside.innerHTML = html;
})();

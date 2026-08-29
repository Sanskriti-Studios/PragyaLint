/* Injects the docs sidebar navigation. */
(function () {
  "use strict";
  var aside = document.getElementById("docs-aside");
  if (!aside) return;

  var SECTIONS = [
    { label: "Guides", items: [
      { href: "/docs/", label: "Getting started" },
      { href: "/docs/install.html", label: "Installation" },
      { href: "/docs/config.html", label: "Configuration" },
      { href: "/docs/fixes.html", label: "Fixes" },
      { href: "/docs/faq.html", label: "FAQ" },
    ] },
  ];

  var html = "";
  SECTIONS.forEach(function (sec) {
    html += "<h4>" + sec.label + "</h4>";
    sec.items.forEach(function (item) {
      var active =
        location.pathname === item.href ||
        (item.href === "/docs/" && location.pathname === "/docs/");
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

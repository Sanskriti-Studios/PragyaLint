/* Shared layout: injects the nav bar and footer into each page. */
(function () {
  "use strict";

  // Compact gear-and-chain brand mark — matches the animated logo page.
  function brandSvg() {
    return (
      '<svg viewBox="0 0 48 32" fill="none" aria-hidden="true">' +
      '<circle cx="16" cy="16" r="7.5" fill="currentColor"/>' +
      '<circle cx="16" cy="16" r="11.5" stroke="currentColor" stroke-width="2" fill="none"/>' +
      '<circle cx="38" cy="16" r="5.5" fill="currentColor"/>' +
      '<circle cx="38" cy="16" r="8.5" stroke="currentColor" stroke-width="2" fill="none"/>' +
      '<path d="M27.5 7.5 L29.5 7.5 M27.5 24.5 L29.5 24.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
      '<circle cx="16" cy="16" r="3" fill="var(--bg)" stroke="currentColor" stroke-width="1.5"/>' +
      '<circle cx="38" cy="16" r="2.2" fill="var(--bg)" stroke="currentColor" stroke-width="1.5"/>' +
      '<path d="M11 8 L21 24 M21 8 L11 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.55"/>' +
      "</svg>"
    );
  }

  // Right-side icon-only links. Font Awesome classes drive the glyphs.
  var ICONS = [
    { href: "/docs/", fa: "fa-solid fa-book", label: "Docs", title: "Documentation" },
    { href: "https://github.com/Sanskriti-Studios/PragyaLint", fa: "fa-brands fa-github", label: "GitHub", title: "GitHub repository", external: true },
    { href: "https://pypi.org/project/pragyalint/", fa: "fa-brands fa-python", label: "PyPI", title: "PyPI package", external: true },
    { href: "https://marketplace.visualstudio.com/items?itemName=abhinu.pragyalint", fa: "fa-brands fa-vscode", label: "VS Code", title: "VS Code extension", external: true },
  ];

  function injectNav() {
    var navPlaceholder = document.getElementById("nav");
    if (!navPlaceholder) return;
    var activeHref = location.pathname;
    var links = ICONS.map(function (item) {
      var active = activeHref === item.href || (item.href !== "/" && activeHref.indexOf(item.href) === 0);
      return (
        '<a href="' + item.href + '"' +
        (item.external ? ' target="_blank" rel="noopener"' : "") +
        (active ? ' class="active"' : "") +
        ' title="' + item.title + '"' +
        ' aria-label="' + item.label + '">' +
        '<i class="' + item.fa + '"></i>' +
        "</a>"
      );
    }).join("");

    navPlaceholder.outerHTML =
      '<header class="nav"><div class="nav-inner">' +
      '<a class="brand" href="/">' + brandSvg() + "<span>PragyaLint</span></a>" +
      '<nav class="nav-links">' +
      links +
      '<button class="theme-toggle" aria-label="Toggle theme"></button>' +
      "</nav>" +
      "</div></header>";
  }

  function injectFooter() {
    var foot = document.getElementById("footer");
    if (!foot) return;
    foot.outerHTML =
      '<footer class="footer"><div class="footer-inner">' +
      "<span>&copy; 2026 PragyaLint — GPL-3.0-or-later</span>" +
      '<span class="footer-icons">' +
      '<a href="/docs/" aria-label="Docs" title="Docs"><i class="fa-solid fa-book"></i></a>' +
      '<a href="https://github.com/Sanskriti-Studios/PragyaLint" target="_blank" rel="noopener" aria-label="GitHub" title="GitHub"><i class="fa-brands fa-github"></i></a>' +
      '<a href="https://pypi.org/project/pragyalint/" target="_blank" rel="noopener" aria-label="PyPI" title="PyPI"><i class="fa-brands fa-python"></i></a>' +
      '<a href="https://marketplace.visualstudio.com/items?itemName=abhinu.pragyalint" target="_blank" rel="noopener" aria-label="VS Code" title="VS Code"><i class="fa-brands fa-vscode"></i></a>' +
      "</span>" +
      "</div></footer>";
  }

  injectNav();
  injectFooter();
})();

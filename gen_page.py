#!/usr/bin/env python3
"""Doc-page generator for the PragyaLint static site.

Renders a doc page from a shared shell (head, nav, aside, footer, script
includes) plus a body fragment. Uses simple token replacement rather than
str.format so body code samples can contain { } freely.

The shared <head> carries the full SEO set: canonical URL, robots meta,
Open Graph, Twitter cards, and JSON-LD structured data. Pages also register
themselves here so the sitemap and robots.txt stay in sync automatically.

Usage (see write_pages.py):
    from gen_page import write
    write(path, title, description, body)
    write_sitemap()   # once all pages are written
    write_robots()
"""

import datetime
import html
import json

SITE_NAME = "PragyaLint"
SITE_BASE = "https://prgl.ic3cool.int.yt"
OG_IMAGE = SITE_BASE + "/og-image.png"
PAGES = []

TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>__TITLE__ — PragyaLint Docs</title>
    <meta
      name="description"
      content="__DESCRIPTION__"
    />
    <link rel="canonical" href="__CANONICAL__" />
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />
    <meta name="theme-color" content="#0d0b1e" />

    <!-- Open Graph -->
    <meta property="og:site_name" content="PragyaLint" />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="en_US" />
    <meta property="og:title" content="__OG_TITLE__" />
    <meta property="og:description" content="__DESCRIPTION__" />
    <meta property="og:url" content="__CANONICAL__" />
    <meta property="og:image" content="__OG_IMAGE__" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="PragyaLint — dead-code analyzer for Python" />

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="__OG_TITLE__" />
    <meta name="twitter:description" content="__DESCRIPTION__" />
    <meta name="twitter:image" content="__OG_IMAGE__" />

    <!-- Structured data -->
    <script type="application/ld+json">
__JSONLD__
    </script>

    <script>
      (function () {
        var p = location.pathname;
        var root;
        var di = p.indexOf("/docs/");
        if (di !== -1) {
          root = p.slice(0, di + 1);
        } else {
          var last = p.lastIndexOf("/");
          root = last <= 0 ? "/" : p.slice(0, last + 1);
        }
        var b = document.createElement("base");
        b.href = root;
        document.head.insertBefore(b, document.head.firstChild);
      })();
    </script>

<link rel="icon" href="favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="css/style.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" />
  </head>
  <body>
    <div id="nav"></div>

    <div class="container docs">
      <aside class="docs-aside" id="docs-aside"></aside>
      <div class="docs-content">
__BODY__
        <div class="docs-pager" id="docs-pager"></div>
      </div>
    </div>

    <div id="footer"></div>

    <script src="js/layout.js"></script>
    <script src="js/docs-nav.js"></script>
    <script src="js/docs.js"></script>
    <script src="js/main.js"></script>
  </body>
</html>
"""


def _jsonld(title, description, canonical):
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": canonical,
            "inLanguage": "en",
            "isPartOf": {
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": SITE_BASE + "/",
            },
        },
        indent=2,
    )


def _page_url(path):
    rel = path
    if rel.startswith("site/"):
        rel = rel[len("site/") :]
    if rel.endswith(".html"):
        rel = rel[: -len(".html")]
    if rel == "index":
        return "/"
    return "/" + rel + ".html" if rel else "/"


def write(path, title, description, body):
    url = _page_url(path)
    canonical = SITE_BASE + url
    og_title = f"{title} — PragyaLint Docs"
    content = TEMPLATE
    content = content.replace("__TITLE__", html.escape(title))
    content = content.replace("__DESCRIPTION__", html.escape(description))
    content = content.replace("__CANONICAL__", canonical)
    content = content.replace("__OG_TITLE__", html.escape(og_title))
    content = content.replace("__OG_IMAGE__", OG_IMAGE)
    content = content.replace("__JSONLD__", _jsonld(title, description, canonical))
    content = content.replace("__BODY__", body.rstrip("\n"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    PAGES.append({"title": title, "url": url})
    print("wrote", path)


def write_sitemap():
    lastmod = datetime.date.today().isoformat()
    entries = [{"url": "/", "title": "Home", "freq": "weekly", "priority": "1.0"}]
    entries += [
        {"url": p["url"], "title": p["title"], "freq": "monthly", "priority": "0.8"}
        for p in PAGES
    ]
    urls = []
    for e in entries:
        urls.append(
            "  <url>"
            f"<loc>{SITE_BASE}{e['url']}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>{e['freq']}</changefreq>"
            f"<priority>{e['priority']}</priority>"
            "</url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    with open("site/sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write(xml)
    print("wrote", "site/sitemap.xml")


def write_robots():
    text = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_BASE}/sitemap.xml\n"
    )
    with open("site/robots.txt", "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote", "site/robots.txt")
#!/usr/bin/env python3
"""Doc-page generator for the PragyaLint static site.

Renders a doc page from a shared shell (head, nav, aside, footer, script
includes) plus a body fragment. Uses simple token replacement rather than
str.format so body code samples can contain { } freely.

Usage (see write_pages.py):
    from gen_page import write
    write(path, title, description, body)
"""

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


def write(path, title, description, body):
    content = TEMPLATE
    content = content.replace("__TITLE__", title)
    content = content.replace("__DESCRIPTION__", description)
    content = content.replace("__BODY__", body.rstrip("\n"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", path)
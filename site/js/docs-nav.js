/* Docs information architecture: grouped sections + subcategories, shared
 * by the sidebar (js/docs.js) and the "next steps" button grid at the
 * bottom of each doc page. Single source of truth so both stay in sync. */
(function (global) {
  "use strict";

  var DOCS_NAV = [
    {
      label: "Start here",
      items: [
        { href: "docs/", label: "Getting started", icon: "fa-solid fa-flag-checkered", desc: "Install PragyaLint and run your first scan." },
        { href: "docs/install.html", label: "Installation", icon: "fa-solid fa-download", desc: "pip, pipx, uv, and CI-image installs." },
        { href: "docs/why.html", label: "Why PragyaLint", icon: "fa-solid fa-star", desc: "How it differs from vulture, ruff --select F401, pyflakes." },
        { href: "docs/how-it-works.html", label: "How it works", icon: "fa-solid fa-diagram-project", desc: "Module graph, reachability, and confidence levels." },
      ],
    },
    {
      label: "Core concepts",
      items: [
        { href: "docs/entry-files.html", label: "Entry files", icon: "fa-solid fa-door-open", desc: "Conventional entries, --entry, and test-file discovery." },
        { href: "docs/analysis.html", label: "Analysis rules", icon: "fa-solid fa-magnifying-glass", desc: "unused_file, unused_import, unused_export, unused_local." },
        { href: "docs/confidence.html", label: "Confidence levels", icon: "fa-solid fa-gauge-high", desc: "HIGH / MEDIUM / LOW, and what gates auto-fixing." },
        { href: "docs/dynamic-dispatch.html", label: "Dynamic dispatch", icon: "fa-solid fa-shuffle", desc: "getattr, dispatch tables, exec/eval — and how PragyaLint stays safe." },
      ],
    },
    {
      label: "Using it",
      items: [
        { href: "docs/cli-commands.html", label: "CLI commands", icon: "fa-solid fa-terminal", desc: "Every flag: --fix, --dry-run, --confidence, --force, --json." },
        { href: "docs/config.html", label: "Configuration", icon: "fa-solid fa-sliders", desc: "pyproject.toml, .pragyalint.toml, and precedence." },
        { href: "docs/fixes.html", label: "Fixes & --fix", icon: "fa-solid fa-wrench", desc: "What each fix target does, and how to preview safely." },
        { href: "docs/reports.html", label: "Reports", icon: "fa-solid fa-file-lines", desc: "Terminal, JSON, and SARIF output formats." },
        { href: "docs/cache.html", label: "Cache", icon: "fa-solid fa-database", desc: "How re-scans get faster, and how to bust the cache." },
      ],
    },
    {
      label: "Integrations",
      items: [
        { href: "docs/integrations.html", label: "Overview", icon: "fa-solid fa-plug", desc: "Editors, CI, and pre-commit at a glance." },
        { href: "docs/automation.html", label: "CI / automation", icon: "fa-solid fa-robot", desc: "GitHub Actions, GitLab CI, pre-commit hooks." },
        { href: "docs/plugins.html", label: "Plugins", icon: "fa-solid fa-puzzle-piece", desc: "Custom finders and reporter hooks." },
        { href: "docs/vscode.html", label: "VS Code extension", icon: "fa-solid fa-code", desc: "Inline diagnostics as you type." },
      ],
    },
    {
      label: "Reference",
      items: [
        { href: "docs/errors.html", label: "Errors & troubleshooting", icon: "fa-solid fa-triangle-exclamation", desc: "ENOENT, parse errors, exit codes, and fixes." },
        { href: "docs/faq.html", label: "FAQ", icon: "fa-solid fa-circle-question", desc: "Common questions, answered briefly." },
        { href: "docs/api.html", label: "Python API", icon: "fa-solid fa-code-branch", desc: "Use PragyaLint as a library: analyze(), apply_fixes()." },
      ],
    },
    {
      label: "Project",
      items: [
        { href: "docs/contributing.html", label: "Contributing", icon: "fa-solid fa-handshake", desc: "Dev setup, running tests, opening a PR." },
        { href: "docs/source.html", label: "Source & releases", icon: "fa-brands fa-git-alt", desc: "Repo layout, changelog, and versioning." },
      ],
    },
  ];

  global.PRAGYALINT_DOCS_NAV = DOCS_NAV;
})(window);

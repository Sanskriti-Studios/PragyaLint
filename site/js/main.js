/* PragyaLint site — theme, nav, copy, demo */
(function () {
  "use strict";

  /* ---------- Theme: follow system, allow manual override, persist ---------- */
  var THEME_KEY = "pragyalint-theme";
  var root = document.documentElement;
  var media = window.matchMedia("(prefers-color-scheme: dark)");

  function applyTheme(theme) {
    if (theme === "dark" || theme === "light") {
      root.setAttribute("data-theme", theme);
    } else {
      root.setAttribute("data-theme", media.matches ? "dark" : "light");
    }
    syncToggleIcon();
  }

  function currentTheme() {
    var stored = localStorage.getItem(THEME_KEY);
    if (stored === "dark" || stored === "light") return stored;
    return media.matches ? "dark" : "light";
  }

  function syncToggleIcon() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    btn.innerHTML =
      currentTheme() === "dark"
        ? '<i class="fa-solid fa-sun"></i>'
        : '<i class="fa-solid fa-moon"></i>';
    btn.setAttribute("aria-label", "Toggle color theme");
  }

  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    });
  }

  // Follow the system unless the user has explicitly chosen.
  media.addEventListener("change", function () {
    if (!localStorage.getItem(THEME_KEY)) applyTheme(null);
  });

  applyTheme(null);

  /* ---------- Mobile nav ---------- */
  var burger = document.querySelector(".burger");
  var links = document.querySelector(".nav-links");
  if (burger && links) {
    burger.addEventListener("click", function () {
      links.classList.toggle("open");
    });
  }

  /* ---------- Copy code buttons ---------- */
  document.querySelectorAll("pre").forEach(function (pre) {
    var btn = document.createElement("button");
    btn.className = "copy";
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      var text = pre.innerText;
      navigator.clipboard
        .writeText(text)
        .then(function () {
          btn.textContent = "Copied!";
          setTimeout(function () {
            btn.textContent = "Copy";
          }, 1600);
        })
        .catch(function () {
          btn.textContent = "Error";
        });
    });
    pre.appendChild(btn);
  });

  /* ---------- Active nav link ---------- */
  var path = location.pathname;
  document.querySelectorAll(".nav-links a").forEach(function (a) {
    var href = a.getAttribute("href") || "";
    if (path.endsWith(href) || (href === "/" && (path.endsWith("/") || path.endsWith("index.html")))) {
      a.classList.add("active");
    }
  });

  /* ---------- Docs sidebar active state ---------- */
  document.querySelectorAll(".docs-aside a").forEach(function (a) {
    if (path.endsWith(a.getAttribute("href") || "")) a.classList.add("active");
  });

  /* ---------- Interactive terminal demo ---------- */
  var demoPanels = {
    scan: {
      title: "pragyalint scan",
      lines: [
        { cls: "", text: "$ pragyalint" },
        { cls: "c", text: "" },
        { cls: "", text: "./src/orphan.py" },
        {
          cls: "hi",
          text:
            "  \u2716 [HIGH]   module 'orphan' is not reachable from any entry point",
        },
        { cls: "", text: "./src/utils/helper.py" },
        {
          cls: "me",
          text:
            "  \u26A0 [MEDIUM] export 'legacy_fn' of module 'utils.helper' is never imported",
        },
        { cls: "", text: "./src/app.py" },
        {
          cls: "hi",
          text: "  \u2716 [HIGH]   import 'os' is never used",
        },
        { cls: "c", text: "" },
        {
          cls: "",
          text: "3 findings in 12 files (11 reachable).",
        },
        {
          cls: "ac",
          text: "  \u2713 2 safe to remove  \u2022  1 needs review",
        },
      ],
    },
    fix: {
      title: "pragyalint --fix",
      lines: [
        { cls: "", text: "$ pragyalint --fix --dry-run" },
        { cls: "c", text: "" },
        {
          cls: "",
          text: "  [dry-run] Would: delete ./src/orphan.py",
        },
        {
          cls: "",
          text: "  [dry-run] Would: remove unused imports in ./src/app.py",
        },
        { cls: "c", text: "" },
        { cls: "", text: "$ pragyalint --fix" },
        { cls: "ac", text: "  [fixed]   delete ./src/orphan.py" },
        { cls: "ac", text: "  [fixed]   remove unused imports in ./src/app.py" },
        { cls: "c", text: "" },
        { cls: "", text: "$ pragyalint" },
        { cls: "ac", text: "  No dead code found. \u2728 clean" },
      ],
    },
    ci: {
      title: "pragyalint --fail-on high",
      lines: [
        { cls: "", text: "# .github/workflows/quality.yml" },
        { cls: "c", text: "steps:" },
        { cls: "", text: "  - run: pip install pragyalint" },
        { cls: "", text: "  - run: pragyalint --fail-on high" },
        { cls: "c", text: "    # exits non-zero when HIGH dead code is found" },
        { cls: "c", text: "" },
        { cls: "", text: "$ pragyalint --json" },
        {
          cls: "",
          text:
            '  { "rule": "unused_file", "confidence": "high", ... }',
        },
        {
          cls: "",
          text: "$ pragyalint --sarif > pragyalint.sarif",
        },
        { cls: "ac", text: "  \u2713 SARIF ready for GitHub Code Scanning" },
      ],
    },
  };

  var body = document.querySelector(".demo-body");
  var runEl = document.querySelector(".demo-run");
  var tabs = document.querySelectorAll(".demo-tabs button");

  function renderDemo(key) {
    var panel = demoPanels[key];
    if (!panel || !body) return;
    tabs.forEach(function (t) {
      t.classList.toggle("active", t.dataset.panel === key);
    });
    body.innerHTML =
      panel.lines
        .map(function (l) {
          return l.cls ? '<span class="' + l.cls + '">' + l.text + "</span>" : l.text;
        })
        .join("\n");
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      renderDemo(t.dataset.panel);
    });
  });

  if (body) renderDemo("scan");

  /* ---------- Rich animations ---------- */

  // Floating background icons (gear strategy: faint FA icons drifting).
  function spawnIcons() {
    var hero = document.querySelector(".hero");
    if (!hero || document.querySelector(".bg-icons")) return;
    var wrap = document.createElement("div");
    wrap.className = "bg-icons";
    var glyphs = [
      "fa-solid fa-gear fa-spin",
      "fa-solid fa-code",
      "fa-solid fa-bug-slash",
      "fa-solid fa-scissors",
      "fa-solid fa-code-branch",
      "fa-solid fa-terminal",
      "fa-solid fa-gears fa-spin",
    ];
    for (var i = 0; i < 14; i++) {
      var ic = document.createElement("i");
      var g = glyphs[i % glyphs.length];
      var cls = g.replace(" fa-spin", "");
      ic.className = cls;
      if (g.indexOf("fa-spin") >= 0) ic.classList.add("fa-spin");
      var size = 14 + Math.floor(Math.random() * 30);
      ic.style.fontSize = size + "px";
      ic.style.left = (Math.random() * 100).toFixed(2) + "%";
      ic.style.top = (Math.random() * 100).toFixed(2) + "%";
      ic.style.animationDelay = (Math.random() * 8).toFixed(2) + "s";
      ic.style.animationDuration = (9 + Math.random() * 10).toFixed(2) + "s";
      wrap.appendChild(ic);
    }
    hero.appendChild(wrap);
  }

  // Scroll reveal: elements with [data-reveal] fade/slide in.
  function initReveal() {
    var els = document.querySelectorAll("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (e) {
        e.classList.add("revealed");
      });
      return;
    }
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add("revealed");
            obs.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach(function (e) {
      obs.observe(e);
    });
  }

  // Animated count-up for elements with [data-count].
  function initCounters() {
    var els = document.querySelectorAll("[data-count]");
    if (!els.length) return;
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          obs.unobserve(el);
          var target = parseFloat(el.getAttribute("data-count"));
          var suffix = el.getAttribute("data-suffix") || "";
          var dur = 1200;
          var start = null;
          function tick(ts) {
            if (!start) start = ts;
            var p = Math.min((ts - start) / dur, 1);
            p = 1 - Math.pow(1 - p, 3); // ease-out cubic
            el.textContent = Math.round(target * p) + suffix;
            if (p < 1) requestAnimationFrame(tick);
            else el.textContent = target + suffix;
          }
          requestAnimationFrame(tick);
        });
      },
      { threshold: 0.4 }
    );
    els.forEach(function (e) {
      obs.observe(e);
    });
  }

  // Tilt cards slightly toward the mouse.
  function initTilt() {
    if (!window.matchMedia("(hover:hover)").matches) return;
    document.querySelectorAll(".card.tilt").forEach(function (card) {
      card.addEventListener("mousemove", function (ev) {
        var r = card.getBoundingClientRect();
        var dx = (ev.clientX - r.left) / r.width - 0.5;
        var dy = (ev.clientY - r.top) / r.height - 0.5;
        card.style.transform =
          "perspective(700px) rotateY(" + dx * 6 + "deg) rotateX(" + -dy * 6 + "deg) translateY(-4px)";
      });
      card.addEventListener("mouseleave", function () {
        card.style.transform = "";
      });
    });
  }

  spawnIcons();
  initReveal();
  initCounters();
  initTilt();
})();
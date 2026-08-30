/* Fetches live-ish project stats (GitHub stars/last-updated, PyPI version)
 * for any element with [data-live-stats]. Fails silently and leaves the
 * static fallback text in place if the network/API call doesn't work
 * (e.g. offline docs, GitHub API rate limit) — never blocks rendering. */
(function () {
  "use strict";

  var GH_REPO = "Sanskriti-Studios/PragyaLint";
  var PYPI_PKG = "pragyalint";

  function timeAgo(iso) {
    var diffMs = Date.now() - new Date(iso).getTime();
    var days = Math.floor(diffMs / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "1 day ago";
    if (days < 30) return days + " days ago";
    var months = Math.floor(days / 30);
    if (months < 12) return months + (months === 1 ? " month ago" : " months ago");
    var years = Math.floor(months / 12);
    return years + (years === 1 ? " year ago" : " years ago");
  }

  function setBadge(key, html) {
    var els = document.querySelectorAll('[data-live-stats="' + key + '"]');
    els.forEach(function (el) {
      el.innerHTML = html;
    });
  }

  function loadGithub() {
    fetch("https://api.github.com/repos/" + GH_REPO)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        setBadge("gh-stars", '<i class="fa-solid fa-star"></i> <strong>' + data.stargazers_count + "</strong> <span class=\"dim\">stars</span>");
        setBadge("gh-updated", '<i class="fa-brands fa-github"></i> Updated <strong>' + timeAgo(data.pushed_at) + "</strong>");
      })
      .catch(function () { /* leave static fallback in the markup */ });
  }

  function loadPypi() {
    fetch("https://pypi.org/pypi/" + PYPI_PKG + "/json")
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        var v = data.info && data.info.version;
        var releases = data.releases && data.releases[v];
        var uploaded = releases && releases[0] && releases[0].upload_time_iso_8601;
        setBadge(
          "pypi-version",
          '<i class="fa-brands fa-python"></i> PyPI <strong>v' + v + "</strong>" +
            (uploaded ? ' <span class="dim">· ' + timeAgo(uploaded) + "</span>" : "")
        );
      })
      .catch(function () { /* leave static fallback in the markup */ });
  }

  if (document.querySelector("[data-live-stats]")) {
    loadGithub();
    loadPypi();
  }
})();
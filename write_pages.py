import sys
sys.path.insert(0, ".")
from gen_page import write

D = "site/docs"

# ---------------------------------------------------------------- why.html
write(f"{D}/why.html", "Why PragyaLint", "Why use PragyaLint over vulture, ruff's unused-import checks, or pyflakes for dead-code detection in Python.", '''
        <h1>Why PragyaLint</h1>
        <p class="lead">
          Dead-code detection for Python isn't new. Here's specifically what
          PragyaLint does differently from the tools you may already have.
        </p>

        <h2 id="reachability">Reachability, not per-file heuristics</h2>
        <p>
          Tools like <code>ruff --select F401</code> or <code>pyflakes</code> catch
          unused imports <em>within a file</em>, but they don't know whether the
          file itself is ever imported by anything. <code>vulture</code> goes
          further with a whole-project scan, but reports a confidence
          <em>percentage</em> derived from name-usage heuristics rather than an
          actual reachability proof.
        </p>
        <p>
          PragyaLint builds a real module graph from your
          <a href="entry-files.html">entry points</a> and asks a structural
          question: can anything reach this module by following imports? If
          not, it's HIGH-confidence dead — not a percentage, a fact about your
          import graph.
        </p>

        <h2 id="dynamic">Dynamic-dispatch aware by default</h2>
        <p>
          Interpreters, plugin systems, and command-dispatch code call functions
          by name at runtime — <code>getattr(obj, name)</code>, a
          <code>{"cmd": handler}</code> table, <code>exec</code>/<code>eval</code>.
          None of that is a plain name reference, so most static analyzers either
          miss it (false negative — they report nothing, silently missing real
          usage) or, worse, confidently delete the "unused" function anyway.
        </p>
        <p>
          PragyaLint specifically recognizes dispatch tables and
          <code>getattr()</code> calls as real usage, and when it detects
          patterns it <em>can't</em> resolve statically (a computed
          <code>getattr</code> name, <code>exec</code>, <code>globals()</code>),
          it downgrades remaining findings project-wide to LOW confidence and
          refuses to delete anything without <code>--force</code>. See
          <a href="dynamic-dispatch.html">Dynamic dispatch</a> for the full
          mechanism.
        </p>

        <h2 id="tests">Understands your test suite</h2>
        <p>
          Pytest discovers <code>test_*.py</code> and <code>conftest.py</code>
          files by walking the filesystem, not through any import statement in
          your source. A tool that only looks at the import graph will always
          see these as "unreachable" and propose deleting your entire test
          suite. PragyaLint recognizes pytest's discovery convention and treats
          these files as entry points automatically.
        </p>

        <h2 id="stdlib">Zero dependencies</h2>
        <p>
          PragyaLint is built entirely on the Python standard-library
          <code>ast</code> module. There's no third-party parser to pin, update,
          or audit — install it and it works with whatever Python version is
          running it.
        </p>

        <h2 id="tradeoffs">What PragyaLint doesn't do</h2>
        <p>To be fair about the trade-offs:</p>
        <ul>
          <li>
            It doesn't do type inference or cross-package call-graph analysis
            the way a full type checker would — it works at the level of names
            and imports, not resolved types.
          </li>
          <li>
            A computed dynamic-dispatch string (e.g.
            <code>getattr(mod, cmd.lower())</code>) is still undecidable by any
            static tool, PragyaLint included — the LOW-confidence downgrade and
            <code>--force</code> gate exist because of this, not instead of it.
          </li>
          <li>
            It analyzes one language (Python) — if your project mixes languages,
            you'll still want per-language tools alongside it.
          </li>
        </ul>
''')

# --------------------------------------------------------- how-it-works.html
write(f"{D}/how-it-works.html", "How it works", "How PragyaLint builds a module graph, computes reachability, and assigns confidence levels to dead-code findings.", '''
        <h1>How it works</h1>
        <p class="lead">
          PragyaLint runs in three stages: build a graph, compute reachability,
          then run each rule against the result.
        </p>

        <h2 id="discovery">1. Discovery</h2>
        <p>
          PragyaLint walks your project directory (respecting
          <code>--ignore</code> patterns and skipping <code>__pycache__</code>,
          <code>node_modules</code>, <code>site-packages</code>, and virtualenv
          directories automatically) and parses every matching file with the
          standard-library <code>ast</code> module.
        </p>

        <h2 id="graph">2. Module graph</h2>
        <p>
          For each file, PragyaLint extracts:
        </p>
        <ul>
          <li><strong>Imports</strong> — every <code>import</code> and <code>from ... import</code> statement, resolved to a module name.</li>
          <li><strong>Exports</strong> — top-level functions, classes, and assignments (or the explicit <code>__all__</code> list, if present).</li>
          <li><strong>Entry status</strong> — whether the file qualifies as an entry point. See <a href="entry-files.html">Entry files</a>.</li>
        </ul>
        <p>
          These become a directed graph: modules are nodes, imports are edges.
        </p>

        <h2 id="reachability">3. Reachability</h2>
        <p>
          Starting from every entry-point module, PragyaLint walks the import
          graph outward. Any module never reached this way is flagged
          <span class="conf conf-high">high</span>-confidence dead (rule
          <code>unused_file</code>). Anything reached but containing exports
          nothing else imports gets checked by the remaining rules. See
          <a href="analysis.html">Analysis rules</a> for the full rule set.
        </p>

        <h2 id="dynamic-note">4. Dynamic-dispatch check</h2>
        <p>
          Before finalizing findings, PragyaLint scans the whole project for
          patterns that can hide real usage from the graph: dispatch tables,
          <code>getattr()</code>, <code>exec</code>/<code>eval</code>,
          <code>globals()</code>/<code>locals()</code>. Names used this way are
          excluded from findings entirely where resolvable, or the rest of the
          project's findings are downgraded to LOW confidence where not. Full
          detail on <a href="dynamic-dispatch.html">Dynamic dispatch</a>.
        </p>

        <h2 id="output">5. Report</h2>
        <p>
          Every remaining issue becomes a <code>Finding</code>: a rule name, a
          confidence level, a message, and a file/line location. These render
          to your terminal by default, or as JSON/SARIF with
          <code>--json</code>/<code>--sarif</code> — see
          <a href="reports.html">Reports</a>.
        </p>
''')

# ------------------------------------------------------------ entry-files.html
write(f"{D}/entry-files.html", "Entry files", "How PragyaLint determines entry points: conventional entries, the --entry flag, and pytest test-file discovery.", '''
        <h1>Entry files</h1>
        <p class="lead">
          An entry point is a file PragyaLint assumes gets run or imported from
          outside your codebase — the starting point for reachability analysis.
          Everything reachable from an entry point is "alive"; everything else
          is a candidate for deletion.
        </p>

        <h2 id="conventional">Conventional entries</h2>
        <p>
          With no <code>--entry</code> flag, PragyaLint treats these as entries
          automatically:
        </p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pattern</th><th>Why</th></tr></thead>
            <tbody>
              <tr><td><code>__main__.py</code></td><td>Runnable as a package (<code>python -m yourpkg</code>).</td></tr>
              <tr><td><code>main.py</code></td><td>Common script entry-point filename.</td></tr>
              <tr><td><code>app.py</code></td><td>Common web-app entry-point filename.</td></tr>
              <tr><td><code>cli.py</code></td><td>Common CLI entry-point filename.</td></tr>
              <tr><td><code>setup.py</code></td><td>Package build script, invoked by <code>pip</code>/<code>setuptools</code> directly.</td></tr>
              <tr><td>Root-level <code>__init__.py</code></td><td>Package's public surface.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Disable this with <code>--no-conventional-entries</code> if you want
          to specify entries explicitly and nothing else.
        </p>

        <h2 id="explicit">Explicit entries</h2>
        <p>Pass one or more entry points explicitly with <code>--entry</code>:</p>
<pre><code>pragyalint --entry src/server.py --entry src/worker.py
pragyalint --entry src.server   # module-name form also works</code></pre>
        <p>
          When <code>--entry</code> is given, it's used <em>in addition to</em>
          test-file discovery (below) — not instead of it.
        </p>

        <h2 id="tests">Test files are always entries</h2>
        <div class="callout">
          <strong>This applies regardless of <code>--entry</code>.</strong>
          Pytest (and unittest discovery) import <code>conftest.py</code> and
          <code>test_*.py</code>/<code>*_test.py</code> files themselves, by
          walking the filesystem — not through any <code>import</code>
          statement in your source. A pure import-graph reachability check
          would always see these as unreachable and try to delete your whole
          test suite. PragyaLint recognizes this convention and treats matching
          files as entries automatically.
        </div>
        <p>Matched by any of:</p>
        <ul>
          <li>Filename <code>conftest.py</code></li>
          <li>Filename starting with <code>test_</code> or ending in <code>_test.py</code></li>
          <li>Any file inside a <code>tests/</code>, <code>test/</code>, or <code>__tests__/</code> directory</li>
        </ul>
        <p>
          Top-level definitions inside entry files (including test files)
          aren't flagged by <code>unused_local</code>/<code>unused_export</code>
          by default either — pytest calls <code>test_foo</code> functions by
          name-convention, not by reference, so they'd otherwise show up as
          "defined but never used" too. Pass <code>--include-entry-exports</code>
          if you specifically want entry-file definitions checked anyway.
        </p>

        <h2 id="package-init">Non-root <code>__init__.py</code> files</h2>
        <p>
          Only the <em>root</em> <code>__init__.py</code> counts as a
          conventional entry. Package <code>__init__.py</code> files deeper in
          your tree are analyzed normally — if nothing imports that
          subpackage, it's still flagged as unreachable.
        </p>
''')

# ------------------------------------------------------------- analysis.html
write(f"{D}/analysis.html", "Analysis rules", "The five PragyaLint rules: unused_file, unused_import, unused_export, unused_local, and cycle — what each checks and its confidence level.", '''
        <h1>Analysis rules</h1>
        <p class="lead">
          PragyaLint runs five independent rules. Each finding is tagged with
          the rule that produced it, so you can filter with
          <code>--rules</code> or read <code>rule</code> in JSON output.
        </p>

        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Rule</th><th>Checks</th><th>Confidence</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><code>unused_file</code></td>
                <td>Module unreachable from any entry point.</td>
                <td><span class="conf conf-high">high</span></td>
              </tr>
              <tr>
                <td><code>unused_import</code></td>
                <td>An imported name (or a single name inside a multi-name import) never referenced in that file.</td>
                <td><span class="conf conf-high">high</span></td>
              </tr>
              <tr>
                <td><code>unused_export</code></td>
                <td>A top-level function/class/variable no other module ever imports.</td>
                <td><span class="conf conf-medium">medium</span> (or <span class="conf conf-low">low</span> if dynamic dispatch detected)</td>
              </tr>
              <tr>
                <td><code>unused_local</code></td>
                <td>A top-level definition referenced nowhere in the project at all — not even within its own file.</td>
                <td><span class="conf conf-medium">medium</span> (or <span class="conf conf-low">low</span> if dynamic dispatch detected)</td>
              </tr>
              <tr>
                <td><code>cycle</code></td>
                <td>A circular import between modules (only run with <code>--cycles</code>).</td>
                <td><span class="conf conf-low">low</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2 id="export-vs-local">unused_export vs. unused_local</h2>
        <p>
          These two look similar but check different things, and a definition
          can trigger one, both, or neither:
        </p>
        <ul>
          <li>
            <code>unused_export</code> asks: <em>does any other module import
            this?</em> A function only ever called from within its own file
            (a private helper, effectively) will trigger this even though it's
            perfectly alive.
          </li>
          <li>
            <code>unused_local</code> asks: <em>is this referenced anywhere at
            all, including its own file?</em> This is the stronger claim — a
            <code>unused_local</code> finding means the definition is
            genuinely never called.
          </li>
        </ul>

        <h2 id="exemptions">What's exempt from unused_export / unused_local</h2>
        <ul>
          <li>Names starting with <code>_</code> (treated as intentionally private).</li>
          <li>Names listed in an explicit <code>__all__</code>.</li>
          <li>Names used as values in a dict/list/tuple/set literal (dispatch tables) — see <a href="dynamic-dispatch.html">Dynamic dispatch</a>.</li>
          <li>Names passed to <code>getattr(obj, "literal_name")</code> anywhere in the project.</li>
          <li>Top-level definitions in entry files (including test files), unless <code>--include-entry-exports</code> is passed.</li>
          <li>A definition marked with a trailing or preceding <code># pragyalint: keep</code> comment.</li>
        </ul>

        <h2 id="restricting">Restricting which rules run</h2>
<pre><code># Only check for unused files and imports (fastest, highest-confidence pass)
pragyalint --rules unused_file unused_import

# Add cycle detection (off by default)
pragyalint --cycles</code></pre>
''')

# ----------------------------------------------------------- confidence.html
write(f"{D}/confidence.html", "Confidence levels", "How PragyaLint's HIGH/MEDIUM/LOW confidence levels work, and what --fail-on and --confidence actually gate.", '''
        <h1>Confidence levels</h1>
        <p class="lead">
          Every finding carries a confidence level. It's not a percentage or a
          machine-learning score — it reflects how certain the underlying
          static-analysis claim is.
        </p>

        <div class="table-wrap">
          <table>
            <thead><tr><th>Level</th><th>Means</th><th>Example</th></tr></thead>
            <tbody>
              <tr>
                <td><span class="conf conf-high">high</span></td>
                <td>Structurally certain — provable from the import graph alone.</td>
                <td>A module nothing imports; an imported name never referenced in that file.</td>
              </tr>
              <tr>
                <td><span class="conf conf-medium">medium</span></td>
                <td>Strongly implied, but static analysis can't rule out an external caller (a library's public API) or an unusual internal pattern.</td>
                <td>An exported function no module in this project imports.</td>
              </tr>
              <tr>
                <td><span class="conf conf-low">low</span></td>
                <td>Heuristic, or downgraded because the project uses a pattern (dynamic dispatch, import cycles) that undermines the analysis's certainty.</td>
                <td>A dead-looking constant assignment; any finding in a project that also uses <code>exec</code>/<code>eval</code>/<code>getattr</code>/<code>globals()</code> somewhere.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2 id="two-gates">Two different gates use confidence</h2>

        <h3><code>--fail-on</code> — for CI</h3>
        <p>
          Controls what makes the process exit non-zero. Findings are still
          reported below this threshold; they just don't fail the run.
        </p>
<pre><code>pragyalint --fail-on high     # only HIGH findings fail CI (default: never fails)
pragyalint --fail-on medium   # MEDIUM and HIGH fail CI</code></pre>

        <h3><code>--confidence</code> — for <code>--fix</code></h3>
        <p>
          Controls which findings the fixer is allowed to actually delete.
          Plain <code>--fix</code> only touches HIGH-confidence findings.
        </p>
<pre><code>pragyalint --fix                          # HIGH only
pragyalint --fix --confidence medium+     # MEDIUM and HIGH
pragyalint --fix --confidence all         # everything, including LOW</code></pre>
        <div class="callout warn">
          <strong>Even at <code>--confidence all</code></strong>, the fixer
          still won't delete definitions from a project where dynamic dispatch
          was detected unless you also pass <code>--force</code>. Confidence
          and the dynamic-dispatch safety gate are independent checks — see
          <a href="dynamic-dispatch.html">Dynamic dispatch</a>.
        </div>

        <h2 id="why-low-not-deleted">Why LOW findings still show up if they're never auto-fixed</h2>
        <p>
          A LOW-confidence finding is still useful to <em>read</em> — it's
          telling you "this looks dead, but I found something in your project
          that makes me unsure." Reviewing it yourself is exactly the workflow
          it's designed for; it's just not going to delete anything for you
          without an explicit override.
        </p>
''')

# ----------------------------------------------------------- dynamic-dispatch.html
write(f"{D}/dynamic-dispatch.html", "Dynamic dispatch", "How PragyaLint detects getattr, dispatch tables, and exec/eval, and stays safe around code that calls functions by name at runtime.", '''
        <h1>Dynamic dispatch</h1>
        <p class="lead">
          Static analysis sees your code as text and syntax — it has no idea
          what happens at runtime. Code that calls functions <em>by name</em>
          instead of by direct reference is invisible to a naive
          "is this name referenced anywhere" check. PragyaLint specifically
          detects the common shapes of this and adjusts its confidence
          accordingly, rather than confidently deleting something that's
          actually alive.
        </p>

        <h2 id="patterns">Patterns PragyaLint recognizes</h2>

        <h3>Dispatch tables</h3>
        <p>A dict, list, tuple, or set literal whose values are bare names:</p>
<pre><code>DISPATCH = {"echo": execute_line, "run": run_block}
HANDLERS = [handler_a, handler_b]</code></pre>
        <p>
          Names used this way are treated as used, project-wide — no
          downgrade needed, because this pattern is fully resolvable
          statically.
        </p>

        <h3>Literal <code>getattr()</code></h3>
<pre><code>fn = getattr(runtime, "execute_line")</code></pre>
        <p>
          Also fully resolvable — PragyaLint treats this exactly like
          <code>runtime.execute_line</code>, a normal attribute access.
        </p>

        <h3>Computed <code>getattr()</code>, <code>exec</code>, <code>eval</code>, <code>globals()</code>/<code>locals()</code></h3>
<pre><code>fn = getattr(runtime, user_input)   # name isn't a literal — can't resolve
exec(f"{cmd}()")
globals()[cmd_name]()</code></pre>
        <p>
          These are genuinely undecidable by static analysis — the actual name
          being looked up depends on runtime data. When PragyaLint detects any
          of these <strong>anywhere in the project</strong>, it downgrades
          every remaining <code>unused_export</code>/<code>unused_local</code>
          finding to <span class="conf conf-low">low</span> confidence,
          project-wide.
        </p>

        <div class="callout">
          <strong>Why project-wide, not just the file with the call?</strong>
          A reflective call in <code>app.py</code> can just as easily reach a
          function defined in <code>runtime.py</code>. Limiting the safety
          check to only the file containing the <code>getattr</code> call
          would miss exactly the cross-file case that matters most — an
          interpreter's dispatch logic living in one file, calling functions
          defined in another.
        </div>

        <h2 id="fixer-gate">The <code>--force</code> gate</h2>
        <p>
          Confidence downgrade alone isn't the only safety net. Once dynamic
          dispatch is detected anywhere in the project, <code>--fix</code>
          refuses to delete any definition — even at
          <code>--confidence all</code> — unless you also pass
          <code>--force</code>:
        </p>
<pre><code># Reports the finding, but does not delete anything:
pragyalint --fix exports --confidence all

# Explicitly overrides the safety check:
pragyalint --fix exports --confidence all --force</code></pre>

        <h2 id="pragma">Manual override: the keep pragma</h2>
        <p>
          For a specific definition you know is used dynamically in a way
          PragyaLint can't detect (a computed name, a decorator-based
          registry), mark it directly:
        </p>
<pre><code>def execute_line(line):  # pragyalint: keep
    ...</code></pre>
        <p>
          This exempts the definition from <code>unused_export</code> and
          <code>unused_local</code> entirely, regardless of confidence or
          dynamic-dispatch state elsewhere in the project.
        </p>

        <h2 id="limits">What this doesn't solve</h2>
        <p>
          PragyaLint can't prove a computed <code>getattr</code> name is safe
          to delete — that's genuinely undecidable in general. The
          LOW-confidence downgrade plus the <code>--force</code> requirement
          exist precisely because of this limit: they make deletion opt-in
          rather than automatic once the analysis can no longer be fully
          certain, rather than pretending certainty it doesn't have.
        </p>
''')

# ---------------------------------------------------------- cli-commands.html
write(f"{D}/cli-commands.html", "CLI commands", "The full pragyalint flag reference: analysis, report, and fix options, plus exit codes.", '''
        <h1>CLI commands</h1>
        <p class="lead">
          PragyaLint is a single flag-based CLI — there are no subcommands.
          Everything is either an analysis option, a report option, or a fix
          option on the <code>pragyalint</code> command. This page is the
          reference for all of them.
        </p>

        <h2 id="basics">Basics</h2>
<pre><code>pragyalint                # analyze the current directory
pragyalint --help         # full option list
pragyalint --version      # print version
python3 -m pragyalint     # run as a module (works even when not on PATH)
py -m pragyalint          # Windows (py launcher)</code></pre>

        <h2 id="analysis">Analysis options</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Flag</th><th>Default</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td><code>-r, --root-dir &lt;path&gt;</code></td><td>current directory</td><td>Root directory of the project.</td></tr>
              <tr><td><code>-e, --entry &lt;module...&gt;</code></td><td>auto-detect</td><td>Entry-point modules, globs, or file paths. Space-separated or repeated; see <a href="entry-files.html">Entry files</a>.</td></tr>
              <tr><td><code>-i, --ignore &lt;patterns...&gt;</code></td><td><code>[]</code></td><td>Glob patterns to ignore while scanning.</td></tr>
              <tr><td><code>-x, --extensions &lt;exts...&gt;</code></td><td><code>.py</code></td><td>File extensions to analyze.</td></tr>
              <tr><td><code>--include &lt;paths...&gt;</code></td><td><code>[]</code></td><td>Only analyze files under these paths.</td></tr>
              <tr><td><code>--rules &lt;rules...&gt;</code></td><td>all</td><td>Restrict analysis to listed rules: <code>unused_file</code>, <code>unused_export</code>, <code>unused_import</code>, <code>unused_local</code>, <code>cycle</code>.</td></tr>
              <tr><td><code>--no-report-unused-exports</code></td><td>enabled</td><td>Disable unused-export reporting.</td></tr>
              <tr><td><code>--no-conventional-entries</code></td><td>included</td><td>Exclude conventional entries (<code>main.py</code>, <code>app.py</code>, <code>cli.py</code>, <code>__main__.py</code>, <code>setup.py</code>).</td></tr>
              <tr><td><code>--include-entry-exports</code></td><td>disabled</td><td>Report unused exports declared in entry files.</td></tr>
              <tr><td><code>--ignore-tests</code></td><td>disabled</td><td>Ignore test files and directories.</td></tr>
              <tr><td><code>--cycles</code></td><td>disabled</td><td>Detect and report circular import cycles.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="report">Report options</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Flag</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td><code>--fail-on high|medium|low|none</code></td><td>Exit non-zero when findings meet this confidence threshold. Default: never fails on findings alone.</td></tr>
              <tr><td><code>--json</code></td><td>Print the structured JSON report. See <a href="reports.html">Reports</a>.</td></tr>
              <tr><td><code>--sarif</code></td><td>Print SARIF output for Code Scanning. See <a href="reports.html">Reports</a>.</td></tr>
              <tr><td><code>--no-color</code></td><td>Disable ANSI colors in terminal output.</td></tr>
              <tr><td><code>-v, --verbose</code></td><td>Print internal graph state: entry points and every module marked R (reachable) or D (dead).</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="fix">Fix options</h2>
        <p>
          Analysis is always read-only. Fixes are opt-in and confidence-gated —
          see <a href="fixes.html">Fixes &amp; --fix</a> for the safety model.
        </p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Flag</th><th>Default</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td><code>--fix [files imports exports]</code></td><td>all targets</td><td>Apply fixes for the given targets. With no targets, applies <code>files</code>, <code>imports</code>, and <code>exports</code>.</td></tr>
              <tr><td><code>--confidence high|medium+|low+|all</code></td><td><code>high</code></td><td>Minimum confidence to fix.</td></tr>
              <tr><td><code>--dry-run</code></td><td>off</td><td>Log planned fixes without changing any files.</td></tr>
              <tr><td><code>--force</code></td><td>off</td><td>Allow a fix normally considered unsafe (e.g. a name listed in <code>__all__</code>, or any definition when the project uses dynamic dispatch).</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="examples">Common combinations</h2>
<pre><code># Fast CI pass: dead files and unused imports only
pragyalint --rules unused_file unused_import --fail-on high

# Preview exactly what --fix would change
pragyalint --fix --dry-run

# Machine-readable report for other tools
pragyalint --json &gt; report.json
pragyalint --sarif &gt; pragyalint.sarif

# Verbose graph dump (debugging reachability)
pragyalint -v</code></pre>

        <h2 id="config">Config files feed the same options</h2>
        <p>
          Every value above can also come from <code>pragyalint.toml</code>,
          <code>pragyalint.json</code>, or the <code>[tool.pragyalint]</code>
          table in <code>pyproject.toml</code> (dashes become underscores).
          Command-line flags always win. See <a href="config.html">Configuration</a>.
        </p>

        <h2 id="exit-codes">Exit codes</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Code</th><th>Meaning</th></tr></thead>
            <tbody>
              <tr><td><code>0</code></td><td>Scan completed; no finding met the <code>--fail-on</code> threshold (default).</td></tr>
              <tr><td><code>1</code></td><td>At least one finding met or exceeded <code>--fail-on</code>.</td></tr>
              <tr><td><code>2</code></td><td>Usage or configuration error — bad flags, invalid config value, unreadable config file.</td></tr>
              <tr><td><code>130</code></td><td>Interrupted (<kbd>Ctrl-C</kbd>).</td></tr>
            </tbody>
          </table>
        </div>
''')

# -------------------------------------------------------------- reports.html
write(f"{D}/reports.html", "Reports", "Terminal, JSON, and SARIF output formats for PragyaLint reports.", '''
        <h1>Reports</h1>
        <p class="lead">
          PragyaLint's findings render three ways: human-readable terminal
          output by default, JSON with <code>--json</code>, and SARIF with
          <code>--sarif</code>. Pick one per run — JSON and SARIF are
          mutually exclusive output modes.
        </p>

        <h2 id="terminal">Terminal (default)</h2>
        <p>Findings are grouped by file, each with a location, a confidence marker, and a message:</p>
<pre><code>$ pragyalint

./src/orphan.py
  &#10008; [HIGH  ] module 'orphan' is not reachable from any entry point

./src/utils/helper.py
  &#9888; [MEDIUM] export 'legacy_fn' of module 'utils.helper' is never imported

./src/app.py
  &#10008; [HIGH  ] import 'os' is never used

3 findings in 12 files (11 reachable).
  2 high | 1 medium</code></pre>
        <p>Markers and colors by confidence:</p>
        <ul>
          <li><span class="conf conf-high">high</span> — red <code>&#10008;</code> (✖)</li>
          <li><span class="conf conf-medium">medium</span> — yellow <code>&#9888;</code> (⚠)</li>
          <li><span class="conf conf-low">low</span> — cyan <code>&#8505;</code> (ℹ)</li>
        </ul>
        <p>
          Pass <code>--no-color</code> to disable ANSI colors (useful for logs
          and diffs). When there's nothing to report, PragyaLint prints
          <code>No dead code found.</code>
        </p>

        <h2 id="json">JSON</h2>
        <p><code>--json</code> prints the full structured report. Top-level keys:</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Key</th><th>Contents</th></tr></thead>
            <tbody>
              <tr><td><code>root_dir</code></td><td>The analysis root directory.</td></tr>
              <tr><td><code>summary</code></td><td><code>total_files</code>, <code>reachable_files</code>, <code>findings</code>, <code>by_rule</code>, <code>by_confidence</code>.</td></tr>
              <tr><td><code>findings</code></td><td>Objects with <code>rule</code>, <code>confidence</code>, <code>message</code>, <code>file</code>, <code>line</code>, <code>column</code>, and <code>extra</code> (rule-specific metadata like the unused name).</td></tr>
              <tr><td><code>modules</code></td><td>Per-module records: <code>path</code>, <code>module_name</code>, <code>is_package</code>, <code>is_entry</code>, <code>exports</code>, <code>imports</code>, <code>reachable</code>.</td></tr>
              <tr><td><code>entry_points</code></td><td>Module names treated as entries.</td></tr>
              <tr><td><code>cycles</code></td><td>Detected import cycles (empty unless <code>--cycles</code>).</td></tr>
              <tr><td><code>deps</code></td><td>Reserved dependency map.</td></tr>
            </tbody>
          </table>
        </div>
<pre><code>pragyalint --json</code></pre>
        <p>Truncated example:</p>
<pre><code>{
  "root_dir": "/home/you/project",
  "summary": {
    "total_files": 12,
    "reachable_files": 11,
    "findings": 2,
    "by_rule": {"unused_file": 1, "unused_import": 1},
    "by_confidence": {"high": 2}
  },
  "findings": [
    {
      "rule": "unused_file",
      "confidence": "high",
      "message": "module 'orphan' is not reachable from any entry point",
      "file": "/home/you/project/src/orphan.py",
      "line": null,
      "column": null,
      "extra": {"module": "orphan"}
    }
  ],
  "entry_points": ["main"],
  "cycles": []
}</code></pre>
        <p>Feed it to <code>jq</code> for quick triage:</p>
<pre><code>pragyalint --json | jq -r '.findings[] | [.rule, .confidence, (.file | split("/") | last)] | @tsv'</code></pre>

        <h2 id="sarif">SARIF</h2>
        <p><code>--sarif</code> emits a SARIF 2.1.0 document for Code Scanning tools:</p>
<pre><code>pragyalint --sarif &gt; pragyalint.sarif</code></pre>
        <ul>
          <li>Confidence maps to SARIF levels: <span class="conf conf-high">high</span> &rarr; <code>error</code>, <span class="conf conf-medium">medium</span> &rarr; <code>warning</code>, <span class="conf conf-low">low</span> &rarr; <code>note</code>.</li>
          <li>Each result carries the rule name, message, and a physical location (URI + start line/column) when the finding has one.</li>
          <li>Rules are declared under <code>runs[0].tool.driver</code>.</li>
        </ul>
        <p>
          Combine with the GitHub Code Scanning upload action to surface
          findings in pull requests — see <a href="automation.html">CI / automation</a>.
        </p>

        <h2 id="note">A note on <code>--fix</code> alongside reports</h2>
        <p>
          Fixes run as their own pass. With <code>--dry-run</code> the plan is
          printed first, then the report follows; nothing is written to disk.
          See <a href="fixes.html">Fixes &amp; --fix</a>.
        </p>
''')

# ---------------------------------------------------------------- cache.html
write(f"{D}/cache.html", "Cache", "What PragyaLint caches (and what it doesn't), why every run re-parses, and how to keep scans fast.", '''
        <h1>Cache</h1>
        <p class="lead">
          Short answer: PragyaLint keeps no on-disk analysis cache in the
          current release. Every run re-discovers your files and re-parses
          them. This page explains why, what actually controls a scan's cost,
          and how to keep re-runs fast.
        </p>

        <h2 id="no-cache">Is there a cache?</h2>
        <p>
          No. PragyaLint does not write any persistent state (no
          <code>pragyalint.cache</code>, no build directory, nothing hidden in
          <code>__pycache__</code>). Each invocation:
        </p>
        <ol>
          <li><strong>Walks</strong> the project tree looking for matching files.</li>
          <li><strong>Parses</strong> every matching file with the standard-library <code>ast</code> module.</li>
          <li><strong>Builds</strong> the module graph and runs the requested rules, all in memory.</li>
        </ol>
        <p>That's deliberate:</p>
        <ul>
          <li>
            <strong>Correctness</strong> — a stale cache is a silent lie. After
            any edit, the next scan must reflect current source.
          </li>
          <li>
            <strong>Zero dependencies</strong> — no extra state to corrupt,
            version, or debug, consistent with PragyaLint's
            "standard library only" guarantee.
          </li>
        </ul>

        <h2 id="cost">What actually affects run time</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Factor</th><th>Effect</th></tr></thead>
            <tbody>
              <tr><td>Number and size of files</td><td>Parsing dominates the scan; more code means a slower pass.</td></tr>
              <tr><td><code>--include</code></td><td>Restricts analysis to files under the listed paths — the single biggest lever.</td></tr>
              <tr><td><code>--ignore</code></td><td>Skips generated/templated/vendored directories entirely.</td></tr>
              <tr><td><code>--rules</code></td><td>Fewer rules means fewer traversal passes over the graph.</td></tr>
              <tr><td><code>--extensions</code></td><td>Limits which files are parsed at all.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="keep-fast">How to keep re-scans fast today</h2>
<pre><code># Narrow the scan to your source tree
pragyalint --include src

# Skip generated and vendored code that'll never be dead
pragyalint --ignore "**/generated" --ignore "vendor/"

# CI: only the two highest-confidence, graph-only rules
pragyalint --rules unused_file unused_import --fail-on high</code></pre>
        <p>
          Re-running immediately after a scan is also cheap because the OS page
          cache still holds the source files — nothing about the analysis
          itself is cached, but the operating system caches the reads.
        </p>

        <h2 id="bust">Busting the cache</h2>
        <p>
          There's nothing persistent to bust. If output ever looks stale, it's
          not a cache — re-run the command. A quick way to be sure you're
          analyzing what you think you are:
        </p>
<pre><code>pragyalint -v   # prints every module and whether it's reachable (R) or dead (D)</code></pre>

        <h2 id="roadmap">Roadmap</h2>
        <p>
          A persistent incremental cache is a plausible future feature (skip
          re-parsing files that haven't changed). When one ships, this page
          will document how it's enabled, when it's invalidated, and how to
          clear it.
        </p>
''')

# --------------------------------------------------------- integrations.html
write(f"{D}/integrations.html", "Integrations overview", "PragyaLint integration overview: editors, CI, and the Python API at a glance.", '''
        <h1>Integrations</h1>
        <p class="lead">
          PragyaLint is a single self-contained Python package with zero
          runtime dependencies — integrating it is usually one install plus
          one command. This page is the map; the linked pages have the details.
        </p>

        <h2 id="requirements">The one prerequisite</h2>
        <p>Everything below assumes the <code>pragyalint</code> executable is on <code>PATH</code>:</p>
<pre><code>pip install pragyalint
pragyalint --version</code></pre>
        <p>
          Python 3.11 or newer. If tools you shell out from (editors, CI
          runners) can't find it, set the executable's absolute path in their
          config — see <a href="errors.html">Errors &amp; troubleshooting</a>.
        </p>

        <h2 id="editor">Editor</h2>
        <div class="callout">
          <strong>VS Code</strong> — the official
          <a href="vscode.html">PragyaLint extension</a> publishes dead-code
          findings to the Problems panel, colored by confidence, and runs
          fixes as editor commands. Install it from the Marketplace or with
          <code>code --install-extension IndianCoder3.sks-pragyalint</code>.
        </div>

        <h2 id="ci">CI / automation</h2>
        <div class="callout">
          <strong>GitHub Actions, GitLab CI, pre-commit</strong> — see
          <a href="automation.html">CI / automation</a> for ready-to-copy
          workflows using <code>--fail-on</code> to gate merges and
          <code>--sarif</code> to feed Code Scanning.
        </div>

        <h2 id="api">Library use</h2>
        <div class="callout">
          <strong>Python API</strong> — <code>analyze()</code>,
          <code>apply_fixes()</code>, and the report model let you embed
          PragyaLint in your own tooling. See <a href="api.html">Python API</a>,
          and <a href="plugins.html">Plugins</a> for custom finder passes.
        </div>

        <h2 id="flow">A typical workflow</h2>
<pre><code># Local: review what's dead
pragyalint

# Local: preview an automated prune
pragyalint --fix --dry-run

# CI on every push: block merges that add high-confidence dead code
pragyalint --fail-on high</code></pre>
''')

# ------------------------------------------------------------- automation.html
write(f"{D}/automation.html", "CI / automation", "Run PragyaLint in CI: GitHub Actions, GitLab CI, pre-commit, and Code Scanning.", '''
        <h1>CI / automation</h1>
        <p class="lead">
          The two things PragyaLint gives CI are a <em>gate</em> — exit code 1
          when findings meet <code>--fail-on</code> — and a <em>feed</em> for
          other tools: JSON or SARIF. Wire either (or both) into your pipeline.
        </p>

        <h2 id="github-actions">GitHub Actions</h2>
        <p>A minimal job that gates every PR on high-confidence dead code:</p>
<pre><code>name: quality
on: [pull_request]
jobs:
  dead-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pragyalint
      - run: pragyalint --fail-on high</code></pre>

        <h3>Code Scanning with SARIF</h3>
        <p>Emit SARIF and upload it so findings appear as Code Scanning alerts on PRs:</p>
<pre><code>      - run: pragyalint --sarif &gt; pragyalint.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: pragyalint.sarif</code></pre>

        <h3>Self-analysis gate</h3>
        <p>PragyaLint's own CI runs this — it proves the codebase being shipped is clean:</p>
<pre><code>pragyalint --fail-on high --include pragyalint</code></pre>

        <h2 id="gitlab">GitLab CI</h2>
<pre><code>dead-code:
  image: python:3.12
  before_script:
    - pip install pragyalint
  script:
    - pragyalint --fail-on medium</code></pre>
        <p>
          With <code>--fail-on medium</code>, any MEDIUM or HIGH finding makes
          the job fail. Use <code>--json</code> and <code>artifacts:reports</code>
          if you want structured output in the pipeline.
        </p>

        <h2 id="precommit">pre-commit</h2>
        <p>
          PragyaLint currently ships no <code>.pre-commit-hooks.yaml</code>, so
          use a <code>repo: local</code> hook that calls the installed binary:
        </p>
<pre><code>repos:
  - repo: local
    hooks:
      - id: pragyalint
        name: pragyalint dead-code check
        entry: pragyalint --fail-on high
        language: system
        pass_filenames: false</code></pre>
        <p>
          <code>pass_filenames: false</code> matters — dead-code analysis is
          whole-project, not per-file.
        </p>

        <h2 id="tips">Tips</h2>
        <ul>
          <li>
            <strong>Install, don't assume.</strong> Pin a version in CI:
            <code>pip install "pragyalint==0.1.*"</code>.
          </li>
          <li>
            <strong>Narrow the scan.</strong> Monorepos: add
            <code>--include</code>/<code>--ignore</code> to keep the job fast
            and relevant.
          </li>
          <li>
            <strong>Start permissive.</strong> First run with
            <code>--fail-on high</code> only; graduate to MEDIUM once HIGH is
            clean.
          </li>
          <li>
            <strong>Exit codes</strong> — 0 is clean, 1 means findings at/above
            the threshold. CI treats the non-zero as a failure.
          </li>
        </ul>
''')

# --------------------------------------------------------------- plugins.html
write(f"{D}/plugins.html", "Plugins", "Extending PragyaLint with custom finder passes through the Python API", '''
        <h1>Plugins</h1>
        <p class="lead">
          PragyaLint's extension point is the Python API: an analysis run is a
          set of <em>finder</em> passes, and the set is pluggable. There is no
          CLI plugin-autoloading yet — custom passes are registered by calling
          <code>analyze()</code> yourself.
        </p>

        <h2 id="model">How rules are wired</h2>
        <p>
          <code>analyze()</code> receives a <code>hooks</code> mapping from
          rule name to a finder class. <code>default_hooks()</code> returns the
          five built-in finders:
        </p>
<pre><code>from pragyalint.analyzer import default_hooks

print(default_hooks())  # {rule: FinderClass, ...}</code></pre>

        <h2 id="custom">Writing a custom finder</h2>
        <p>
          A finder subclasses <code>Finder</code>, reads the module records and
          AST trees available on itself, and calls <code>emit()</code>:
        </p>
<pre><code>import ast
from pragyalint.analyzer import analyze, default_hooks
from pragyalint.finders import Finder
from pragyalint.models import Confidence, Finding

class MissingDocstringFinder(Finder):
    """Report modules whose first statement isn't a docstring."""

    rule = "missing_docstring"

    def run(self, records):
        for record in records:
            tree = self.trees.get(record.path)
            if tree is None:
                continue
            if isinstance(tree.body[0], ast.Expr) and isinstance(
                tree.body[0].value, ast.Constant
            ):
                continue
            self.emit(
                Finding(
                    rule=self.rule,
                    confidence=Confidence.LOW,
                    message="module lacks a docstring",
                    file=record.path,
                    line=1,
                )
            )

report = analyze(
    "src",
    hooks={**default_hooks(), "missing_docstring": MissingDocstringFinder},
)

for finding in report.findings:
    print(finding.rule, finding.confidence, finding.file)</code></pre>
        <p>What a finder gets to work with:</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Attribute</th><th>Contents</th></tr></thead>
            <tbody>
              <tr><td><code>self.report</code></td><td>The <code>AnalysisReport</code>, already populated with module records and reachability.</td></tr>
              <tr><td><code>self.graph</code></td><td>The module graph — <code>used_members_for()</code>, <code>resolve_to_record()</code>, <code>tree_for()</code>.</td></tr>
              <tr><td><code>self.trees</code></td><td><code>path → ast.Module</code> for every analyzed file.</td></tr>
              <tr><td><code>self.options</code></td><td>Passed-in options, e.g. <code>include_entry_exports</code>.</td></tr>
              <tr><td><code>self.emit(finding)</code></td><td>Appends the finding to the report and updates its summary counters.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="reporters">Custom reporters</h2>
        <p>
          The reporters are plain functions over an <code>AnalysisReport</code>:
          <code>format_terminal(report, color=True)</code>,
          <code>format_json(report, indent=2)</code>, and
          <code>format_sarif(report)</code>. Pass a report to your own
          formatter the same way.
        </p>

        <h2 id="limits">Current limits</h2>
        <ul>
          <li>No external plugin discovery (no entry-point scanning, no config-triggered loading) — you drive <code>analyze()</code>.</li>
          <li>Finders see <em>records</em> and <em>trees</em>, not resolved types; the same static-analysis boundaries that constrain the built-ins apply.</li>
          <li>The analyzer API is alpha-level and may change between releases.</li>
        </ul>
        <p>
          If a custom rule proves generally useful, consider contributing it as
          a built-in — see <a href="contributing.html">Contributing</a>.
        </p>
''')

# ----------------------------------------------------------------- vscode.html
write(f"{D}/vscode.html", "VS Code extension", "PragyaLint for Visual Studio Code: commands, settings, and inline dead-code diagnostics.", '''
        <h1>VS Code extension</h1>
        <p class="lead">
          <strong>PragyaLint for Visual Studio Code</strong> brings dead-code
          diagnostics into the editor. It runs <code>pragyalint --json</code>
          on your workspace and publishes findings to the Problems panel,
          colored by confidence, then lets you preview and apply fixes without
          leaving the editor.
        </p>

        <h2 id="install">Install</h2>
<pre><code>code --install-extension IndianCoder3.sks-pragyalint</code></pre>
        <p>Or open the Extensions panel (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>X</kbd>) and search for <strong>PragyaLint</strong>.</p>
        <p>
          <a href="https://marketplace.visualstudio.com/items?itemName=IndianCoder3.sks-pragyalint"
             target="_blank" rel="noopener">marketplace.visualstudio.com/…IndianCoder3.sks-pragyalint</a>
        </p>

        <h2 id="requirements">Requirements</h2>
        <p>
          The extension shells out to the <code>pragyalint</code> CLI, so it
          must be installed and reachable — <a href="install.html">install the
          CLI</a> with <code>pip install pragyalint</code> or pipx first. If the
          process that launches VS Code can't see it on its <code>PATH</code>,
          set <code>pragyalint.binaryPath</code> to the absolute path (see
          <a href="#settings">settings</a> and
          <a href="errors.html">ENOENT troubleshooting</a>).
        </p>

        <h2 id="commands">Commands</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Command</th><th>What it does</th></tr></thead>
            <tbody>
              <tr><td><code>PragyaLint: Scan workspace</code></td><td>Runs <code>pragyalint --json</code> and reports dead code into the Problems panel.</td></tr>
              <tr><td><code>PragyaLint: Preview fixes (dry-run)</code></td><td>Runs <code>--fix --dry-run</code> and opens the plan in a read-only document.</td></tr>
              <tr><td><code>PragyaLint: Apply safe fixes</code></td><td>Applies high-confidence fixes.</td></tr>
              <tr><td><code>PragyaLint: Scan and remove dead code (all confidence)</code></td><td>Full prune: <code>--fix --confidence low+ --force</code>.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Problems are colored by confidence — error (high), warning (medium),
          info (low) — matching the CLI report.
        </p>

        <h2 id="settings">Settings</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Setting</th><th>Default</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td><code>pragyalint.binaryPath</code></td><td><code>pragyalint</code></td><td>Executable to run. Set to an absolute path when the CLI isn't on the editor's <code>PATH</code>.</td></tr>
              <tr><td><code>pragyalint.confidence</code></td><td><code>high</code></td><td>Minimum confidence for fixes (<code>high</code>, <code>medium+</code>, <code>low+</code>, <code>all</code>).</td></tr>
              <tr><td><code>pragyalint.showLowConfidence</code></td><td><code>true</code></td><td>Show or hide low-confidence findings in the Problems panel.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="troubleshooting">Troubleshooting</h2>
        <ul>
          <li>
            <strong>ENOENT / "cannot find pragyalint"</strong> — the CLI isn't on
            the environment's <code>PATH</code>. Find it with
            <code>which pragyalint</code> (Windows: <code>where pragyalint</code>) and set <code>pragyalint.binaryPath</code>.
          </li>
          <li>
            <strong>Wrong interpreter</strong> — install the CLI into the same
            virtualenv VS Code's Python interpreter is using.
          </li>
          <li><strong>Stale results</strong> — re-run <em>Scan workspace</em>; nothing is cached between runs.</li>
        </ul>
        <p>Full diagnosis guidance: <a href="errors.html">Errors &amp; troubleshooting</a>.</p>
''')

# ------------------------------------------------------------------- api.html
write(f"{D}/api.html", "Python API", "Use PragyaLint as a library: analyze(), apply_fixes(), and the report model.", '''
        <h1>Python API</h1>
        <p class="lead">
          PragyaLint is built as a library with a thin CLI on top. You can call
          the same pipeline directly — run an analysis, inspect the report, and
          apply fixes — without shelling out.
        </p>

        <h2 id="analyze"><code>analyze()</code></h2>
<pre><code>from pragyalint.analyzer import analyze

report = analyze(root_dir=".", entry=["src/main.py"])</code></pre>
        <p>Full signature:</p>
<pre><code>analyze(
    root_dir: str,
    entry: list[str] | None = None,
    ignore: list[str] | None = None,
    extensions: list[str] | None = None,
    include: list[str] | None = None,
    rules: list[str] | None = None,
    report_unused_exports: bool = True,
    conventional_entries: bool = True,
    include_entry_exports: bool = False,
    ignore_tests: bool = False,
    detect_cycles: bool = False,
    fail_on: str | None = None,
    include_deps: bool = False,
    hooks: dict | None = None,
) -&gt; AnalysisReport</code></pre>
        <p>
          These mirror the CLI flags exactly (see <a href="cli-commands.html">CLI commands</a>).
          <code>entry</code>/<code>rules</code>/<code>hooks</code> may be
          <code>None</code> for "auto"; passing <code>hooks</code> replaces the
          rule set — see <a href="plugins.html">Plugins</a>.
        </p>

        <h2 id="report"><code>AnalysisReport</code></h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Field</th><th>Type</th><th>Contents</th></tr></thead>
            <tbody>
              <tr><td><code>root_dir</code></td><td><code>str</code></td><td>Analysis root.</td></tr>
              <tr><td><code>summary</code></td><td><code>Summary</code></td><td><code>total_files</code>, <code>reachable_files</code>, <code>findings</code>, <code>by_rule</code>, <code>by_confidence</code>.</td></tr>
              <tr><td><code>findings</code></td><td><code>list[Finding]</code></td><td>Every rule finding — see below.</td></tr>
              <tr><td><code>modules</code></td><td><code>list[ModuleRecord]</code></td><td>Per-module path, name, package/entry flags, exports, imports, reachable.</td></tr>
              <tr><td><code>entry_points</code></td><td><code>list[str]</code></td><td>Module names treated as entries.</td></tr>
              <tr><td><code>cycles</code></td><td><code>list[list[str]]</code></td><td>Import cycles (populated only with <code>detect_cycles=True</code>).</td></tr>
              <tr><td><code>deps</code></td><td><code>dict</code></td><td>Reserved dependency map.</td></tr>
            </tbody>
          </table>
        </div>
        <p><code>report.to_dict()</code> produces the same structure as <code>pragyalint --json</code>.</p>

        <h2 id="finding"><code>Finding</code></h2>
<pre><code>Finding(
    rule: str,                 # unused_file / unused_import / unused_export / unused_local / cycle
    confidence: str,           # "high" | "medium" | "low"
    message: str,
    file: str | None = None,
    line: int | None = None,
    column: int | None = None,
    extra: dict | None = None, # rule-specific metadata, e.g. the unused name
)</code></pre>
        <p><code>Confidence</code> provides the constants (<code>HIGH</code>, <code>MEDIUM</code>, <code>LOW</code>) and parsers (<code>parse()</code>, <code>parse_min()</code>).</p>

        <h2 id="apply-fixes"><code>apply_fixes()</code></h2>
<pre><code>from pragyalint.fixer import apply_fixes

result = apply_fixes(
    report,
    targets=["files", "imports", "exports"],
    min_confidence="high",     # "high" | "medium" | "low" (from --confidence)
    dry_run=True,              # preview only
    force=False,               # allow unsafe edits
)</code></pre>
        <p>
          Returns a <code>FixResult</code> with three lists:
          <code>applied</code>, <code>dry_run</code>, and <code>skipped</code>.
          The same confidence gating and safety checks that protect the CLI
          apply here (see <a href="fixes.html">Fixes &amp; --fix</a>).
        </p>

        <h2 id="reporters">Reporters</h2>
<pre><code>from pragyalint.reporters import format_terminal, format_json, format_sarif

print(format_terminal(report))
print(format_json(report))
print(format_sarif(report))</code></pre>

        <h2 id="example">Complete example</h2>
<pre><code>from pragyalint.analyzer import analyze
from pragyalint.fixer import apply_fixes

report = analyze(root_dir="src", detect_cycles=True)

for finding in report.findings:
    print(f"{finding.rule}\t{finding.confidence}\t{finding.line}\t{finding.message}")

# Preview fixing dead imports
result = apply_fixes(report, targets=["imports"], min_confidence="high", dry_run=True)
for planned in result.dry_run:
    print("would:", planned)</code></pre>

        <div class="callout">
          <strong>Stability:</strong> the API is alpha. <code>analyze()</code>,
          <code>apply_fixes()</code>, and the report model are the supported
          surface; details like the <code>hooks</code> wiring may evolve.
        </div>
''')

# ----------------------------------------------------------- contributing.html
write(f"{D}/contributing.html", "Contributing", "Dev setup, running tests, and opening a pull request for PragyaLint.", '''
        <h1>Contributing</h1>
        <p class="lead">
          PragyaLint is a small, dependency-free codebase — the analysis engine,
          the fixer, and the finders all live in one package with a tidy test
          suite. Here's how to get set up and what the maintainers expect.
        </p>

        <h2 id="setup">Dev setup</h2>
<pre><code>git clone https://github.com/Sanskriti-Studios/PragyaLint
cd PragyaLint
python -m venv .venv
source .venv/bin/activate               # Linux/macOS
.venv\\Scripts\\activate                # Windows (cmd)
.venv\\Scripts\\Activate.ps1            # Windows (PowerShell)
pip install -e ".[dev]"
pytest -q</code></pre>
        <p>Requires Python 3.11 or newer. The <code>dev</code> extra is just pytest — the package itself stays zero-dependency.</p>

        <h2 id="layout">Repository layout</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Path</th><th>What it's for</th></tr></thead>
            <tbody>
              <tr><td><code>pragyalint/</code></td><td>The package.</td></tr>
              <tr><td><code>pragyalint/analyzer.py</code></td><td>Pipeline: graph, reachability, then finder passes.</td></tr>
              <tr><td><code>pragyalint/graph.py</code></td><td>Discovery, AST parsing, imports/exports, cycle detection.</td></tr>
              <tr><td><code>pragyalint/finders/</code></td><td>One file per rule (<code>unused_*</code>, <code>cycles</code>).</td></tr>
              <tr><td><code>pragyalint/fixer.py</code></td><td>Opt-in, confidence-gated edits.</td></tr>
              <tr><td><code>pragyalint/reporters/</code></td><td>Terminal, JSON, and SARIF formatting.</td></tr>
              <tr><td><code>pragyalint/dynamic.py</code></td><td>Dynamic-dispatch heuristics and the keep pragma.</td></tr>
              <tr><td><code>pragyalint/config.py</code></td><td>Config discovery and defaults.</td></tr>
              <tr><td><code>tests/</code></td><td>pytest suite — one module per area (<code>test_graph</code>, <code>test_exports</code>, <code>test_fixer</code>, …).</td></tr>
              <tr><td><code>site/</code></td><td>This static documentation site.</td></tr>
              <tr><td><code>extensions/vscode-pragyalint/</code></td><td>VS Code extension source.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="tests">Running &amp; adding tests</h2>
<pre><code>pytest -q                         # whole suite
pytest tests/test_graph.py        # a single module
pytest -k "exports or dynamic"    # by keyword</code></pre>
        <p>
          New rules or behaviors need tests that build a tiny fixture tree in a
          temp directory and assert on the emitted findings — follow the
          existing test style. The repo's CI gate also runs a self-analysis:
        </p>
<pre><code>pragyalint --fail-on high --include pragyalint</code></pre>

        <h2 id="ci">CI workflows</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Workflow</th><th>Runs</th></tr></thead>
            <tbody>
              <tr><td><code>tests.yml</code></td><td>pytest on Python 3.11/3.12/3.13 plus the self-analysis gate, on push and PR.</td></tr>
              <tr><td><code>pages.yml</code></td><td>Deploys <code>site/</code> to GitHub Pages on push to main.</td></tr>
              <tr><td><code>publish.yml</code></td><td>Builds and publishes to PyPI and GitHub Releases; triggers on a <code>release:</code> commit.</td></tr>
              <tr><td><code>bins.yml</code></td><td>Builds standalone Windows/Linux/macOS binaries with PyInstaller and attaches them to releases.</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="conventions">Conventions</h2>
        <ul>
          <li>Standard library only — no new runtime dependencies.</li>
          <li>Python 3.11+ syntax and type annotations.</li>
          <li>Docstrings on public functions; rule logic lives in <code>finders/</code>.</li>
          <li>Docs: if you change behavior, update the matching page in <code>site/docs/</code> and its entry in <code>site/js/docs-nav.js</code>.</li>
          <li>Add a bullet to <code>CHANGELOG.md</code> for user-visible changes.</li>
        </ul>

        <h2 id="pr">Opening a PR</h2>
        <ul>
          <li>Open an issue first for anything non-trivial so the plan is agreed before the code.</li>
          <li>Describe the bug/feature, cite a reproduction, and attach <code>pragyalint -v</code> output when relevant.</li>
          <li>Use conventional commit prefixes — <code>fix:</code>, <code>feat:</code>, <code>chore:</code>, <code>docs:</code> — matching the existing history.</li>
          <li>Make sure tests and the self-analysis gate pass locally before pushing.</li>
        </ul>
        <p>
          Issues and PRs:
          <a href="https://github.com/Sanskriti-Studios/PragyaLint/issues" target="_blank" rel="noopener">github.com/Sanskriti-Studios/PragyaLint/issues</a>
        </p>
''')

# ---------------------------------------------------------------- source.html
write(f"{D}/source.html", "Source & releases", "Repository layout, releases, and versioning for PragyaLint.", '''
        <h1>Source &amp; releases</h1>
        <p class="lead">
          Where PragyaLint lives, how it's versioned, and what you'll find in a
          release — on PyPI, on GitHub, and as standalone binaries.
        </p>

        <h2 id="repo">Repositories</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Place</th><th>Link</th></tr></thead>
            <tbody>
              <tr><td>Source &amp; issues</td><td><a href="https://github.com/Sanskriti-Studios/PragyaLint" target="_blank" rel="noopener">github.com/Sanskriti-Studios/PragyaLint</a></td></tr>
              <tr><td>PyPI package</td><td><a href="https://pypi.org/project/pragyalint/" target="_blank" rel="noopener">pypi.org/project/pragyalint</a></td></tr>
              <tr><td>VS Code extension</td><td><a href="https://marketplace.visualstudio.com/items?itemName=IndianCoder3.sks-pragyalint" target="_blank" rel="noopener">marketplace.visualstudio.com/…IndianCoder3.sks-pragyalint</a></td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="layout">Repository layout</h2>
        <ul>
          <li><code>pragyalint/</code> — the analyzer package (CLI, graph, finders, fixer, reporters, config).</li>
          <li><code>tests/</code> — pytest suite.</li>
          <li><code>site/</code> — this static site, deployed to GitHub Pages.</li>
          <li><code>extensions/vscode-pragyalint/</code> — the VS Code extension.</li>
          <li><code>.github/workflows/</code> — CI: tests, Pages deployment, PyPI publishing, binary builds.</li>
          <li><code>CHANGELOG.md</code> — notable changes per release.</li>
        </ul>

        <h2 id="releases">Releases</h2>
        <p>
          PragyaLint follows <a href="https://semver.org/" target="_blank" rel="noopener">Semantic Versioning</a>.
          Each release ships to PyPI and as a GitHub Release with build
          artifacts:
        </p>
        <ul>
          <li><strong>sdist + wheel</strong> — install with <code>pip install pragyalint</code>.</li>
          <li><strong>Standalone binaries</strong> — PyInstaller-built executables for Windows (<code>.exe</code>), Linux, and macOS, attached to the GitHub Release.</li>
          <li><strong>Extension</strong> — the VS Code package (<code>.vsix</code>) is built and attached to the release too.</li>
        </ul>
        <p>
          The release pipeline in <code>.github/workflows/publish.yml</code>
          runs when a commit message contains <code>release:</code>
          (e.g. <code>release: v0.1.4</code>): it builds the PyPI wheel,
          PyInstaller binaries for Windows/Linux/macOS, and creates the GitHub
          Release with every asset attached. The
          <code>.github/workflows/vsix.yml</code> workflow builds and attaches
          the VS Code extension package to the same release, and tries to
          publish it to the VS Code Marketplace when a <code>VSCE_PAT</code>
          secret is configured.
        </p>

        <h2 id="versioning">Versions</h2>
<pre><code>pragyalint --version</code></pre>
        <p>
          The version lives in <code>pragyalint/__init__.py</code> and
          <code>pyproject.toml</code>. Current series at the time of writing:
          0.1.x (alpha). See
          <a href="https://github.com/Sanskriti-Studios/PragyaLint/blob/main/CHANGELOG.md" target="_blank" rel="noopener">CHANGELOG.md</a>
          for what changed in each release.
        </p>

        <h2 id="license">License</h2>
        <p>
          PragyaLint is free software, released under the
          <a href="https://github.com/Sanskriti-Studios/PragyaLint/blob/main/LICENSE" target="_blank" rel="noopener">GPL-3.0-or-later</a>
          license.
        </p>
''')

print("all batches done")
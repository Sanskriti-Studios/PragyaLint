import * as vscode from "vscode";
import { execFile } from "child_process";
import * as path from "path";

interface Finding {
  module: string;
  rule: string;
  confidence: string;
  path: string;
  line: number;
  column: number;
  message: string;
}

interface Report {
  findings: Finding[];
  summary?: {
    total_files: number;
    reachable_files: number;
    findings: number;
    by_rule: Record<string, number>;
    by_confidence: Record<string, number>;
  };
}

function resolveBinary(configured: string): string[] {
  const parts = configured.trim().split(/\s+/);
  const bin = parts[0];
  const rest = parts.slice(1);

  if (bin !== "pragyalint") {
    // User supplied an explicit path/command — use it verbatim.
    return [bin, ...rest];
  }

  const home = process.env.HOME || process.env.USERPROFILE || "";
  const fs = require("fs") as typeof import("fs");
  const candidates = [
    "pragyalint",
    `${home}/.local/bin/pragyalint`,
    `${home}/.local/share/pipx/venvs/pragyalint/bin/pragyalint`,
    `${home}/.local/bin/pragyalint.exe`,
    `${home}/.local/share/pipx/venvs/pragyalint/Scripts/pragyalint.exe`,
  ];

  for (const c of candidates) {
    if (c === "pragyalint") {
      // Fall through to PATH/locator below only if reachable; otherwise keep trying.
      if (fs.existsSync(c)) return [c, ...rest];
      continue;
    }
    if (fs.existsSync(c)) return [c, ...rest];
  }

  return ["pragyalint", ...rest];
}

function runPragyaLint(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const cfg = vscode.workspace.getConfiguration("pragyalint");
    const bin = resolveBinary(cfg.get<string>("binaryPath") || "pragyalint");
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
    execFile(
      bin[0],
      [...bin.slice(1), ...args],
      { cwd, maxBuffer: 16 * 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err && !stdout) {
          const hint =
            (err as NodeJS.ErrnoException).code === "ENOENT"
              ? `\nInstall PragyaLint (pip install pragyalint or pipx install pragyalint), or set the "pragyalint.binaryPath" setting to the executable's full path.`
              : "";
          const msg = (stderr || err.message || "pragyalint exited with an error").trim();
          reject(new Error(msg + hint));
        } else {
          resolve(stdout);
        }
      }
    );
  });
}

function parseReport(raw: string): Report {
  try {
    return JSON.parse(raw) as Report;
  } catch {
    // Fallback: empty report on parse failure.
    return { findings: [] };
  }
}

function severityFor(confidence: string): vscode.DiagnosticSeverity {
  switch (confidence) {
    case "high":
      return vscode.DiagnosticSeverity.Error;
    case "medium":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

function renderProblems() {
  const diags = new Map<string, vscode.Diagnostic[]>();
  return vscode.commands.registerCommand("pragyalint.scan", async () => {
    diags.clear();
    const result = await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "PragyaLint: scanning…" },
      async () => {
        const out = await runPragyaLint(["--json"]);
        return parseReport(out);
      }
    );

    const cfg = vscode.workspace.getConfiguration("pragyalint");
    const showLow = cfg.get<boolean>("showLowConfidence", true);

    for (const f of result.findings || []) {
      if (f.confidence === "low" && !showLow) continue;
      const filePath =
        f.path ||
        (f.module ? f.module.replace(/\./g, path.sep) + ".py" : "unknown.py");
      const range = new vscode.Range(
        Math.max(0, (f.line || 1) - 1),
        Math.max(0, (f.column || 1) - 1),
        Math.max(0, (f.line || 1) - 1),
        Math.max(1, (f.column || 1) - 1)
      );
      const d = new vscode.Diagnostic(
        range,
        `[${f.confidence}] ${f.rule}: ${f.message}`,
        severityFor(f.confidence)
      );
      d.source = "pragyalint";
      d.code = f.rule;
      d.relatedInformation = [];
      const abs = path.isAbsolute(filePath)
        ? filePath
        : path.join(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || "", filePath);
      if (!diags.has(abs)) diags.set(abs, []);
      diags.get(abs)!.push(d);
    }

    for (const f of vscode.workspace.textDocuments) {
      vscode.languages.getDiagnostics(f.uri);
    }
    for (const [file, list] of diags) {
      const uri = vscode.Uri.file(file);
      vscode.languages.createDiagnosticCollection("pragyalint").set(uri, list);
    }

    const summary = result.summary;
    if (summary) {
      const findings = summary.findings ?? 0;
      const c = summary.by_confidence || {};
      vscode.window.showInformationMessage(
        `PragyaLint: ${findings} finding${findings === 1 ? "" : "s"} in ${summary.total_files ?? 0} files ` +
          `(${c.high ?? 0} high, ${c.medium ?? 0} medium, ${c.low ?? 0} low)`
      );
    }
  });
}

function fixCommand(dryRun: boolean, all: boolean): vscode.Disposable {
  return vscode.commands.registerCommand(
    dryRun ? "pragyalint.dryRun" : all ? "pragyalint.cleanAll" : "pragyalint.fix",
    async () => {
      const args = ["--fix"];
      if (dryRun) args.push("--dry-run");
      if (all) {
        args.push("--confidence", "low+", "--force");
      } else {
        const cfg = vscode.workspace.getConfiguration("pragyalint");
        args.push("--confidence", cfg.get<string>("confidence") || "high");
      }
      const out = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: dryRun ? "PragyaLint: previewing…" : "PragyaLint: fixing…" },
        async () => (await runPragyaLint(args)) || ""
      );
      const doc = await vscode.workspace.openTextDocument({ content: out });
      await vscode.window.showTextDocument(doc, { preview: true, viewColumn: vscode.ViewColumn.Beside });
    }
  );
}

export function activate(ctx: vscode.ExtensionContext) {
  ctx.subscriptions.push(renderProblems());
  ctx.subscriptions.push(fixCommand(false, false));
  ctx.subscriptions.push(fixCommand(true, false));
  ctx.subscriptions.push(fixCommand(false, true));
}

export function deactivate() {}
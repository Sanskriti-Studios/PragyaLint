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
    files: number;
    findings: number;
    high: number;
    medium: number;
    low: number;
  };
}

function runPragyaLint(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const cfg = vscode.workspace.getConfiguration("pragyalint");
    const bin = (cfg.get<string>("binaryPath") || "pragyalint").split(/\s+/);
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
    execFile(
      bin[0],
      [...bin.slice(1), ...args],
      { cwd, maxBuffer: 16 * 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err && !stdout) {
          reject(new Error(stderr || err.message));
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
      const filePath = f.path || f.module.replace(/\./g, path.sep) + ".py";
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
      vscode.window.showInformationMessage(
        `PragyaLint: ${summary.findings} finding${summary.findings === 1 ? "" : "s"} in ${summary.files} files ` +
          `(${summary.high} high, ${summary.medium} medium, ${summary.low} low)`
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
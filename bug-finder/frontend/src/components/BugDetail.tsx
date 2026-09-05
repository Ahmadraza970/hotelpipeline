import { useEffect, useState } from "react";
import type { Bug, FixResult } from "../lib/api";
import { fix } from "../lib/api";
import { CodeEditor } from "./CodeEditor";
import { PremiumGate } from "./PremiumGate";
import { usePremium } from "../lib/premium";

interface Props {
  projectId: string;
  bug: Bug | null;
  onClose: () => void;
  onApplied: (result: FixResult) => void;
  hasApplied: boolean;
  onExportAll: () => void;
}

export function BugDetail({ projectId, bug, onClose, onApplied, hasApplied, onExportAll }: Props) {
  const [result, setResult] = useState<FixResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { premium, setPremium } = usePremium();
  const [showGate, setShowGate] = useState(false);

  const handleUpgrade = (name: string) => {
    if (name === "cancel") {
      setShowGate(false);
      return;
    }
    setPremium(true);
    setShowGate(false);
    setTimeout(() => void generate(), 0);
  };

  useEffect(() => {
    setResult(null);
    setError(null);
  }, [bug]);

  if (!bug) return null;

  const generate = async () => {
    if (!premium) {
      setShowGate(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fix(projectId, bug.id);
      setResult(res);
      onApplied(res);
    } catch (e: any) {
      setError(e.message ?? "could not generate fix");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-end bg-black/50 sm:items-center"
      onClick={onClose}
    >
      <div
        className="relative h-[85vh] w-full max-w-4xl overflow-y-auto rounded-t-xl rounded-b-xl border border-panel bg-panel sm:rounded-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-start justify-between rounded-t-xl border-b border-panel bg-panel-2 p-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="font-mono">{bug.file}:{bug.line}</span>
              <SeverityPill severity={bug.severity} />
            </div>
            <h3 className="mt-1 text-lg font-semibold text-slate-100">{bug.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-panel-2 hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="p-4">
          <p className="text-sm text-slate-300">{bug.description}</p>

          <div className="mt-4 rounded-lg border border-panel-2 bg-surface p-3">
            <div className="mb-2 text-xs font-semibold text-slate-400">Fix preview</div>
            {result ? (
              <DiffView diff={result.diff} explanation={result.explanation} />
            ) : (
              <div className="flex items-center justify-center py-8 text-slate-400">
                {loading ? "Generating fix…" : "Click below to generate a previewed fix."}
              </div>
            )}
            {error && <p className="mt-2 text-sm text-rose-300">{error}</p>}

            <button
              onClick={generate}
              disabled={loading || !!result}
              className="mt-3 rounded bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Generating…" : result ? "Regenerate" : premium ? "Generate fix" : "Generate fix — Pro"}
            </button>
            {!premium && (
              <span className="mt-2 block text-xs text-amber-300">
                AI fix generation requires a Pro or Team plan.{" "}
                <a href="/pricing" className="underline">
                  Compare plans
                </a>
              </span>
            )}
          </div>

          {result && (
            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={() => downloadBlob(result.diff, `${bug.file}.patch`)}
                className="rounded bg-panel-2 px-3 py-1.5 text-sm text-slate-200 hover:bg-panel"
              >
                Download this fix (.patch)
              </button>
              <span className={result.lint_ok ? "text-xs text-emerald-300" : "text-xs text-rose-300"}>
                Lint gate: {result.lint_ok ? "passed" : "warnings present"}
              </span>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 flex justify-between items-center rounded-b-xl border-t border-panel bg-panel-2 p-3">
          <button
            onClick={onExportAll}
            className="rounded bg-amber-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-amber-500"
            disabled={!hasApplied}
          >
            Export all applied fixes
          </button>
          <div className="text-xs text-slate-400">
            Fixes are previewed only — nothing changes until you download or export.
          </div>
        </div>
        {showGate && <PremiumGate onRequest={handleUpgrade} />}
      </div>
    </div>
  );
}

function SeverityPill({ severity }: { severity: string }) {
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.25 text-[10px] font-semibold uppercase ${
        {
          Critical: "bg-rose-500/20 text-rose-300",
          High: "bg-amber-500/20 text-amber-300",
          Medium: "bg-orange-500/20 text-orange-300",
          Low: "bg-blue-400/20 text-blue-300",
          Info: "bg-teal-400/20 text-teal-300",
        }[severity] ?? "bg-slate-400/20 text-slate-300"
      }`}
    >
      {severity}
    </span>
  );
}

function DiffView({ diff, explanation }: { diff: string; explanation: string }) {
  const isDiff = diff.includes("--- ") && diff.includes("+++ ");
  const before = isDiff ? extractRemoved(diff) : diff;
  const after = isDiff ? extractAdded(diff) : diff;
  return (
    <div className="space-y-3">
      <pre className="max-h-72 overflow-auto rounded bg-panel-2 p-3 text-xs text-slate-200 whitespace-pre-wrap">
        {diff}
      </pre>
      {before && after && (
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <CodeEditor value={before} language="plaintext" height="200px" />
          <CodeEditor value={after} language="plaintext" height="200px" />
        </div>
      )}
      <p className="text-xs text-slate-400">{explanation}</p>
    </div>
  );
}

// Loose extraction of removed/added context lines from a unified diff for the side panels.
function extractRemoved(diff: string): string {
  return diff.split("\n").filter((l) => l.startsWith("-") && !l.startsWith("--")).map((l) => l.slice(1)).join("\n");
}
function extractAdded(diff: string): string {
  return diff.split("\n").filter((l) => l.startsWith("+") && !l.startsWith("++")).map((l) => l.slice(1)).join("\n");
}

function downloadBlob(text: string, filename: string) {
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

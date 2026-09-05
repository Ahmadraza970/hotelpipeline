import { Link } from "react-router-dom";
import type { ScanResult } from "../lib/api";

interface Props {
  result: ScanResult;
  exploredFiles: number;
}

export function ScanSummary({ result, exploredFiles }: Props) {
  const counts = result.summary.by_severity;
  const order: Array<string> = ["Critical", "High", "Medium", "Low", "Info"];
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-panel bg-panel px-4 py-3">
      <div className="flex items-center gap-3 text-sm text-slate-300">
        <Link to="/" className="text-brand hover:underline">
          New scan
        </Link>
        <span className="text-slate-600">·</span>
        <span className="font-mono text-xs text-slate-400">
          Project: {result.project_id}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="rounded bg-panel-2 px-2 py-0.5 text-xs">
          {exploredFiles} file{exploredFiles !== 1 ? "s" : ""}
        </span>
        {order.map((s) => {
          const n = counts[s] ?? 0;
          if (!n) return null;
          return (
            <span
              key={s}
              className={`rounded px-2 py-0.5 text-xs font-medium ${pill(s)}`}
            >
              {s}: {n}
            </span>
          );
        })}
        <span className="text-xs text-slate-400">{result.elapsed_ms}ms</span>
      </div>
    </div>
  );
}

function pill(s: string) {
  return {
    Critical: "bg-rose-500/20 text-rose-300",
    High: "bg-amber-500/20 text-amber-300",
    Medium: "bg-orange-500/20 text-orange-300",
    Low: "bg-blue-400/20 text-blue-300",
    Info: "bg-teal-400/20 text-teal-300",
  }[s] ?? "bg-slate-400/20 text-slate-300";
}
